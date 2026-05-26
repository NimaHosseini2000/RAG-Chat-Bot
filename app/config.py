"""
Central configuration loaded from environment variables or a .env file.
Copy .env.example to .env and fill in your values before running.
"""

import os
import secrets as _secrets
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # â”€â”€ Qdrant â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "knowledge_base")

    # â”€â”€ Embedding model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # NOTE: all-MiniLM-L6-v2 is English-only. For Persian/Farsi documents use
    # paraphrase-multilingual-MiniLM-L12-v2 instead (same 384-dim vector size).
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", "384"))

    # â”€â”€ LLM (OpenAI) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    MOCK_LLM: bool = os.getenv("MOCK_LLM", "false").lower() == "true"

    # â”€â”€ OCR (Tesseract) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    TESSERACT_CMD: str = os.getenv(
        "TESSERACT_CMD",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )
    # fas = Farsi/Persian  |  eng = English (preserves URLs and mixed content)
    OCR_LANG: str = os.getenv("OCR_LANG", "fas+eng")

    # â”€â”€ Chunking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "200"))       # words per chunk
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "30"))  # overlapping words

    # â”€â”€ Ingestion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    UPLOAD_BATCH_SIZE: int = int(os.getenv("UPLOAD_BATCH_SIZE", "100"))

    # PDF pages with fewer characters than this threshold trigger OCR fallback
    OCR_FALLBACK_THRESHOLD: int = int(os.getenv("OCR_FALLBACK_THRESHOLD", "50"))

    # ── Dashboard / Auth ─────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", _secrets.token_urlsafe(32))
    DB_PATH: str = os.getenv("DB_PATH", "data/chatbot.db")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")


settings = Settings()


