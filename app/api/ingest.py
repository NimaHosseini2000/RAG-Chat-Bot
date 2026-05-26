"""
Ingest router — POST /ingest

Accepts a file upload, extracts and normalizes text, embeds the chunks,
and upserts them into the Qdrant collection.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from qdrant_client.models import PointStruct

from app.dependencies import get_embedder, get_store
from app.ingestion.chunker import chunk_text
from app.ingestion.normalizer import normalize_persian
from app.ingestion.readers import SUPPORTED_EXTENSIONS, read_file
from app.schemas import IngestResponse
from app.vectorstore.embedder import Embedder
from app.vectorstore.qdrant_store import QdrantStore

router = APIRouter(tags=["Ingestion"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    embedder: Embedder = Depends(get_embedder),
    store: QdrantStore = Depends(get_store),
) -> IngestResponse:
    """Upload a PDF, Word document, or image and index it into the knowledge base."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Accepted: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        pages = read_file(tmp_path)

        chunk_records: list[dict] = []
        for page in pages:
            clean = normalize_persian(page["text"])
            for chunk in chunk_text(clean):
                chunk_records.append({"chunk": chunk, "page": page})

        if not chunk_records:
            return IngestResponse(
                message="File processed but no text could be extracted.",
                chunks_indexed=0,
                source=file.filename,
            )

        texts = [r["chunk"] for r in chunk_records]
        vectors = embedder.encode(texts, show_progress=False)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i].tolist(),
                payload={
                    "text":   chunk_records[i]["chunk"],
                    "source": file.filename,
                    "page":   chunk_records[i]["page"]["page"],
                    "urls":   chunk_records[i]["page"]["urls"],
                    "method": chunk_records[i]["page"]["method"],
                },
            )
            for i in range(len(chunk_records))
        ]

        store.upsert(points)
        return IngestResponse(
            message="File indexed successfully.",
            chunks_indexed=len(points),
            source=file.filename,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
