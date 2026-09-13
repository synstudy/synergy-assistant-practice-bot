import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "app.db")))
_lock = threading.Lock()


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with _lock, _connect() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "session_id TEXT PRIMARY KEY, "
            "state TEXT NOT NULL, "
            "updated_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS leads ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "session_id TEXT, "
            "name TEXT, "
            "phone TEXT, "
            "program TEXT, "
            "created_at TEXT NOT NULL)"
        )


def _now():
    return datetime.now(timezone.utc).isoformat()


def get_session(session_id):
    with _connect() as connection:
        row = connection.execute(
            "SELECT state FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["state"])
    except json.JSONDecodeError:
        return None


def save_session(session_id, session):
    payload = json.dumps(session, ensure_ascii=False)
    with _lock, _connect() as connection:
        connection.execute(
            "INSERT INTO sessions (session_id, state, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
            (session_id, payload, _now()),
        )


def reset_session(session_id):
    with _lock, _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def save_lead(session_id, lead):
    with _lock, _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO leads (session_id, name, phone, program, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, lead.get("name"), lead.get("phone"), lead.get("program"), _now()),
        )
        return cursor.lastrowid


def get_leads(limit=100):
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, session_id, name, phone, program, created_at FROM leads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
