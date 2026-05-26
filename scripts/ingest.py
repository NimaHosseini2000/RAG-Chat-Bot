#!/usr/bin/env python3
"""
CLI ingestion pipeline.

Scans a file or directory for supported documents (PDF, Word, images),
normalizes the text, chunks it with overlap, embeds each chunk with a
multilingual sentence-transformer, and uploads the vectors to Qdrant.

Run from the project root:

    python scripts/ingest.py path/to/documents/
    python scripts/ingest.py path/to/documents/ --recursive
    python scripts/ingest.py path/to/documents/ --recursive --recreate
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import uuid
from typing import List

from qdrant_client.models import PointStruct

from app.config import settings
from app.ingestion.chunker import chunk_text
from app.ingestion.normalizer import normalize_persian
from app.ingestion.readers import SUPPORTED_EXTENSIONS, read_file
from app.vectorstore.embedder import Embedder
from app.vectorstore.qdrant_store import QdrantStore


def collect_files(input_path: Path, recursive: bool) -> List[Path]:
    """Return all supported files under *input_path*."""
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in SUPPORTED_EXTENSIONS else []
    pattern = "**/*" if recursive else "*"
    return [
        f for f in sorted(input_path.glob(pattern))
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def run(files: List[Path], recreate: bool = False) -> None:
    store = QdrantStore()
    if not store.ping():
        print(
            f"ERROR: Cannot reach Qdrant at "
            f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}. "
            "Make sure it is running."
        )
        sys.exit(1)

    store.ensure_collection(recreate=recreate)
    embedder = Embedder()
    print()

    total_chunks = 0

    for file_path in files:
        print(f"Processing  : {file_path}")

        try:
            pages = read_file(file_path)
        except Exception as exc:
            print(f"  SKIPPED   : {exc}\n")
            continue

        chunk_records: list[dict] = []
        for page in pages:
            clean = normalize_persian(page["text"])
            if not clean.strip():
                continue
            for chunk in chunk_text(clean):
                chunk_records.append({
                    "chunk":  chunk,
                    "page":   page["page"],
                    "urls":   page["urls"],
                    "method": page["method"],
                })

        if not chunk_records:
            print("  No text extracted — skipping.\n")
            continue

        texts = [r["chunk"] for r in chunk_records]
        vectors = embedder.encode(texts, batch_size=64, show_progress=True)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i].tolist(),
                payload={
                    "text":   chunk_records[i]["chunk"],
                    "source": str(file_path),
                    "page":   chunk_records[i]["page"],
                    "urls":   chunk_records[i]["urls"],
                    "method": chunk_records[i]["method"],
                },
            )
            for i in range(len(chunk_records))
        ]

        store.upsert(points)
        total_chunks += len(points)
        print(f"  Indexed   : {len(points)} chunks\n")

    print("─" * 50)
    print(f"Total chunks indexed : {total_chunks}")
    print(f"Collection size      : {store.count()} points")
    print(f"Qdrant dashboard     : http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/dashboard")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest PDF, Word, and image files into the Qdrant knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Path to a file or directory to ingest.")
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively search subdirectories.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the collection before ingesting.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Path does not exist: {input_path}")
        sys.exit(1)

    files = collect_files(input_path, recursive=args.recursive)
    if not files:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"No supported files found. Accepted extensions: {exts}")
        sys.exit(0)

    print(f"Found {len(files)} file(s) to process.\n")
    run(files, recreate=args.recreate)


if __name__ == "__main__":
    main()
