"""Login / logout endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from app.auth_utils import create_session, destroy_session, get_session, verify_password
from app.db import get_conn

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    with get_conn() as conn:
        sa = conn.execute(
            "SELECT id, password_hash FROM superadmins WHERE username = ?",
            (req.username,),
        ).fetchone()
        if sa and verify_password(req.password, sa["password_hash"]):
            token = create_session("superadmin", sa["id"], req.username)
            response.set_cookie("session_token", token, httponly=True, samesite="lax")
            return {"role": "superadmin"}

        admin = conn.execute(
            "SELECT id, password_hash FROM admins WHERE username = ?",
            (req.username,),
        ).fetchone()
        if admin and verify_password(req.password, admin["password_hash"]):
            token = create_session("admin", admin["id"], req.username)
            response.set_cookie("session_token", token, httponly=True, samesite="lax")
            return {"role": "admin"}

    raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/logout")
async def logout(response: Response, session_token: str | None = Cookie(default=None)):
    if session_token:
        destroy_session(session_token)
    response.delete_cookie("session_token")
    return {"ok": True}


@router.get("/me")
async def me(session_token: str | None = Cookie(default=None)):
    s = get_session(session_token)
    if not s:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return s
