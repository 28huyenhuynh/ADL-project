#!/usr/bin/env python3
"""
Task 4: web interface for the handbook chatbot.

  python app.py            -> open http://127.0.0.1:8000
  MOCK=1 python app.py     -> fake answers, no Ollama needed (for working on the UI)

Flask serves one HTML page (templates/index.html). The page sends the question and
the recent conversation to /api/ask and receives the answer as a stream, so the
words appear while the local model is still generating.
"""

import json
import os
import threading

from flask import Flask, Response, jsonify, render_template, request

from rag import config

app = Flask(__name__)

_pipeline = None
_lock = threading.Lock()


def get_pipeline():
    """Created on the first question, so the server starts even while Ollama is loading."""
    global _pipeline
    with _lock:
        if _pipeline is None:
            if os.getenv("MOCK") == "1":
                from rag.mock import MockPipeline
                _pipeline = MockPipeline()
            else:
                from rag.pipeline import RAGPipeline
                _pipeline = RAGPipeline()
        return _pipeline


@app.get("/")
def index():
    return render_template("index.html", title=config.APP_TITLE)


@app.get("/api/info")
def info():
    return jsonify({
        "title": config.APP_TITLE,
        "model": config.LLM_MODEL,
        "embedding": config.EMBED_MODEL,
        "top_k": config.TOP_K,
    })


TAROT_DIR = os.path.join(app.static_folder, "tarot")


@app.get("/api/deck")
def deck():
    """Tarot card images exported into static/tarot/, in deck order (see tarot.py).
    Empty list means the page uses its built-in drawn cards."""
    from tarot import load_deck
    data = load_deck(TAROT_DIR)
    data["credit"] = {
        "artist": config.TAROT_ARTIST,
        "title": config.TAROT_TITLE,
        "author": config.TAROT_AUTHOR,
        "source": config.TAROT_SOURCE,
        "license": config.TAROT_LICENSE,
        "license_url": config.TAROT_LICENSE_URL,
    }
    return jsonify(data)


@app.post("/api/ask")
def ask():
    body = request.get_json(force=True)
    question = (body.get("question") or "").strip()
    history = body.get("history") or []
    if not question:
        return jsonify({"error": "Empty question"}), 400

    def generate():
        try:
            rag = get_pipeline()
            plan = rag.prepare(question, history)
            sources = plan["sources"]
            yield json.dumps({"type": "sources", "scope": plan["reason"], "lang": plan.get("lang"),
                              "question_en": plan.get("question_en"), "sources": [
                {"source": s["source"], "page": s["page"], "score": s["score"], "text": s["content"][:400]}
                for s in sources
            ]}) + "\n"
            answer = ""
            for token in rag.stream(question, plan, history):
                answer += token
                yield json.dumps({"type": "token", "text": token}) + "\n"
            # Numbers the small model wrote that appear in none of the passages (e.g. an
            # invented "120 credits") are flagged under the answer.
            from rag.scope import ungrounded_numbers
            unsupported = ungrounded_numbers(answer, sources, question + " " + (plan.get("question_en") or "")) if sources else []
            if unsupported:
                yield json.dumps({"type": "warning", "numbers": unsupported}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
        except Exception as error:  # e.g. Ollama not running or model not pulled
            yield json.dumps({"type": "error", "text": f"{type(error).__name__}: {error}"}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"Open http://{'localhost' if host == '0.0.0.0' else host}:{port}")
    app.run(host=host, port=port, threaded=True)
