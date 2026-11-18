# Report outline (Task 5, at least 1,500 words)

A skeleton to write the report from. Fill the brackets with your own results after running
`python -m eval.run_eval`. Rough word budget in parentheses.

## 1. Introduction (150)
* Problem: LLMs hallucinate and do not know FUV-specific documents.
* Goal: a local, private RAG chatbot for the Art & Media Studies Major Handbook.
* Why local: privacy, no API cost, works offline, full visibility of the pipeline.

## 2. System architecture (300)
* Diagram: PDF → loader + cleaning → chunks (800/150) → nomic-embed-text → ChromaDB (cosine) → top-5 → filter (≥0.35) → prompt → Qwen 2.5 via Ollama → streamed answer + page citations.
* One paragraph per component, and why each setting was chosen.
* Table of the 7 changes compared with the baseline (see README "Improvements").

## 3. Task 1: PDF support (150)
* pypdf, one Document per page so each chunk keeps its page number.
* Observation worth reporting: pypdf inserts stray spaces inside words in the AMS handbook ("s tudents", "c urriculum", "als o", "o r", "socio -economic"). A split word is tokenized and embedded differently from the real word, so it hurts retrieval. Fixed in `repair_split_words()`: with no dictionary offline, the handbook's own vocabulary is used, joining two pieces when the joined word appears elsewhere more often than the rarer piece. Result: 10 repairs in AMS, 4 in CS, no wrong merges found. Words that occur only once ("increasing ly") stay broken: a limitation to discuss.
* Some other handbooks (e.g. CS) also have heading fonts whose "ti" glyph extracts as `;` or `8` ("Descrip;on"), fixed with a targeted regex.
* Other cleaning: NFKC for ligatures ("ﬁ"), removing table-of-contents dot leaders.
* Comparison you can mention: pdfplumber kept table cells in a different order than pypdf on the course catalogue page.
* Test PDF: the project brief itself (`data/test_pdf/`), with 2 example questions.

## 4. Task 2: Handbook chatbot and evaluation (450, the core section)
* Why the Art & Media Studies handbook (fits the art-themed UI; 32 pages with requirements, a full course catalogue and long course descriptions).
* Test set: 20 questions in 8 categories (`eval/questions.json`).
* Metrics: retrieval hit (expected page retrieved), keyword score, time, manual verdict.
* Results table per model (0.5b / 1.5b / 3b): [paste summary from results.md].
* At least 2 examples each of Correct, Incorrect, Incomplete, Ambiguous, with the reason:
  * Retrieval failure: right page not retrieved (check `retrieved_pages`).
  * Generation failure: right page retrieved but the model misread or invented (e.g. wrong course code).
  * Answer spread across pages (Q10 "which courses have a materials fee?"): fees appear on 5 different pages, top-5 retrieval cannot collect them all, so answers are incomplete.
  * The handbook contradicts itself (Q17, Q18): for ARTS 305 the catalogue table says "one 200-level course" but the description says "two"; for ARTS 307 the two sections list different courses. Which page gets retrieved decides the answer. Shows that RAG is only as reliable as its documents.
  * Missing information (Q19): the cover has the label "MAJOR CODE" with no number. Does the model admit it, or invent one?
  * Unanswerable (Q19, Q20): does the model refuse, or still invent a tuition fee?
* Prompt design: baseline told the model to use general knowledge when context is weak; we changed to "answer only from context". Discuss the trade-off (fewer hallucinations, more refusals).
* Model size: accuracy vs speed on your machine [numbers].

## 5. Task 3: Docker deployment (200)
* Why three services (ollama, ollama-init, app), volumes for models and index, read-only data mount.
* Environment variables instead of hard-coded settings.
* Problems you met while building (image size, first model download time, macOS GPU limitation and the host.docker.internal alternative).

## 6. Task 4: User interface (200)
* Flask + hand-written HTML/CSS/JS instead of Streamlit/Gradio: full control of the design and no external CDN, so it works offline like the rest of the system.
* Design choice: a tarot reading table inspired by a gothic event poster: three colours only (black, bone white, red), red blackletter title with small-caps corner labels, lace edges and feathers. The conversation has no boxes or borders. A 78-card tarot deck (exported from a Figma Community file, credited) sits on the left: it shuffles while the model thinks and draws a card when the answer arrives, which turns the waiting time of a slow local model into part of the experience. Two themes (Noir, Vellum). Fonts can be stored locally so it works offline.
* Streaming tokens (local models are slow, seeing words appear feels faster), page citations highlighted, source excerpts on demand, history kept across reloads, follow-ups.
* Screenshots: `report/screenshots/`.

## 7. Limitations and future work (150)
* No OCR; table structure lost; small models; single collection.
* Ideas: hybrid search (BM25 + vectors) for course codes like "ARTS 305", a reranker, table-aware chunking, section headers added to each chunk, RAGAS metrics, model choice in the UI.

## 8. Lessons learned and conclusion (100)

## Links
* GitHub: [link]
* Videos: [links if hosted outside Canvas]
