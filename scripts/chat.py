#!/usr/bin/env python3
"""
Interactive command-line chat session.

Loads the embedding model and connects to Qdrant once at startup,
then enters a read-eval-print loop where you can ask questions and
receive answers grounded in your indexed documents.

Run from the project root:

    python scripts/chat.py
    python scripts/chat.py --top-k 8
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from app.config import settings
from app.rag.generator import Generator
from app.rag.retriever import Retriever
from app.vectorstore.embedder import Embedder
from app.vectorstore.qdrant_store import QdrantStore

SEPARATOR = "─" * 60


def run_chat(top_k: int) -> None:
    print(SEPARATOR)
    print("  Persian RAG Chatbot")
    print(SEPARATOR)

    store = QdrantStore()
    if not store.ping():
        print(
            f"ERROR: Cannot reach Qdrant at "
            f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}.\n"
            "Make sure Qdrant is running before starting the chat."
        )
        return

    embedder = Embedder()
    retriever = Retriever(embedder, store)

    try:
        generator = Generator()
    except EnvironmentError as exc:
        print(f"ERROR: {exc}")
        return

    print(f"\nCollection '{settings.COLLECTION_NAME}' — {store.count()} indexed chunks.")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        context, sources, urls = retriever.retrieve(query, top_k=top_k)

        if not context.strip():
            print("Bot: No relevant information found in the knowledge base.\n")
            continue

        answer = generator.generate(query, context)
        print(f"\nBot: {answer}")

        if sources:
            print(f"\nSources ({len(sources)}):")
            for src in sources:
                print(f"  • {src}")

        if urls:
            print(f"\nURLs found in context:")
            for url in urls:
                print(f"  • {url}")

        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive CLI chat with the Persian RAG knowledge base."
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve per query (default: 5).",
    )
    args = parser.parse_args()
    run_chat(top_k=args.top_k)


if __name__ == "__main__":
    main()
