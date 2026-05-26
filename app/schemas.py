"""Pydantic request and response schemas shared across all API routes."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)
    session_id: str = Field("", description="Active student session ID for logging")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    urls: List[str]
    tokens_used: int = 0


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    student_id: str = Field("", max_length=50)


class SessionStartResponse(BaseModel):
    session_id: str


class SessionEndRequest(BaseModel):
    session_id: str


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)


class TicketRespondRequest(BaseModel):
    response: str = Field(..., min_length=1, max_length=2000)


# ── Admin management ──────────────────────────────────────────────────────────

class AdminCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    display_name: str = Field("", max_length=100)
    token_limit: int = Field(10000, ge=100)


class AdminUpdateRequest(BaseModel):
    display_name: str = Field("", max_length=100)
    token_limit: int = Field(10000, ge=100)
    password: str = Field("", max_length=100)  # empty = keep existing


# ── Ingest / Health ───────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    message: str
    chunks_indexed: int
    source: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    collection: str
    embedding_model: str
