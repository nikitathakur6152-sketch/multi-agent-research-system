"""Small SQLite store for accounts, login sessions, and saved research."""

import hashlib
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(
    os.getenv("RESEARCH_DB_PATH", str(Path(__file__).with_name("research.sqlite3")))
).expanduser()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS research_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                topic TEXT NOT NULL,
                search_results TEXT NOT NULL DEFAULT '',
                scraped_content TEXT NOT NULL DEFAULT '',
                report TEXT NOT NULL DEFAULT '',
                feedback TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        # Keep an existing database usable after upgrading from the no-login version.
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(research_runs)").fetchall()
        }
        if "user_id" not in columns:
            connection.execute("ALTER TABLE research_runs ADD COLUMN user_id INTEGER")


def create_user(email: str, password_hash: str) -> int | None:
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, password_hash, _now()),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def find_user(email: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def create_session(user_id: int, token_hash: str) -> None:
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    with _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (_now(),))
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, user_id, expires_at),
        )


def user_for_session(token_hash: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """SELECT users.id, users.email FROM sessions
               JOIN users ON users.id = sessions.user_id
               WHERE sessions.token_hash = ? AND sessions.expires_at > ?""",
            (token_hash, _now()),
        ).fetchone()
    return dict(row) if row else None


def delete_session(token_hash: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


def save_research(user_id: int, topic: str, result: dict[str, Any]) -> dict[str, Any]:
    created_at = _now()
    with _connect() as connection:
        cursor = connection.execute(
            """INSERT INTO research_runs
               (user_id, topic, search_results, scraped_content, report, feedback, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                topic,
                str(result.get("search_results", "")),
                str(result.get("scraped_content", "")),
                str(result.get("report", "")),
                str(result.get("feedback", "")),
                created_at,
            ),
        )
        run_id = cursor.lastrowid
    return {"id": run_id, "topic": topic, "created_at": created_at, **result}


def list_research(user_id: int, limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """SELECT id, topic, created_at FROM research_runs
               WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_research(run_id: int, user_id: int) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """SELECT id, topic, search_results, scraped_content, report, feedback, created_at
               FROM research_runs WHERE id = ? AND user_id = ?""",
            (run_id, user_id),
        ).fetchone()
    return dict(row) if row else None


initialize_database()
