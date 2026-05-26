"""Super admin API routes."""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.auth_deps import require_superadmin
from app.auth_utils import hash_password
from app.db import get_conn
from app.schemas import AdminCreateRequest, AdminUpdateRequest, TicketRespondRequest

router = APIRouter(prefix="/superadmin/api", tags=["SuperAdmin"])


@router.get("/stats")
async def stats(_: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        admins = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        open_tickets = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status = 'open'"
        ).fetchone()[0]
        total_tokens = (
            conn.execute("SELECT SUM(tokens_used) FROM admins").fetchone()[0] or 0
        )
    return {
        "admins": admins,
        "sessions": sessions,
        "open_tickets": open_tickets,
        "total_tokens": total_tokens,
    }


@router.get("/logs")
async def all_logs(_: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, student_name, student_id, tokens_used, started_at, ended_at "
            "FROM sessions ORDER BY started_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/logs/{session_id}")
async def get_log(session_id: str, _: dict = Depends(require_superadmin)):
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


@router.get("/admins")
async def list_admins(_: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, display_name, token_limit, tokens_used, created_at FROM admins"
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/admins")
async def create_admin(req: AdminCreateRequest, _: dict = Depends(require_superadmin)):
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO admins (username, password_hash, display_name, token_limit) VALUES (?, ?, ?, ?)",
                (req.username, hash_password(req.password), req.display_name, req.token_limit),
            )
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"ok": True}


@router.put("/admins/{admin_id}")
async def update_admin(
    admin_id: int, req: AdminUpdateRequest, _: dict = Depends(require_superadmin)
):
    with get_conn() as conn:
        if req.password:
            conn.execute(
                "UPDATE admins SET display_name=?, token_limit=?, password_hash=? WHERE id=?",
                (req.display_name, req.token_limit, hash_password(req.password), admin_id),
            )
        else:
            conn.execute(
                "UPDATE admins SET display_name=?, token_limit=? WHERE id=?",
                (req.display_name, req.token_limit, admin_id),
            )
    return {"ok": True}


@router.delete("/admins/{admin_id}")
async def delete_admin(admin_id: int, _: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        conn.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
    return {"ok": True}


@router.post("/admins/{admin_id}/reset-tokens")
async def reset_tokens(admin_id: int, _: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        conn.execute("UPDATE admins SET tokens_used = 0 WHERE id = ?", (admin_id,))
    return {"ok": True}


@router.get("/tickets")
async def all_tickets(_: dict = Depends(require_superadmin)):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT t.*, a.username AS admin_username, a.display_name AS admin_display_name
            FROM tickets t
            JOIN admins a ON t.admin_id = a.id
            ORDER BY t.created_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


@router.post("/tickets/{ticket_id}/respond")
async def respond_ticket(
    ticket_id: int, req: TicketRespondRequest, _: dict = Depends(require_superadmin)
):
    with get_conn() as conn:
        conn.execute(
            "UPDATE tickets SET status='resolved', response=?, resolved_at=? WHERE id=?",
            (req.response, datetime.datetime.now().isoformat(), ticket_id),
        )
    return {"ok": True}
