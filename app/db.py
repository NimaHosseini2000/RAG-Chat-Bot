"""SQLite database — accounts, sessions, tickets."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.config import settings


def _db_path() -> Path:
    p = Path(settings.DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables and seed default accounts on first run."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS admins (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                display_name  TEXT    DEFAULT '',
                token_limit   INTEGER DEFAULT 10000,
                tokens_used   INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS superadmins (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id    INTEGER NOT NULL,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL,
                status      TEXT    DEFAULT 'open',
                response    TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT    DEFAULT '',
                FOREIGN KEY (admin_id) REFERENCES admins(id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id           TEXT    PRIMARY KEY,
                student_name TEXT    DEFAULT '',
                student_id   TEXT    DEFAULT '',
                tokens_used  INTEGER DEFAULT 0,
                started_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
                ended_at     TEXT    DEFAULT '',
                log_file     TEXT    DEFAULT ''
            );
        """)

    _seed_defaults()


def _seed_defaults() -> None:
    from app.auth_utils import hash_password

    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM superadmins").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO superadmins (username, password_hash) VALUES (?, ?)",
                ("superadmin", hash_password("superadmin123")),
            )
            print("  Default superadmin →  username: superadmin  |  password: superadmin123")

        if conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO admins (username, password_hash, display_name, token_limit) VALUES (?, ?, ?, ?)",
                ("admin", hash_password("admin123"), "University Admin", 10000),
            )
            print("  Default admin       →  username: admin       |  password: admin123")
