"""
FastAPI application entry point.

Start the server with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Interactive API docs are available at http://localhost:8000/docs once running.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, ingest
from app.config import settings
from app.dependencies import get_embedder, get_store
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up singletons and verify connectivity on startup."""
    get_embedder()
    store = get_store()
    if not store.ping():
        raise RuntimeError(
            f"Cannot connect to Qdrant at "
            f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}. "
            "Make sure Qdrant is running before starting the server."
        )
    store.ensure_collection()
    yield


app = FastAPI(
    title="Persian RAG Chatbot",
    description="Question-answering over Persian/Farsi documents via Qdrant + OpenAI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(chat.router)
app.include_router(ingest.router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """Liveness check — returns service status and Qdrant connectivity."""
    store = get_store()
    return HealthResponse(
        status="ok",
        qdrant="reachable" if store.ping() else "unreachable",
        collection=settings.COLLECTION_NAME,
        embedding_model=settings.EMBEDDING_MODEL,
    )
