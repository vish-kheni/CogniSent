"""
Business logic layer: runs predictions through the CNN model and keeps
a persistent SQLite-backed log of analyzed reviews that powers the
dashboard.

Reviews are stored in backend/data/history.db and survive server
restarts / browser sessions ending -- they're only removed if the
user explicitly clears history.

Each review is tagged with a `session_id` (generated client-side, one
per browser tab/page-load) so the Dashboard can group historical
reviews by the session they were analyzed in.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.services.model_registry import registry

DB_PATH = settings.MODELS_DIR.parent / "data" / "history.db"
_lock = threading.Lock()

UNKNOWN_SESSION = "legacy"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _lock:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review TEXT NOT NULL,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                probabilities TEXT NOT NULL,
                session_id TEXT NOT NULL DEFAULT 'legacy',
                created_at TEXT NOT NULL
            )
            """
        )
        # Backward-compatible migration for DBs created before session_id existed
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(reviews)")]
        if "session_id" not in cols:
            conn.execute(
                f"ALTER TABLE reviews ADD COLUMN session_id TEXT NOT NULL DEFAULT '{UNKNOWN_SESSION}'"
            )
        conn.commit()
        conn.close()


_init_db()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "review": row["review"],
        "label": row["label"],
        "confidence": row["confidence"],
        "probabilities": json.loads(row["probabilities"]),
        "session_id": row["session_id"],
        "created_at": row["created_at"],
    }


def analyze_text(text: str, session_id: str | None = None) -> dict:
    model = registry.get()
    result = model.predict(text)
    created_at = datetime.now(timezone.utc).isoformat()
    session_id = session_id or UNKNOWN_SESSION

    with _lock:
        conn = _get_conn()
        cur = conn.execute(
            "INSERT INTO reviews (review, label, confidence, probabilities, session_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                text,
                result["label"],
                result["confidence"],
                json.dumps(result["probabilities"]),
                session_id,
                created_at,
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

    return {
        "id": new_id,
        "review": text,
        "label": result["label"],
        "confidence": result["confidence"],
        "probabilities": result["probabilities"],
        "session_id": session_id,
        "created_at": created_at,
    }


def analyze_batch(texts: list[str], session_id: str | None = None) -> list[dict]:
    return [analyze_text(t, session_id) for t in texts]


def list_reviews(
    limit: int = 50,
    offset: int = 0,
    label: str | None = None,
    session_id: str | None = None,
) -> dict:
    clauses = []
    params: list = []
    if label:
        clauses.append("LOWER(label) = LOWER(?)")
        params.append(label)
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with _lock:
        conn = _get_conn()
        total = conn.execute(
            f"SELECT COUNT(*) FROM reviews {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM reviews {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        conn.close()

    return {"total": total, "items": [_row_to_dict(r) for r in rows]}


def list_sessions(limit: int = 20) -> list[dict]:
    """Returns recent sessions, most recent first, each with a summary
    of how many reviews were analyzed and their sentiment breakdown."""
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT
                session_id,
                COUNT(*) as total,
                MIN(created_at) as started_at,
                MAX(created_at) as last_activity_at,
                SUM(CASE WHEN label = 'Positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN label = 'Negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN label = 'Neutral' THEN 1 ELSE 0 END) as neutral
            FROM reviews
            GROUP BY session_id
            ORDER BY last_activity_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()

    return [
        {
            "session_id": r["session_id"],
            "total": r["total"],
            "started_at": r["started_at"],
            "last_activity_at": r["last_activity_at"],
            "sentiment_counts": {
                "Positive": r["positive"],
                "Negative": r["negative"],
                "Neutral": r["neutral"],
            },
        }
        for r in rows
    ]


def get_stats() -> dict:
    with _lock:
        conn = _get_conn()
        total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for row in conn.execute("SELECT label, COUNT(*) as c FROM reviews GROUP BY label"):
            counts[row["label"]] = row["c"]
        avg_row = conn.execute("SELECT AVG(confidence) as avg_conf FROM reviews").fetchone()
        avg_confidence = avg_row["avg_conf"] or 0.0
        conn.close()

    return {
        "total_reviews": total,
        "sentiment_counts": counts,
        "average_confidence": avg_confidence,
    }


def clear_reviews():
    with _lock:
        conn = _get_conn()
        conn.execute("DELETE FROM reviews")
        conn.commit()
        conn.close()


def delete_review(review_id: int) -> bool:
    """Deletes a single review by id. Returns True if a row was deleted."""
    with _lock:
        conn = _get_conn()
        cur = conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
    return deleted


def delete_session(session_id: str) -> int:
    """Deletes every review belonging to a session. Returns rows deleted."""
    with _lock:
        conn = _get_conn()
        cur = conn.execute("DELETE FROM reviews WHERE session_id = ?", (session_id,))
        conn.commit()
        deleted_count = cur.rowcount
        conn.close()
    return deleted_count
