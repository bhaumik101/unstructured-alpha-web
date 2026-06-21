# utils/alerts_db.py
# Unstructured Alpha — Persistent Watchlist + Alert Storage
#
# Why this exists: every other piece of state in this app lives in
# st.session_state, which is wiped on every browser refresh or new session --
# fine for "what ticker am I looking at right now", wrong for "remember what
# I'm watching and what I've already seen" across visits, which is the whole
# point of alerting. This module is the one place that state is written to
# disk (SQLite), so it survives restarts.
#
# Known limitation, stated plainly: this is a single shared watchlist/alert
# feed for the whole app instance, not a per-user account system -- there is
# no login anywhere in this product. That's consistent with how the rest of
# the app already works (one FRED/EIA key in session_state, not per-user
# credentials), not a new compromise introduced here. If this product later
# gets real user accounts, this schema would need a user_id column added to
# every table.
#
# Also worth stating plainly: on Streamlit Community Cloud's free tier, the
# filesystem is not guaranteed persistent across redeploys/restarts -- this
# works reliably when self-hosted or run locally (this product's primary
# deployment story per DEPLOY.md), but a cloud-hosted instance could lose
# its watchlist on a redeploy. Worth a real database (e.g. a free-tier
# Postgres) if/when this moves to a persistent cloud deployment.
#
# DB location is deliberately OUTSIDE the project folder, in the user's home
# directory -- not a stylistic choice. Confirmed live (2026-06-21) that
# putting the SQLite file inside this project's folder causes a hard
# "disk I/O error" on every write: that folder lives under a cloud-synced
# path (iCloud Drive's Desktop & Documents sync, in this case), and cloud
# sync clients are a well-known source of SQLite locking/journal failures
# regardless of OS or filesystem -- this is not specific to any one sandbox,
# it would bite a real user running this locally just the same. Runtime
# state like a watchlist database has no business living inside a folder
# that's also being synced/version-controlled anyway.

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.expanduser("~"), ".unstructured_alpha", "data")
DB_PATH = os.path.join(DB_DIR, "alerts.db")

DEFAULT_SCORE_BULL_THRESHOLD = 65.0
DEFAULT_SCORE_BEAR_THRESHOLD = 35.0
DEFAULT_PRICE_MOVE_PCT_THRESHOLD = 5.0


@contextmanager
def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't already exist. Safe to call on every page load."""
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker TEXT PRIMARY KEY,
                score_bull_threshold REAL NOT NULL DEFAULT 65.0,
                score_bear_threshold REAL NOT NULL DEFAULT 35.0,
                price_move_pct_threshold REAL NOT NULL DEFAULT 5.0,
                added_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_state (
                ticker TEXT PRIMARY KEY,
                last_score REAL,
                last_price REAL,
                last_52w_high REAL,
                last_52w_low REAL,
                last_insider_status TEXT,
                last_short_interest_status TEXT,
                last_13f_status TEXT,
                last_checked_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                direction TEXT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            )
        """)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Watchlist ────────────────────────────────────────────────────────────────

def add_to_watchlist(
    ticker: str,
    score_bull_threshold: float = DEFAULT_SCORE_BULL_THRESHOLD,
    score_bear_threshold: float = DEFAULT_SCORE_BEAR_THRESHOLD,
    price_move_pct_threshold: float = DEFAULT_PRICE_MOVE_PCT_THRESHOLD,
) -> None:
    ticker = ticker.upper().strip()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO watchlist (ticker, score_bull_threshold, score_bear_threshold,
                                       price_move_pct_threshold, added_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(ticker) DO UPDATE SET
                 score_bull_threshold=excluded.score_bull_threshold,
                 score_bear_threshold=excluded.score_bear_threshold,
                 price_move_pct_threshold=excluded.price_move_pct_threshold""",
            (ticker, score_bull_threshold, score_bear_threshold, price_move_pct_threshold, _now_iso()),
        )


def remove_from_watchlist(ticker: str) -> None:
    ticker = ticker.upper().strip()
    with _conn() as conn:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.execute("DELETE FROM alert_state WHERE ticker = ?", (ticker,))


def get_watchlist() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM watchlist ORDER BY ticker").fetchall()
        return [dict(r) for r in rows]


def is_watched(ticker: str) -> bool:
    ticker = ticker.upper().strip()
    with _conn() as conn:
        row = conn.execute("SELECT 1 FROM watchlist WHERE ticker = ?", (ticker,)).fetchone()
        return row is not None


# ── Alert state (last-seen snapshot, used to compute deltas) ────────────────

def get_alert_state(ticker: str) -> dict | None:
    ticker = ticker.upper().strip()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM alert_state WHERE ticker = ?", (ticker,)).fetchone()
        return dict(row) if row else None


def set_alert_state(ticker: str, **fields) -> None:
    ticker = ticker.upper().strip()
    fields["last_checked_at"] = _now_iso()
    cols = ", ".join(fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    updates = ", ".join(f"{k}=excluded.{k}" for k in fields)
    with _conn() as conn:
        conn.execute(
            f"""INSERT INTO alert_state (ticker, {cols}) VALUES (?, {placeholders})
                ON CONFLICT(ticker) DO UPDATE SET {updates}""",
            (ticker, *fields.values()),
        )


# ── Alerts feed ──────────────────────────────────────────────────────────────

def create_alert(ticker: str, alert_type: str, message: str, direction: str | None = None) -> int:
    ticker = ticker.upper().strip()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (ticker, alert_type, direction, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (ticker, alert_type, direction, message, _now_iso()),
        )
        return cur.lastrowid


def get_alerts(unread_only: bool = False, limit: int = 50) -> list[dict]:
    query = "SELECT * FROM alerts"
    if unread_only:
        query += " WHERE is_read = 0"
    query += " ORDER BY created_at DESC LIMIT ?"
    with _conn() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
        return [dict(r) for r in rows]


def count_unread() -> int:
    with _conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM alerts WHERE is_read = 0").fetchone()
        return row["n"] if row else 0


def mark_all_read() -> None:
    with _conn() as conn:
        conn.execute("UPDATE alerts SET is_read = 1 WHERE is_read = 0")


def mark_read(alert_id: int) -> None:
    with _conn() as conn:
        conn.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))


def clear_all_alerts() -> None:
    """Delete every alert record. Used by tests and an explicit 'clear feed' UI action."""
    with _conn() as conn:
        conn.execute("DELETE FROM alerts")
