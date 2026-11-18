"""
The RAG pipeline: index documents, retrieve chunks, build the prompt, generate.

Differences from the baseline run_txt.py (each one is discussed in the report):
  1. Reads PDF and TXT (loaders.py), keeps the page number of every chunk.
  2. Rebuilds the vector store automatically when documents or settings change
     (the baseline reused an old index forever, even after files were added).
  3. Uses cosine similarity, so scores are between 0 and 1 and easy to threshold.
  4. Filters out weak chunks one by one instead of averaging all scores.
  5. Answers only from the handbook and says so when the answer is missing,
     instead of falling back to the model's general knowledge.
  6. Accepts the recent conversation so follow-up questions work (scope.py rewrites
     follow-ups into stand-alone queries and keeps refusals out of the memory).
  7. Refuses questions outside the handbook (other majors such as Mathematics, or
     general questions) instead of answering them with unrelated AMS passages.
  8. Uses the task prefixes nomic-embed-text was trained with ("search_query: ",
     "search_document: "), which spreads relevant and irrelevant scores further apart.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Iterator

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config, language, scope
from .loaders import list_files, load_documents
from .scope import NOT_FOUND

# Bump when the way chunks are embedded changes, so old vector stores are rebuilt.
INDEX_VERSION = "4-nomic-prefix-section-headings"

PROMPT_TEMPLATE = """You are a helpful assistant that answers questions about {description}.
You only know this one handbook. It is about the Art and Media Studies (AMS) major, not about
other majors such as Mathematics, Computer Science, Economics or Psychology.

Rules:
- Use ONLY the context below. Each context block starts with its page number.
- If the question asks about another major or subject, or the context does not contain the
  answer, reply exactly: "{not_found}"
- Never apply AMS numbers (credits, GPA, courses) to another major or subject.
- Do not invent course codes, numbers or policies.
- The previous conversation is only there to understand words like "it" or "that course".
  Facts must still come from the context.
- Keep the answer short (2 to 5 sentences, or a short list) and mention the page you used, like (p. 7).
{language_rule}{history}
CONTEXT:
{context}
{follow_up}
QUESTION: {question}
{translation}
ANSWER:"""


SCOPE_PROMPT = """A chatbot answers questions about a university's Art and Media Studies major handbook:
courses, credits, requirements, prerequisites, the capstone, faculty, the department chair, advising,
policies, fees, study abroad, internships, learning outcomes, careers and student clubs.

Is the following question something a student could ask about that handbook?
Answer with one word, YES or NO.

Question: {question}
Answer:"""


# Headings whose meaning is lost when a chunk is cut below them:
#   course descriptions   "ARTS 309: Advanced Narrative Film Production"
#   requirement blocks    "Major Requirements (48 credits)", "Minor Requirements (24 credits)"
#   numbered sections     "4. Program Structure and Curriculum", "Major Outline: ..."
_REQUIREMENTS = r"(?:Major|Minor|General Curriculum) Requirements \([^\n)]*\)"
COURSE_HEADING = re.compile(
    r"^(?:ARTS \d{3}(?:/\d{3})?: [^\n]+"
    r"|" + _REQUIREMENTS +
    r"|\d{1,2}\. [A-Z][^\n.]{3,90}"
    r"|Major Outline: [^\n]+)",
    re.MULTILINE,
)
# A new chunk should start at each requirement block, so "Major Requirements (48 credits)"
# is not buried at the end of a chunk about military training and physical education.
_BREAK_BEFORE = re.compile(r"\n(?=" + _REQUIREMENTS + r")")


def separate_sections(documents):
    for doc in documents:
        doc.page_content = _BREAK_BEFORE.sub("\n\n", doc.page_content)
    return documents


def add_course_headings(chunks):
    """
    A chunk cut below its heading loses its meaning. On page 31 the chunk
    "Prerequisites: ARTS 101 ... AND ARTS 104 ..." never says it belongs to ARTS 309, so
    "prerequisites of ARTS 309" retrieved ARTS 308's prerequisites instead; on page 9 the
    minor's course list does not say it is the minor's. Each chunk that continues a
    course description or section gets that heading in front, e.g.
    "[ARTS 309: Advanced Narrative Film Production, continued]".
    """
    current, current_page = None, -1
    for chunk in chunks:
        text = chunk.page_content
        page = chunk.metadata.get("page", 0)
        first = COURSE_HEADING.search(text)
        starts_with_heading = first is not None and not text[:first.start()].strip(" \n0123456789")
        if current and not starts_with_heading and page <= current_page + 1:
            chunk.page_content = f"[{current}, continued]\n{text}"
        headings = COURSE_HEADING.findall(text)
        if headings:
            current, current_page = headings[-1].strip(), page
    return chunks


def _fingerprint() -> str:
    """Changes whenever a document or an indexing setting changes."""
    parts = [INDEX_VERSION, config.EMBED_MODEL, str(config.CHUNK_SIZE), str(config.CHUNK_OVERLAP)]
    for path in list_files(config.DATA_DIR):
        stat = path.stat()
        parts.append(f"{path.name}:{stat.st_size}:{int(stat.st_mtime)}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


class PrefixedEmbeddings(OllamaEmbeddings):
    """nomic-embed-text expects a task prefix on every text; without it, scores bunch
    together (an unrelated question still reaches ~0.5). Other models get no prefix."""

    def _prefix(self, kind: str) -> str:
        return f"{kind}: " if "nomic" in self.model else ""

    def embed_documents(self, texts):
        return super().embed_documents([self._prefix("search_document") + t for t in texts])

    def embed_query(self, text):
        return super().embed_query(self._prefix("search_query") + text)


class RAGPipeline:
    def __init__(self, llm_model: str | None = None, verbose: bool = True):
        self.verbose = verbose
        self.llm_model = llm_model or config.LLM_MODEL
        self.embeddings = PrefixedEmbeddings(model=config.EMBED_MODEL, base_url=config.OLLAMA_URL)
        self.db = self._load_or_build()
        self.llm = OllamaLLM(
            model=self.llm_model,
            base_url=config.OLLAMA_URL,
            temperature=config.TEMPERATURE,
        )

    def _log(self, message: str):
        if self.verbose:
            print(message, flush=True)

    # ---------- Indexing ----------

    def _open_store(self) -> Chroma:
        return Chroma(
            collection_name=config.COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=config.VECTOR_STORE,
            collection_metadata={"hnsw:space": "cosine"},
        )

    def _load_or_build(self) -> Chroma:
        store = Path(config.VECTOR_STORE)
        manifest = store / "manifest.json"
        current = _fingerprint()

        if manifest.exists() and json.loads(manifest.read_text()).get("fingerprint") == current:
            self._log(f"Loading existing vector store from {store}")
            return self._open_store()

        if store.exists():
            self._log("Documents or settings changed, rebuilding the vector store...")
            shutil.rmtree(store)

        files = list_files(config.DATA_DIR)
        if not files:
            raise SystemExit(f"No .txt or .pdf files found in '{config.DATA_DIR}'")

        self._log(f"Indexing documents from {config.DATA_DIR}")
        documents = load_documents(config.DATA_DIR, verbose=self.verbose)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = add_course_headings(splitter.split_documents(separate_sections(documents)))
        self._log(f"  {len(chunks)} chunks, embedding with {config.EMBED_MODEL}...")

        db = self._open_store()
        db.add_documents(chunks)
        store.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({
            "fingerprint": current,
            "files": [p.name for p in files],
            "chunks": len(chunks),
        }, indent=2))
        self._log("  Done.")
        return db

    # ---------- Retrieval ----------

    def prepare(self, question: str, history: list[dict] | None = None) -> dict:
        """
        Scope check + memory + retrieval. Returns
        {"sources": [...], "query": str, "refusal": str | None, "reason": str}
        A refusal is a ready-made answer; the LLM is not called for it.
        """
        # Any language: the question is translated into English for the scope guard and
        # the search, and answered in its own language (language.py).
        lang = language.detect(question, self.llm)
        question_en = language.to_english(self.llm, question, lang)
        if lang != language.ENGLISH:
            self._log(f"  {lang}: {question!r} -> {question_en!r}")
        base = {"lang": lang, "question_en": question_en}

        def decline(kind, query, subjects=None):
            text = language.message(kind, lang, subjects, question_en, self.llm)
            reason = "other_subject" if kind == "other_subject" else ("off_topic" if kind == "off_topic" else "greeting")
            return {**base, "sources": [], "query": query, "refusal": text, "reason": reason}

        plan = scope.resolve(question_en, language.normalize_history(history))
        if plan["action"] == "refuse":
            return decline(plan.get("kind", "greeting"), plan["query"], plan["subjects"])

        sources = self._search(plan["query"])
        best = max((s["score"] for s in sources), default=0.0)
        # Nothing in the handbook is close to the question at all (weather, recipes...).
        if best < config.SCOPE_THRESHOLD:
            return decline("off_topic", plan["query"])

        # Grey zone: some real questions ("Who are the faculty?") score as low as some
        # unrelated ones ("Tell me a joke"), so the LLM makes a quick yes/no decision.
        if best < config.SCOPE_CONFIRM and not self._is_handbook_question(plan["query"]):
            return decline("off_topic", plan["query"])

        kept = [s for s in sources if s["score"] >= config.SCORE_THRESHOLD]
        return {**base, "sources": kept, "query": plan["query"], "refusal": None, "context": plan.get("context"),
                "reason": "follow_up" if plan["follow_up"] else "answer"}

    def _is_handbook_question(self, question: str) -> bool:
        prompt = SCOPE_PROMPT.format(question=question)
        reply = self.llm.invoke(prompt).strip().upper()
        self._log(f"  scope check: {question!r} -> {reply[:10]}")
        return not reply.startswith("NO")

    def retrieve(self, question: str, history: list[dict] | None = None) -> list[dict]:
        return self.prepare(question, history)["sources"]

    def _search(self, query: str) -> list[dict]:
        results = self.db.similarity_search_with_score(query, k=config.TOP_K)
        sources = []
        for doc, distance in results:
            score = round(1 - float(distance), 4)  # cosine distance -> similarity
            sources.append({
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
                "score": score,
                "content": doc.page_content,
            })
        return sources

    # ---------- Prompt ----------

    def build_prompt(self, question: str, sources: list[dict], history: list[dict] | None,
                     context_question: str | None = None, lang: str = language.ENGLISH,
                     question_en: str | None = None) -> str:
        context = "\n\n---\n\n".join(f"[page {s['page']}]\n{s['content']}" for s in sources)

        history_text = ""
        turns = scope.history_for_prompt(language.normalize_history(history), config.HISTORY_TURNS)
        if turns:
            lines = [f"User: {t['question']}\nAssistant: {t['answer']}" for t in turns]
            history_text = "\nPREVIOUS CONVERSATION (for understanding follow-up questions):\n" + "\n\n".join(lines) + "\n"

        return PROMPT_TEMPLATE.format(
            description=config.DOC_DESCRIPTION,
            not_found=language.not_found(lang),
            language_rule=(f"- The question is in {lang}. Write the whole answer in {lang}. Keep course codes and "
                           f"page citations exactly as they are, like (p. 7).\n" if lang != language.ENGLISH else ""),
            translation=(f"QUESTION IN ENGLISH: {question_en}\n" if lang != language.ENGLISH and question_en else ""),
            history=history_text,
            context=context,
            question=question,
            follow_up=(f'\nThis is a follow-up to the earlier question: "{context_question}"\n'
                       if context_question else ""),
        )

    # ---------- Generation ----------

    def ask(self, question: str, history: list[dict] | None = None) -> dict:
        plan = self.prepare(question, history)
        answer = "".join(self.stream(question, plan, history)).strip()
        unsupported = scope.ungrounded_numbers(answer, plan["sources"], question) if plan["sources"] else []
        reason = plan["reason"]
        if not plan.get("refusal") and answer.startswith(language.not_found(plan.get("lang", language.ENGLISH))):
            reason = "not_found"
        return {"answer": answer, "sources": plan["sources"], "no_context": not plan["sources"],
                "reason": reason, "unsupported_numbers": unsupported, "lang": plan.get("lang"),
                "question_en": plan.get("question_en")}

    def stream(self, question: str, plan: dict, history: list[dict] | None = None) -> Iterator[str]:
        """Yields the answer token by token (used by the web interface)."""
        if plan.get("refusal"):
            yield plan["refusal"]
            return
        lang = plan.get("lang", language.ENGLISH)
        if not plan["sources"]:
            yield language.not_found(lang)
            return
        if lang == language.ENGLISH:
            yield from self.llm.stream(self.build_prompt(question, plan["sources"], history, plan.get("context")))
            return
        # Other languages: the small model answers far more accurately in English (the language of the
        # handbook and of the prompt), so it answers the English question first and the answer is then
        # translated. A "not found" answer gets the fixed text in the user's language.
        english = self.llm.invoke(self.build_prompt(plan.get("question_en") or question, plan["sources"],
                                                    history, plan.get("context"))).strip()
        self._log(f"  English answer: {english[:120]!r}")
        if english.startswith(NOT_FOUND):
            yield language.not_found(lang)
            return
        yield from language.translate_answer(self.llm, english, lang)
