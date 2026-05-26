"""
FastAPI application entry point.

Start the server with:
    uvicorn app.main:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, ingest
from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.api.session_routes import router as session_router
from app.api.superadmin_routes import router as superadmin_router
from app.auth_utils import get_session
from app.config import settings
from app.db import init_db
from app.dependencies import get_embedder, get_store
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)
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
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(admin_router)
app.include_router(superadmin_router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("app/static/index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse("app/static/login.html")


@app.get("/admin", include_in_schema=False)
def admin_page(request: Request):
    s = get_session(request.cookies.get("session_token"))
    if not s or s["role"] != "admin":
        return RedirectResponse("/login")
    return FileResponse("app/static/admin.html")


@app.get("/superadmin", include_in_schema=False)
def superadmin_page(request: Request):
    s = get_session(request.cookies.get("session_token"))
    if not s or s["role"] != "superadmin":
        return RedirectResponse("/login")
    return FileResponse("app/static/superadmin.html")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    store = get_store()
    return HealthResponse(
        status="ok",
        qdrant="reachable" if store.ping() else "unreachable",
        collection=settings.COLLECTION_NAME,
        embedding_model=settings.EMBEDDING_MODEL,
    )
