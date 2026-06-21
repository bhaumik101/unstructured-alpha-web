# utils/alerts_db.py
# Unstructured Alpha — Per-User Watchlist + Alert Storage
#
# Every function here takes a user_id and only ever reads/writes that
# user's own rows -- this is what makes the watchlist and alert feed
# "per account" rather than the single shared instance this module used to
# be (see git history before 2026-06-21 for that version). Built on
# utils/db.py's SQLAlchemy engine, which resolves to Postgres in production
# and SQLite for local dev/tests -- see that module's docstring for why.
#
# DEFAULT_* threshold constants are unchanged from the pre-accounts version.

from datetime import datetime, timezone

from sqlalchemy import select, delete

from utils import db
from utils.db import users, watchlist, alert_state, alerts, upsert_stmt

DEFAULT_SCORE_BULL_THRESHOLD = 65.0
DEFAULT_SCORE_BEAR_THRESHOLD = 35.0
DEFAULT_PRICE_MOVE_PCT_THRESHOLD = 5.0


def init_db() -> None:
    db.init_db()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Watchlist ────────────────────────────────────────────────────────────────

def add_to_watchlist(
    user_id: int,
    ticker: str,
    score_bull_threshold: float = DEFAULT_SCORE_BULL_THRESHOLD,
    score_bear_threshold: float = DEFAULT_SCORE_BEAR_THRESHOLD,
    price_move_pct_threshold: float = DEFAULT_PRICE_MOVE_PCT_THRESHOLD,
) -> None:
    ticker = ticker.upper().strip()
    stmt = upsert_stmt(watchlist, ["user_id", "ticker"]).values(
        user_id=user_id, ticker=ticker,
        score_bull_threshold=score_bull_threshold,
        score_bear_threshold=score_bear_threshold,
        price_move_pct_threshold=price_move_pct_threshold,
        added_at=_now_iso(),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "ticker"],
        set_={
            "score_bull_threshold": score_bull_threshold,
            "score_bear_threshold": score_bear_threshold,
            "price_move_pct_threshold": price_move_pct_threshold,
        },
    )
    with db.engine.begin() as conn:
        conn.execute(stmt)


def remove_from_watchlist(user_id: int, ticker: str) -> None:
    ticker = ticker.upper().strip()
    with db.engine.begin() as conn:
        conn.execute(delete(watchlist).where(watchlist.c.user_id == user_id, watchlist.c.ticker == ticker))
        conn.execute(delete(alert_state).where(alert_state.c.user_id == user_id, alert_state.c.ticker == ticker))


def get_watchlist(user_id: int) -> list[dict]:
    with db.engine.begin() as conn:
        rows = conn.execute(
            select(watchlist).where(watchlist.c.user_id == user_id).order_by(watchlist.c.ticker)
        ).mappings().all()
        return [dict(r) for r in rows]


def is_watched(user_id: int, ticker: str) -> bool:
    ticker = ticker.upper().strip()
    with db.engine.begin() as conn:
        row = conn.execute(
            select(watchlist.c.id).where(watchlist.c.user_id == user_id, watchlist.c.ticker == ticker)
        ).first()
        return row is not None


# ── Alert state (last-seen snapshot, used to compute deltas) ────────────────

def get_alert_state(user_id: int, ticker: str) -> dict | None:
    ticker = ticker.upper().strip()
    with db.engine.begin() as conn:
        row = conn.execute(
            select(alert_state).where(alert_state.c.user_id == user_id, alert_state.c.ticker == ticker)
        ).mappings().first()
        return dict(row) if row else None


def set_alert_state(user_id: int, ticker: str, **fields) -> None:
    ticker = ticker.upper().strip()
    fields["last_checked_at"] = _now_iso()
    stmt = upsert_stmt(alert_state, ["user_id", "ticker"]).values(user_id=user_id, ticker=ticker, **fields)
    stmt = stmt.on_conflict_do_update(index_elements=["user_id", "ticker"], set_=fields)
    with db.engine.begin() as conn:
        conn.execute(stmt)


# ── Alerts feed ──────────────────────────────────────────────────────────────

def create_alert(user_id: int, ticker: str, alert_type: str, message: str, direction: str | None = None) -> int:
    ticker = ticker.upper().strip()
    with db.engine.begin() as conn:
        result = conn.execute(
            alerts.insert().values(
                user_id=user_id, ticker=ticker, alert_type=alert_type,
                direction=direction, message=message, created_at=_now_iso(), is_read=0,
            )
        )
        return result.inserted_primary_key[0]


def get_alerts(user_id: int, unread_only: bool = False, limit: int = 50) -> list[dict]:
    query = select(alerts).where(alerts.c.user_id == user_id)
    if unread_only:
        query = query.where(alerts.c.is_read == 0)
    query = query.order_by(alerts.c.created_at.desc()).limit(limit)
    with db.engine.begin() as conn:
        rows = conn.execute(query).mappings().all()
        return [dict(r) for r in rows]


def count_unread(user_id: int) -> int:
    with db.engine.begin() as conn:
        row = conn.execute(
            select(alerts.c.id).where(alerts.c.user_id == user_id, alerts.c.is_read == 0)
        ).all()
        return len(row)


def mark_all_read(user_id: int) -> None:
    with db.engine.begin() as conn:
        conn.execute(alerts.update().where(alerts.c.user_id == user_id, alerts.c.is_read == 0).values(is_read=1))


def mark_read(user_id: int, alert_id: int) -> None:
    """Scoped to user_id too -- a user must not be able to mark another
    account's alert as read just by guessing an id."""
    with db.engine.begin() as conn:
        conn.execute(alerts.update().where(alerts.c.id == alert_id, alerts.c.user_id == user_id).values(is_read=1))


def clear_all_alerts(user_id: int) -> None:
    with db.engine.begin() as conn:
        conn.execute(delete(alerts).where(alerts.c.user_id == user_id))
