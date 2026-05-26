"""In-memory store for active student chat sessions."""
from __future__ import annotations

import datetime
import uuid
from typing import Optional

_active: dict[str, dict] = {}


def start_session(student_name: str, student_id: str) -> str:
    sid = str(uuid.uuid4())
    _active[sid] = {
        "session_id": sid,
        "student_name": student_name,
        "student_id": student_id,
        "started_at": datetime.datetime.now().isoformat(),
        "messages": [],
        "tokens_used": 0,
    }
    return sid


def get_active_session(session_id: str) -> Optional[dict]:
    return _active.get(session_id)


def append_message(
    session_id: str,
    role: str,
    content: str,
    sources: list | None = None,
    urls: list | None = None,
) -> None:
    sess = _active.get(session_id)
    if not sess:
        return
    msg: dict = {
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    if sources:
        msg["sources"] = sources
    if urls:
        msg["urls"] = urls
    sess["messages"].append(msg)


def add_tokens(session_id: str, tokens: int) -> None:
    sess = _active.get(session_id)
    if sess:
        sess["tokens_used"] += tokens


def pop_session(session_id: str) -> Optional[dict]:
    return _active.pop(session_id, None)
