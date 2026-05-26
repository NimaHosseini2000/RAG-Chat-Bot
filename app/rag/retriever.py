"""
Semantic retriever: encodes a query and fetches the top-k matching chunks
from Qdrant, then assembles them into a single context string.
"""

from __future__ import annotations

from typing import List, Tuple

from app.vectorstore.embedder import Embedder
from app.vectorstore.qdrant_store import QdrantStore


class Retriever:
    def __init__(self, embedder: Embedder, store: QdrantStore) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> Tuple[str, List[str], List[str]]:
        """Search the vector store and return context, sources, and URLs.

        Returns:
            context: Joined text passages separated by dividers.
            sources: Deduplicated list of source file paths.
            urls:    Deduplicated list of URLs found in the retrieved chunks.
        """
        query_vector = self._embedder.encode_one(query)
        hits = self._store.search(query_vector, top_k=top_k)

        contexts: List[str] = []
        sources: List[str] = []
        urls: List[str] = []

        for hit in hits:
            payload = hit.payload or {}
            text = payload.get("text", "")
            if text:
                contexts.append(text)
            source = payload.get("source", "")
            if source:
                sources.append(source)
            urls.extend(payload.get("urls", []))

        context_text = "\n\n---\n\n".join(contexts)
        return context_text, list(dict.fromkeys(sources)), list(dict.fromkeys(urls))
