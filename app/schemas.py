"""
Pydantic request and response schemas shared across all API routes.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="The user's question.")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve.")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    urls: List[str]


class IngestResponse(BaseModel):
    message: str
    chunks_indexed: int
    source: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    collection: str
    embedding_model: str
