"""
Document loading (Task 1: PDF support).

The baseline only read *.txt files. This module reads both *.txt and *.pdf files
and returns LangChain Document objects with metadata {source, page} so that the
chatbot can cite where an answer came from.
"""

import re
from collections import Counter
import unicodedata
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

SUPPORTED = (".txt", ".pdf")

# Some handbook headings use a custom font whose glyphs for "ti" and "tt" are
# extracted as ";", "8", "’", "0" or "2" (e.g. "Descrip;on", "Educa8onal",
# "Founda’onal", "A2ributes"). These broken words would never match a query such
# as "program description", so they are repaired before indexing.
# Only "...ti" + "on"/"ve" is repaired, so normal apostrophes ("Fulbright’s") are kept.
_BROKEN_TI = re.compile(r"(?<=[a-z])[;8’](?=(?:on|ve))")
_BROKEN_TT = re.compile(r"\bA[02]ribute", re.IGNORECASE)


def clean_text(text: str) -> str:
    # NFKC turns ligature characters such as "ﬁ" into normal letters "fi".
    text = unicodedata.normalize("NFKC", text)
    text = _BROKEN_TI.sub("ti", text)
    text = _BROKEN_TT.sub("Attribute", text)
    # Table-of-contents dot leaders ("Mission ........ 2") add noise to embeddings.
    text = re.sub(r"\.{4,}\s*\d*", " ", text)
    # Collapse runs of spaces, keep line breaks (they separate table rows).
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


# pypdf sometimes inserts a space inside a word ("s tudents", "als o", "o r",
# "socio -economic"), because of how the PDF positions letters. There is no
# dictionary offline, so the document itself is used as one: two pieces are joined
# when the joined word appears in the document more often than the rarer piece.
_WORD = re.compile(r"[A-Za-z]+")
_TOKENS = re.compile(r"([A-Za-z]+)")


def repair_split_words(texts: list[str]) -> tuple[list[str], int]:
    counts = Counter(w.lower() for t in texts for w in _WORD.findall(t))
    fixed = 0
    repaired = []
    for text in texts:
        text = re.sub(r"(?<=[a-z]) -(?=[a-z])", "-", text)      # "socio -economic"
        text = re.sub(r"(?<=[a-z]) (?=[,.;:](\s|$))", "", text)  # "arts , media"
        # parts alternates: separator, word, separator, word, ...
        parts = _TOKENS.split(text)
        i = 1
        while i + 2 < len(parts):
            a, gap, b = parts[i], parts[i + 1], parts[i + 2]
            whole = (a + b).lower()
            if (gap == " " and b.islower()
                    and counts[whole] >= 2
                    and counts[whole] > min(counts[a.lower()], counts[b])):
                parts[i:i + 3] = [a + b]   # merge, then try to merge again with the next piece
                fixed += 1
                continue
            i += 2
        repaired.append("".join(parts))
    return repaired, fixed


def load_txt(path: Path) -> list[Document]:
    content = path.read_text(encoding="utf-8")
    # A first line "# Title" names the source in citations, e.g. "(AMS web page)".
    first = content.lstrip().splitlines()[0] if content.strip() else ""
    title = first[1:].strip() if first.startswith("#") else path.stem.replace("_", " ")
    return [Document(page_content=clean_text(content), metadata={"source": path.name, "page": 0, "title": title})]


def load_pdf(path: Path) -> list[Document]:
    """One Document per PDF page, so every chunk remembers its page number."""
    reader = PdfReader(str(path))
    raw = [page.extract_text() or "" for page in reader.pages]
    pages = [clean_text(text) for text in raw]
    pages, fixed = repair_split_words(pages)
    if fixed:
        print(f"  Repaired {fixed} split words in {path.name}")
    docs = []
    for number, (text, original) in enumerate(zip(pages, raw), start=1):
        # Skip empty pages (blank pages or pages that are only an image).
        # Text inside images would need OCR, which is out of scope (see FAQ 5).
        if len(text) < 20:
            continue
        # Skip table-of-contents pages. They list every heading side by side
        # ("Major Requirements (48 credits)  Minor Requirements (24 credits)"), rank high for
        # almost any question, and led the model to add 48 + 24 = 72 "credits to graduate".
        if is_table_of_contents(original):
            print(f"  Skipped table of contents: {path.name} page {number}")
            continue
        docs.append(Document(page_content=text, metadata={"source": path.name, "page": number}))
    return docs


_DOT_LEADER = re.compile(r"\.{4,}\s*\d+\s*$", re.MULTILINE)   # "Mission ........ 2"


def is_table_of_contents(raw_text: str) -> bool:
    return len(_DOT_LEADER.findall(raw_text)) >= 5


def list_files(directory: str) -> list[Path]:
    folder = Path(directory)
    return sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith(("~$", "."))
    )


def load_documents(directory: str, verbose: bool = True) -> list[Document]:
    documents = []
    for path in list_files(directory):
        loader = load_pdf if path.suffix.lower() == ".pdf" else load_txt
        docs = loader(path)
        if verbose:
            print(f"  Loaded {path.name}: {len(docs)} page(s)")
        documents.extend(docs)
    return documents
