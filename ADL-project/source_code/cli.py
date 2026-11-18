#!/usr/bin/env python3
"""
Ask the RAG system from the terminal.

Examples:
  python cli.py                                   # interactive chat with the AMS handbook
  python cli.py -q "What are the major requirements?"
  python cli.py --data-dir data/test_pdf --store vector_store/test_pdf -q "How much is Task 3 worth?"
  python cli.py --model qwen2.5:3b -q "What are the prerequisites for ARTS 309?"
"""

import argparse

from rag import config
from rag.pipeline import RAGPipeline


def show(result: dict):
    print("\nA: " + result["answer"] + "\n")
    if result["sources"]:
        print("Sources:")
        for s in result["sources"]:
            print(f"   {s['source']}  page {s['page']}  score={s['score']}")
    else:
        print("(no chunk passed the relevance threshold)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Local RAG over TXT and PDF files")
    parser.add_argument("-q", "--question", help="Ask one question and exit")
    parser.add_argument("--data-dir", help=f"Folder with .txt/.pdf files (default {config.DATA_DIR})")
    parser.add_argument("--store", help=f"Vector store folder (default {config.VECTOR_STORE})")
    parser.add_argument("--model", help=f"Ollama LLM (default {config.LLM_MODEL})")
    args = parser.parse_args()

    if args.data_dir:
        config.DATA_DIR = args.data_dir
    if args.store:
        config.VECTOR_STORE = args.store

    rag = RAGPipeline(llm_model=args.model)
    print(f"Model: {rag.llm_model}")

    if args.question:
        print("Q: " + args.question)
        show(rag.ask(args.question))
        return

    history = []
    print("Type a question (empty line to quit).")
    while True:
        try:
            question = input("Q: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            break
        result = rag.ask(question, history)
        show(result)
        history.append({"question": question, "answer": result["answer"]})


if __name__ == "__main__":
    main()
