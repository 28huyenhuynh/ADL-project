#!/usr/bin/env python3
"""
Out-of-scope evaluation: does the AMS chatbot decline questions about OTHER majors?

  python -m eval.run_scope_eval                 # guarded pipeline vs. baseline, default model
  python -m eval.run_scope_eval --skip-baseline # only the guarded pipeline (faster)

The questions in eval/out_of_scope.json are real questions answered by the Applied
Mathematics and Computer Science handbooks (with the true answer and page from those
handbooks). The AMS bot cannot know those answers, so the only correct behaviour is to
decline. Many are shaped exactly like AMS questions ("How many credits does the CS major
require?"), which is the trap: retrieval finds AMS passages about credits, and an
unguarded model answers with the AMS figure (48) instead of the true CS figure (56).

Two kinds of control check that the guard is not too strict:
  * C1-C5 in out_of_scope.json name another subject but are really about AMS
    ("Can I take ARTS 313 if I completed SOCI 102?") and must be answered;
  * the 20 AMS questions from eval/questions.json must all be answered.

Modes:
  guarded   the current pipeline (scope guard + grounded prompt + memory rules)
  baseline  the same index and model, but no scope guard, the original prompt and the
            original follow-up rule: what the bot did before the hallucination fix.

Results: eval/results/scope_results.md and scope_results.json
"""

import argparse
import json
import time
from pathlib import Path

from rag import config
from rag.pipeline import NOT_FOUND, RAGPipeline

HERE = Path(__file__).parent
OUT = HERE / "results"
DECLINE_REASONS = {"other_subject", "off_topic"}

# The prompt the chatbot used before the scope fix (kept here only for the comparison).
BASELINE_PROMPT = """You are a helpful assistant that answers questions about {description}.

Use ONLY the context below. Each context block starts with its page number.
If the context does not contain the answer, reply exactly: "{not_found}"
Do not invent course codes, numbers or policies.
Keep the answer short (2 to 5 sentences, or a short list) and mention the page you used, like (p. 7).
{history}
CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def baseline_ask(rag: RAGPipeline, question: str, history: list[dict]) -> dict:
    query = question
    if history and len(question.split()) < 8:  # the original follow-up rule
        query = history[-1]["question"] + " " + question
    sources = [s for s in rag._search(query) if s["score"] >= config.SCORE_THRESHOLD]
    if not sources:
        return {"answer": NOT_FOUND, "reason": "no_context", "sources": []}
    turns = history[-config.HISTORY_TURNS:] if config.HISTORY_TURNS else []
    history_text = ""
    if turns:
        history_text = ("\nPREVIOUS CONVERSATION (for understanding follow-up questions):\n"
                        + "\n\n".join(f"User: {t['question']}\nAssistant: {t['answer']}" for t in turns) + "\n")
    prompt = BASELINE_PROMPT.format(
        description=config.DOC_DESCRIPTION, not_found=NOT_FOUND, history=history_text,
        context="\n\n---\n\n".join(f"[page {s['page']}]\n{s['content']}" for s in sources),
        question=question,
    )
    return {"answer": rag.llm.invoke(prompt).strip(), "reason": "answer", "sources": sources}


def run(rag: RAGPipeline, mode: str, question: str, history_questions: list[str]) -> dict:
    ask = rag.ask if mode == "guarded" else (lambda q, h: baseline_ask(rag, q, h))
    history = []
    for hq in history_questions:  # earlier turns get real answers from the same mode
        history.append({"question": hq, "answer": ask(hq, list(history))["answer"]})
    start = time.time()
    result = ask(question, history)
    result["seconds"] = round(time.time() - start, 1)
    result["history"] = history
    return result


def declined(result: dict) -> bool:
    return result.get("reason") in DECLINE_REASONS or NOT_FOUND.lower() in result["answer"].lower()


def evaluate(model: str, cases: list[dict], ams_questions: list[dict], modes: list[str]) -> list[dict]:
    rag = RAGPipeline(llm_model=model, verbose=False)
    rows = []
    for mode in modes:
        for case in cases:
            r = run(rag, mode, case["question"], case.get("history", []))
            expect = case.get("expect", "decline")
            ok = declined(r) if expect == "decline" else not declined(r)
            trap = case.get("ams_trap")
            repeats_ams = bool(trap) and not declined(r) and trap.lower() in r["answer"].lower()
            rows.append({**case, "expect": expect, "mode": mode, "model": model, "answer": r["answer"],
                         "reason": r.get("reason"), "declined": declined(r), "pass": ok,
                         "repeats_ams_fact": repeats_ams, "seconds": r["seconds"],
                         "unsupported_numbers": r.get("unsupported_numbers", [])})
            print(f"[{model}/{mode}] {case['id']:>4}  {'PASS' if ok else 'FAIL'}  "
                  f"{'declined' if declined(r) else 'answered'} ({r.get('reason')})  {r['seconds']}s")
    if "guarded" in modes:  # AMS questions: the guard must not refuse them
        for q in ams_questions:
            r = run(rag, "guarded", q["question"], [])
            ok = not declined(r) or not q["pages"]  # Q20 (tuition) is meant to be "not found"
            rows.append({"id": f"A{q['id']}", "category": "Control: AMS evaluation question",
                         "question": q["question"], "expect": "answer" if q["pages"] else "not found",
                         "mode": "guarded", "model": model, "answer": r["answer"], "reason": r.get("reason"),
                         "declined": declined(r), "pass": ok, "repeats_ams_fact": False,
                         "seconds": r["seconds"], "source": "AMS_MajorHandbook.pdf",
                         "true_answer": q["expected"]})
            print(f"[{model}/guarded] A{q['id']:>3}  {'PASS' if ok else 'FAIL'}  ({r.get('reason')})")
    return rows


def cell(text: str, limit: int = 220) -> str:
    text = " ".join((text or "").split()).replace("|", "/")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def to_markdown(rows: list[dict]) -> str:
    lines = ["# Out-of-scope evaluation", "",
             "Questions answered by the **Applied Mathematics** and **Computer Science** handbooks, asked to the",
             "**AMS** chatbot. The AMS bot cannot know these answers, so the correct behaviour is to decline.",
             "Controls check that AMS questions (including ones that mention another subject) are still answered.",
             "", f"Model `{rows[0]['model']}`, embedding `{config.EMBED_MODEL}`, top-k {config.TOP_K}, "
             f"scope thresholds {config.SCOPE_THRESHOLD}/{config.SCOPE_CONFIRM}.", "",
             "## Summary", "",
             "| Mode | Other-major questions declined | Answered anyway | …of which repeat an AMS fact | Controls answered |",
             "|---|---|---|---|---|"]
    for mode in ("baseline", "guarded"):
        m = [r for r in rows if r["mode"] == mode]
        if not m:
            continue
        out = [r for r in m if r["expect"] == "decline"]
        ctl = [r for r in m if r["expect"] != "decline"]
        lines.append(f"| {mode} | {sum(r['declined'] for r in out)}/{len(out)} | "
                     f"{sum(not r['declined'] for r in out)} | {sum(r['repeats_ams_fact'] for r in out)} | "
                     f"{sum(r['pass'] for r in ctl)}/{len(ctl)} |")
    lines += ["", "*baseline* = same index and model, without the scope guard, with the original prompt and",
              "follow-up rule. *Repeat an AMS fact* = the answer contains the AMS figure the question is a trap",
              "for (e.g. 48 credits or GPA 3.6), i.e. an AMS fact presented as another major's.", ""]

    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], {})[r["mode"]] = r
    lines += ["## Other-major questions and controls", "",
              "| # | Category | Question | True answer (source) | Guarded | Baseline answer |", "|---|---|---|---|---|---|"]
    for rid, modes in by_id.items():
        g, b = modes.get("guarded"), modes.get("baseline")
        if rid.startswith("A"):
            continue
        any_r = g or b
        q = any_r["question"]
        if any_r.get("history"):
            q = " → ".join(any_r["history"] + [q])
        gtxt = "—" if not g else (("✅ " if g["pass"] else "❌ ") + ("declined" if g["declined"] else "answered: " + cell(g["answer"], 120)))
        btxt = "—" if not b else (("✅ " if b["pass"] else "❌ ") + cell(b["answer"]))
        lines.append(f"| {rid} | {any_r['category']} | {cell(q, 160)} | {cell(any_r['true_answer'], 120)} ({any_r['source']}) | {gtxt} | {btxt} |")

    ams = [r for r in rows if r["id"].startswith("A")]
    if ams:
        lines += ["", "## AMS evaluation questions (guarded): must not be refused", "",
                  "| # | Question | Result | Answer |", "|---|---|---|---|"]
        for r in ams:
            lines.append(f"| {r['id']} | {r['question']} | {'✅' if r['pass'] else '❌'} {r['reason']} | {cell(r['answer'], 140)} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=config.LLM_MODEL)
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--skip-ams", action="store_true", help="do not re-run the 20 AMS control questions")
    args = parser.parse_args()

    cases = json.loads((HERE / "out_of_scope.json").read_text(encoding="utf-8"))
    ams = [] if args.skip_ams else json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    modes = ["guarded"] if args.skip_baseline else ["baseline", "guarded"]

    rows = evaluate(args.model, cases, ams, modes)
    OUT.mkdir(exist_ok=True)
    (OUT / "scope_results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "scope_results.md").write_text(to_markdown(rows), encoding="utf-8")
    print(f"\nSaved to {OUT / 'scope_results.md'}")


if __name__ == "__main__":
    main()
