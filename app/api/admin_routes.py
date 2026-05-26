"""Admin dashboard API routes."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.auth_deps import require_admin
from app.db import get_conn
from app.schemas import TicketCreateRequest

router = APIRouter(prefix="/admin/api", tags=["Admin"])


@router.get("/stats")
async def stats(session: dict = Depends(require_admin)):
    with get_conn() as conn:
        admin = conn.execute(
            "SELECT display_name, token_limit, tokens_used FROM admins WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
        open_tickets = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE admin_id = ? AND status = 'open'",
            (session["user_id"],),
        ).fetchone()[0]
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    return {**dict(admin), "open_tickets": open_tickets, "total_sessions": total_sessions}


@router.get("/logs")
async def list_logs(_: dict = Depends(require_admin)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, student_name, student_id, tokens_used, started_at, ended_at "
            "FROM sessions ORDER BY started_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/logs/{session_id}")
async def get_log(session_id: str, _: dict = Depends(require_admin)):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT log_file FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    if not row or not row["log_file"]:
        raise HTTPException(status_code=404, detail="Log not found")
    p = Path(row["log_file"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="Log file missing on disk")
    return json.loads(p.read_text(encoding="utf-8"))


@router.get("/tickets")
async def list_tickets(session: dict = Depends(require_admin)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE admin_id = ? ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/tickets")
async def create_ticket(req: TicketCreateRequest, session: dict = Depends(require_admin)):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tickets (admin_id, title, description) VALUES (?, ?, ?)",
            (session["user_id"], req.title, req.description),
        )
    return {"ok": True}
