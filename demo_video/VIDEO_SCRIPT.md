# Video demo scripts (Tasks 1–4)

Record with Win + Alt + R (Xbox Game Bar, saves to Videos\Captures). Aim for 2–3 minutes per video.
Each video follows the brief: **show the implementation, explain its purpose, show the output.**
Answers take 10–30 s; pause the recording while you wait if you like.

Before you start: open VS Code on the `ADL-project` folder and open a PowerShell terminal in it:
```
cd C:\Users\Admin\Downloads\ADL-project\source_code
..\.venv\Scripts\activate
```
(Ollama must be running; check with `ollama list`.)

---

## Video 1 — Task 1: PDF file support (~2 min)

**1. Purpose (say)**
"Task 1 extends the baseline, which only read .txt files, so it can read PDF documents: extract the text,
split it into chunks, embed the chunks and store them in the vector database."

**2. Implementation (show `source_code/rag/loaders.py`)**
- Scroll to `load_pdf`. Say: "I use pypdf and create one document per page, so every chunk keeps its page
  number and answers can cite pages, like (p. 9)."
- Scroll to `clean_text` and `repair_split_words`. Say: "pypdf extracts some words with stray spaces,
  like 's tudents', and some headings with broken letters, like 'Descrip;on'. These hurt retrieval, so I
  repair them using the document's own vocabulary. I also skip the table of contents page."
- Open `source_code/rag/pipeline.py`, scroll to `_load_or_build`. Say: "The text is split into
  800-character chunks with 150 characters of overlap, embedded with nomic-embed-text and stored in
  ChromaDB. A fingerprint of the files is saved, so when a PDF is added or changed the index rebuilds
  automatically."

**3. Output (run in the terminal)**
Any PDF works for Task 1; I use the project brief:
```
python cli.py --data-dir data/test_pdf --store vector_store/test_pdf -q "How much is the Docker task worth?"
```
Point at: "Loaded Final-project-ADL.pdf: 13 page(s)", the answer **20%**, and the sources with page numbers
(page 6 is the requirements table). Say: "The answer comes from the PDF, and the sources show which pages
were retrieved and their similarity scores."

Then the handbook PDF:
```
python cli.py -q "What are the prerequisites for ARTS 309?"
```
Say: "The same loader reads the AMS handbook, the document for the rest of the project."

---

## Video 2 — Task 2: Major handbook chatbot (~3 min)

**1. Purpose (say)**
"Task 2 is a RAG chatbot for one major handbook. I chose the B.A. Art and Media Studies handbook. It
answers program requirements, course offerings, learning outcomes and policies, and cites the pages."

**2. Implementation (show briefly)**
- `rag/pipeline.py`, scroll to `PROMPT_TEMPLATE`. Say: "The model may only use the retrieved context,
  must cite the source, and must say 'I could not find this in the handbook' instead of guessing."
- `rag/scope.py`, top docstring. Say: "Testing showed a hallucination: asked about the Maths major, the
  bot answered with AMS numbers, because the search always returns the closest chunks. This scope guard
  declines questions about other majors."

**3. Output (terminal, interactive chat with memory)**
```
python cli.py
```
Type, one at a time (empty line to quit):
1. `How many credits does the AMS major require?` → 48 credits (p. 9)
2. `What GPA do I need for the Capstone?` → 3.6
3. `What kind of project can I do for it?` → follow-up: artistic project, short film or thesis
4. `How many credits are required to graduate?` → at least 128, of which the major is 48
5. `How many credits does the Computer Science major require?` → declined (outside my scope)
6. `How much is the tuition fee?` → "I could not find this in the handbook."

Say for 3: "'it' is understood from the conversation." For 5: "Before the fix the bot said 48 here,
the AMS figure; the real CS figure is 56."

**4. Evaluation (show files)**
- Open `eval/questions.json`: "20 test questions in 8 categories."
- Open `eval/results/results.md`: "Expected page retrieved for 100% of questions. I marked each answer:
  11 correct, 4 incomplete, 3 incorrect, 2 ambiguous." Give one example of each:
  - incomplete: materials fees are spread over 5 pages, top-5 retrieval finds only 2;
  - incorrect: "major code" — the handbook has no code, the model invented one;
  - ambiguous: ARTS 305 — the handbook gives two different prerequisite lists.
- Open `eval/results/scope_results.md`: "25 real questions from the Maths and CS handbooks. Without the
  guard the bot answered 14 of them, 7 with AMS facts. With the guard it declines all 25 and still answers
  all 25 control questions."

---

## Video 3 — Task 3: Docker container deployment (~2 min)

(Docker is not installed on this laptop, so this video presents the configuration.
Say this honestly at the start.)

**1. Purpose (say)**
"Task 3 packages the chatbot in Docker so it runs the same way on any machine, with all dependencies
inside the containers."

**2. Implementation (show `docker/Dockerfile`)**
- "Based on python:3.10-slim. It installs requirements.txt, copies the source code, and starts the
  Flask app with gunicorn on port 8000. A healthcheck calls /api/info."

**3. Configuration (show `docker/docker-compose.yml`)**
- "Three services. `ollama` runs the model server; models are stored in a volume so they are downloaded
  only once. `ollama-init` runs once, pulls nomic-embed-text and the LLM, then exits. `app` is the
  chatbot; it waits until the models are ready."
- Point at the volumes: "The handbook folder is mounted read-only — adding a PDF there rebuilds the
  index. The vector store and the saved conversations are named volumes, so they survive restarts."
- Point at the environment variables: "Settings are environment variables, so the model can be changed
  without editing code, for example `LLM_MODEL=qwen2.5:3b docker compose up`."

**4. Instructions (show README, section "Option B: run with Docker")**
```
cd docker
docker compose up --build
```
"Then open http://localhost:8000." Mention the macOS note (no GPU in Docker on Mac, so run Ollama
natively and only the app container).

---

## Video 4 — Task 4: UI/UX deployment (~3 min)

Open http://127.0.0.1:8000 (server: `python app.py` in `source_code`). Click "New reading" first.

**1. Purpose (say)**
"Task 4 is a web interface: question input, answer display and conversation history. I built it with
Flask and my own HTML, CSS and JavaScript, so it also works offline."

**2. Design (say while showing the page)**
"It is designed as a Victorian tarot reading table: rose damask background, lace edges, falling rose
petals, and a 78-card tarot deck on the left that shuffles while the model thinks and draws a card when
the answer arrives."

**3. Question and answer**
- Ask `What are the prerequisites for ARTS 309?` — point at: words appearing as they stream, the card
  shuffling, the page citation.
- Click "Found on pages …" to open the excerpts: "These are the retrieved passages and their scores."
- Ask `What about Computer Science?` — "Out-of-scope questions are declined and shown in italics."

**4. Conversation history**
- Ask `How often is it offered?` after an ARTS 309 question — "follow-up questions use the history."
- Click **Past readings**: "Every conversation is saved on the server. I can reopen one, delete it, or
  export it as Markdown or JSON." Open an older reading to show it coming back.
- Click **New reading**: "A new conversation; the old one stays in the list."

**5. Extras (quickly)**
- Click **Tiếng Việt**: the interface switches to Vietnamese. Ask
  `Ngành AMS cần bao nhiêu tín chỉ để tốt nghiệp?` — the answer comes in Vietnamese.
- Click **Vellum** for the light theme.
- Optional: make the browser window narrow to show the phone layout.

Close: "Everything — models, index, history — runs on this laptop, with no internet needed."
