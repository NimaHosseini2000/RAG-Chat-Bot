"""FastAPI dependencies for role-based access control."""
from __future__ import annotations

from fastapi import Cookie, HTTPException, status

from app.auth_utils import get_session


def require_admin(session_token: str | None = Cookie(default=None)) -> dict:
    s = get_session(session_token)
    if not s or s["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required")
    return s


def require_superadmin(session_token: str | None = Cookie(default=None)) -> dict:
    s = get_session(session_token)
    if not s or s["role"] != "superadmin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Super admin login required")
    return s
