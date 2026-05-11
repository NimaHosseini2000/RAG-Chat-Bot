"""
FastAPI dependency providers.

Each provider is cached with functools.lru_cache so the heavy objects
(embedding model, Qdrant client) are created once and reused across requests.
Inject them into route handlers via FastAPI's Depends() mechanism.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.rag.generator import Generator
from app.rag.retriever import Retriever
from app.vectorstore.embedder import Embedder
from app.vectorstore.qdrant_store import QdrantStore


@lru_cache
def get_embedder() -> Embedder:
    return Embedder()


@lru_cache
def get_store() -> QdrantStore:
    return QdrantStore()


@lru_cache
def get_generator() -> Generator:
    return Generator()


def get_retriever(
    embedder: Embedder = Depends(get_embedder),
    store: QdrantStore = Depends(get_store),
) -> Retriever:
    return Retriever(embedder, store)
