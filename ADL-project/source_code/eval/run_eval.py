#!/usr/bin/env python3
"""
Task 2 evaluation: run every test question against one or more models.

  python -m eval.run_eval                                   # default model
  python -m eval.run_eval --models qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b

For each answer it records:
  - retrieval hit: was one of the expected pages among the retrieved chunks?
  - keyword score: share of expected keywords found in the answer (a rough hint only)
  - time in seconds
Results go to eval/results/. The "verdict" column in results.md is left empty on
purpose: read each answer and mark it Correct / Incorrect / Incomplete / Ambiguous.
"""

import argparse
import json
import time
from pathlib import Path

from rag import config
from rag.pipeline import NOT_FOUND, RAGPipeline

HERE = Path(__file__).parent
OUT = HERE / "results"


def norm(text: str) -> str:
    return text.lower().replace(" ", "")


def keyword_score(answer: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    found = sum(1 for k in keywords if norm(k) in norm(answer))
    return round(found / len(keywords), 2)


def evaluate(model: str, questions: list[dict]) -> list[dict]:
    rag = RAGPipeline(llm_model=model, verbose=False)
    rows = []
    for q in questions:
        start = time.time()
        result = rag.ask(q["question"])
        seconds = round(time.time() - start, 1)
        pages = sorted({s["page"] for s in result["sources"]})
        if q["pages"]:
            hit = any(p in pages for p in q["pages"])
        else:  # unanswerable question: a "hit" means the bot refused correctly
            hit = NOT_FOUND.lower() in result["answer"].lower()
        rows.append({
            **q,
            "model": model,
            "answer": result["answer"],
            "retrieved_pages": pages,
            "top_score": max((s["score"] for s in result["sources"]), default=0),
            "retrieval_hit": hit,
            "keyword_score": keyword_score(result["answer"], q["keywords"]),
            "seconds": seconds,
        })
        print(f"[{model}] Q{q['id']:>2}  hit={hit!s:5}  kw={rows[-1]['keyword_score']:.2f}  {seconds}s")
    return rows


def to_markdown(all_rows: list[dict]) -> str:
    lines = ["# Evaluation results", ""]
    lines.append(f"Embedding: `{config.EMBED_MODEL}`, chunk {config.CHUNK_SIZE}/{config.CHUNK_OVERLAP}, "
                 f"top-k {config.TOP_K}, threshold {config.SCORE_THRESHOLD}, temperature {config.TEMPERATURE}")
    lines.append("")

    models = sorted({r["model"] for r in all_rows})
    lines += ["## Summary", "", "| Model | Retrieval hit | Avg keyword score | Avg time (s) |", "|---|---|---|---|"]
    for m in models:
        rows = [r for r in all_rows if r["model"] == m]
        hit = sum(r["retrieval_hit"] for r in rows) / len(rows)
        kw = sum(r["keyword_score"] for r in rows) / len(rows)
        t = sum(r["seconds"] for r in rows) / len(rows)
        lines.append(f"| {m} | {hit:.0%} | {kw:.2f} | {t:.1f} |")
    lines.append("")

    for m in models:
        lines += [f"## {m}", "", "| # | Category | Question | Answer | Pages | Hit | KW | Verdict |", "|---|---|---|---|---|---|---|---|"]
        for r in (r for r in all_rows if r["model"] == m):
            answer = r["answer"].replace("\n", " ").replace("|", "/")
            lines.append(f"| {r['id']} | {r['category']} | {r['question']} | {answer} | "
                         f"{r['retrieved_pages']} | {'yes' if r['retrieval_hit'] else 'no'} | {r['keyword_score']} |  |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=[config.LLM_MODEL])
    parser.add_argument("--questions", default=str(HERE / "questions.json"))
    args = parser.parse_args()

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)

    all_rows = []
    for model in args.models:
        rows = evaluate(model, questions)
        (OUT / f"results_{model.replace(':', '_')}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        all_rows += rows

    (OUT / "results.md").write_text(to_markdown(all_rows), encoding="utf-8")
    print(f"\nSaved to {OUT}/results.md")


if __name__ == "__main__":
    main()
