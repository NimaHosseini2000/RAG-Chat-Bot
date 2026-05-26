"""Password hashing and in-memory session management."""
from __future__ import annotations

import secrets
from typing import Optional

import bcrypt

# token -> {role, user_id, username}
_sessions: dict[str, dict] = {}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_session(role: str, user_id: int, username: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"role": role, "user_id": user_id, "username": username}
    return token


def get_session(token: str | None) -> Optional[dict]:
    if not token:
        return None
    return _sessions.get(token)


def destroy_session(token: str) -> None:
    _sessions.pop(token, None)
