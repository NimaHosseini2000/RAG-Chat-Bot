"""Student session start / end endpoints."""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.db import get_conn
from app.schemas import SessionEndRequest, SessionStartRequest, SessionStartResponse
from app.session_store import pop_session, start_session

router = APIRouter(tags=["Session"])


@router.post("/session/start", response_model=SessionStartResponse)
async def session_start(req: SessionStartRequest) -> SessionStartResponse:
    with get_conn() as conn:
        admin = conn.execute(
            "SELECT token_limit, tokens_used FROM admins WHERE id = 1"
        ).fetchone()

    if admin and admin["tokens_used"] >= admin["token_limit"]:
        raise HTTPException(
            status_code=403,
            detail="محدودیت توکن به پایان رسیده است. لطفاً با مدیر سیستم تماس بگیرید.",
        )

    sid = start_session(req.student_name, req.student_id)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (id, student_name, student_id) VALUES (?, ?, ?)",
            (sid, req.student_name, req.student_id),
        )

    return SessionStartResponse(session_id=sid)


@router.post("/session/end")
async def session_end(req: SessionEndRequest):
    sess = pop_session(req.session_id)
    if not sess:
        return {"ok": True}

    sess["ended_at"] = datetime.datetime.now().isoformat()

    logs_dir = Path(settings.LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        c for c in sess["student_name"] if c.isalnum() or c in " _-"
    )[:20].strip().replace(" ", "_")
    filename = f"{ts}_{safe_name}_{req.session_id[:8]}.json"
    log_path = logs_dir / filename

    log_path.write_text(
        json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, log_file = ? WHERE id = ?",
            (sess["ended_at"], str(log_path), req.session_id),
        )

    return {"ok": True}
