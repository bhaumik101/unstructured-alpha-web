"""
utils/onboarding.py — First-time user detection and 3-step onboarding state.

A user is "new" if their account was created within the last 7 days.
Onboarding has three steps that must be completed in any order:
  1. view_signals     — visit the Signal Dashboard
  2. search_ticker    — look up any ticker in Ticker Deep Dive
  3. add_to_watchlist — add a ticker to the Watchlist

Step completion is persisted in the onboarding_progress table so the checklist
state survives page reloads and new browser sessions. All DB operations are
wrapped in try/except — this module never raises.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# The three onboarding steps. Order matters for display only.
STEPS: list[dict] = [
    {
        "id":    "view_signals",
        "label": "Explore the Signal Dashboard",
        "desc":  "See which of 43 macro signals are bullish, bearish, or neutral right now.",
        "page":  "pages/1_Signal_Dashboard.py",
        "icon":  "📊",
    },
    {
        "id":    "search_ticker",
        "label": "Look up a stock you follow",
        "desc":  "Enter any ticker to get its Confluence Score and signal breakdown.",
        "page":  "pages/3_Ticker_Deep_Dive.py",
        "icon":  "🔍",
    },
    {
        "id":    "add_to_watchlist",
        "label": "Add a ticker to your Watchlist",
        "desc":  "Track score changes and get alerts on the stocks you care about.",
        "page":  "pages/10_Watchlist.py",
        "icon":  "🔔",
    },
]

_NEW_USER_DAYS = 7


def get_onboarding_state(user_id: int, created_at=None) -> dict:
    """
    Return the current onboarding state for a user.

    Returns:
        is_new_user (bool)  — account < 7 days old
        show_banner (bool)  — new user AND at least one step still pending
        completed   (set)   — set of completed step IDs
        all_done    (bool)  — all three steps completed
        steps       (list)  — STEPS with 'done' bool injected per step
        n_done      (int)   — number of completed steps
    """
    completed = _get_completed(user_id)
    is_new    = _is_new_user(created_at)
    all_done  = {s["id"] for s in STEPS} <= completed

    return {
        "is_new_user": is_new,
        "show_banner": is_new and not all_done,
        "completed":   completed,
        "all_done":    all_done,
        "n_done":      len(completed),
        "steps":       [{**s, "done": s["id"] in completed} for s in STEPS],
    }


def mark_step(user_id: int, step_id: str) -> None:
    """
    Mark an onboarding step as completed. Idempotent — safe to call on every page load.
    Silently ignores invalid step IDs and DB errors.
    """
    valid_ids = {s["id"] for s in STEPS}
    if step_id not in valid_ids:
        return
    try:
        from utils.db import engine, IS_SQLITE
        from sqlalchemy import text

        ts = datetime.now(timezone.utc).isoformat()
        if IS_SQLITE:
            sql = """
                INSERT OR IGNORE INTO onboarding_progress (user_id, step_id, completed_at)
                VALUES (:uid, :step, :ts)
            """
        else:
            sql = """
                INSERT INTO onboarding_progress (user_id, step_id, completed_at)
                VALUES (:uid, :step, :ts)
                ON CONFLICT (user_id, step_id) DO NOTHING
            """
        with engine.connect() as conn:
            conn.execute(text(sql), {"uid": user_id, "step": step_id, "ts": ts})
            conn.commit()
    except Exception:
        pass


# ── Private helpers ────────────────────────────────────────────────────────────

def _is_new_user(created_at) -> bool:
    """Return True if the account was created within _NEW_USER_DAYS days."""
    if created_at is None:
        return False
    try:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created_at) < timedelta(days=_NEW_USER_DAYS)
    except Exception:
        return False


def _get_completed(user_id: int) -> set:
    """Return the set of step IDs already completed for this user."""
    try:
        from utils.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT step_id FROM onboarding_progress WHERE user_id = :uid"),
                {"uid": user_id},
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()
