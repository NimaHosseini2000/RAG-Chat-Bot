"""
Qdrant vector store: collection management, batch upsert, and semantic search.
"""

from __future__ import annotations

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.config import settings


class QdrantStore:
    def __init__(self) -> None:
        self._client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

    # ── Collection management ─────────────────────────────────────────────────

    def ping(self) -> bool:
        """Return True if Qdrant is reachable."""
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, recreate: bool = False) -> None:
        """Create the collection if it does not exist.

        When *recreate* is True the existing collection is deleted first,
        which lets you re-index from scratch without leftover stale vectors.
        """
        exists = self._client.collection_exists(settings.COLLECTION_NAME)
        if exists and recreate:
            self._client.delete_collection(settings.COLLECTION_NAME)
            exists = False

        if not exists:
            self._client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            print(f"Created collection '{settings.COLLECTION_NAME}'")
        else:
            print(f"Using existing collection '{settings.COLLECTION_NAME}'")

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert(self, points: List[PointStruct]) -> None:
        """Upload points in batches to avoid large single requests."""
        batch_size = settings.UPLOAD_BATCH_SIZE
        total = len(points)
        for start in range(0, total, batch_size):
            batch = points[start : start + batch_size]
            self._client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=batch,
            )
            end = min(start + batch_size, total)
            print(f"  Uploaded {end}/{total} points", end="\r")
        print()

    # ── Read ──────────────────────────────────────────────────────────────────

    def search(self, vector: List[float], top_k: int = 5) -> List[ScoredPoint]:
        """Return the top-k most similar points for the given query vector."""
        result = self._client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return result.points

    def count(self) -> int:
        """Return the number of points currently in the collection."""
        info = self._client.get_collection(settings.COLLECTION_NAME)
        return info.points_count
