# Demo video plan (Task 6, four videos, about 2 to 4 minutes each)

Record the screen with your voice. For each task: what it is for, how it was done, the result.

## Video 1: PDF support
1. Show the baseline: `run_txt.py` only globs `*.txt`.
2. Open `rag/loaders.py`: `load_pdf()` (one document per page) and `clean_text()`.
3. Show the split-word problem ("s tudents", "c urriculum"): print raw pypdf text of page 5, then the repaired text.
4. Run: `python cli.py --data-dir data/test_pdf --store vector_store/test_pdf -q "How much is the Docker task worth?"`
5. Point at the log (pages loaded, chunks indexed) and the answer with page and score.

## Video 2: Handbook chatbot
1. Explain why the Art & Media Studies handbook, show `data/handbook/`.
2. Open `rag/pipeline.py`: cosine store, threshold filter, grounded prompt, auto rebuild.
3. Interactive `python cli.py`: one good answer, one follow-up ("what about its prerequisites?"), one unanswerable question (tuition).
4. Run `python -m eval.run_eval --models qwen2.5:0.5b qwen2.5:1.5b` and open `eval/results/results.md`.
5. Show one correct, one incorrect, one incomplete answer and explain why.

## Video 3: Docker
1. Walk through `Dockerfile` and `docker-compose.yml` (three services, volumes).
2. `docker compose up --build`, show `ollama-init` pulling models and exiting.
3. `docker ps`, `docker compose logs app` (indexing), open http://localhost:8000.
4. `docker compose exec app python cli.py -q "..."` to show the container answers.

## Video 4: Web interface
1. Open the page, explain the tarot design idea (three colours, blackletter, lace and feathers), and browse a few cards with the arrows.
2. Click a suggested question: the card shuffles while the model thinks, then the answer streams in with its page citation.
3. Open "Found on pages ..." to show the retrieved excerpts.
4. Ask a follow-up, reload the page (history stays), click "New conversation".
5. Switch the system to dark mode, then show the narrow (phone) layout.
