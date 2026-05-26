"""
Sentence-transformer wrapper for multilingual text embedding.

Uses paraphrase-multilingual-MiniLM-L12-v2 by default, which supports 50+
languages including Persian/Farsi and produces 384-dimensional vectors.
The model is loaded once at construction time and reused for all calls.
"""

from __future__ import annotations

from typing import List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.config import settings


class Embedder:
    def __init__(self) -> None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL} on {device}")
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)

    def encode(
        self,
        texts: List[str],
        batch_size: int = 64,
        show_progress: bool = True,
    ) -> np.ndarray:
        """Encode a list of strings into a (N, D) float32 array.

        Embeddings are L2-normalised so cosine similarity equals dot product.
        """
        return self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
        )

    def encode_one(self, text: str) -> List[float]:
        """Encode a single string and return a plain Python float list."""
        vector: np.ndarray = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()
