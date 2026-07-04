# cron/send_velocity_alerts.py
# Unstructured Alpha — Score Velocity Alert Cron
#
# Runs daily (16:00 UTC = noon ET). For every user's watchlist, detects
# tickers whose Confluence Score is moving at an unusually high rate and
# emails a single velocity-alert digest.
#
# What counts as "unusual":
#   - Velocity percentile ≥ VELOCITY_THRESHOLD_PERCENTILE (default 90)
#   - At least MIN_HISTORY_WINDOWS historical windows for a meaningful baseline
#
# De-duplication:
#   - Stores last_velocity_alert_at in alert_state per (user, ticker)
#   - Will not re-alert for the same ticker within MIN_DAYS_BETWEEN_ALERTS days
#   - This prevents daily spam when a score is trending steadily for a week
#
# First-run behaviour:
#   - Tickers with no snapshot history return None from get_score_velocity_stats
#     and are simply skipped — no spurious alert on first run.
#
# Design: velocity is computed purely from score_snapshots, which the
# send_digest cron already populates for ALL ~193 tickers daily. So by the
# time this cron runs, essentially every ticker already has enough history
# after the first few weeks of operation.

import sys
from pathlib import Path

# Allow imports from the dashboard package root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from utils.db import (
    init_db,
    engine,
    alert_state,
    score_snapshots,
    upsert_stmt,
)
from utils.alerts_db import get_all_watchlist_users, get_watchlist, get_alert_state
from utils.score_history import get_score_velocity_stats
from utils.email import send_velocity_alert_email
from utils.config import TICKERS

# ── Configuration ─────────────────────────────────────────────────────────────

VELOCITY_THRESHOLD_PERCENTILE = 90.0   # top 10% of absolute historical velocity
MIN_HISTORY_WINDOWS            = 6     # need at least 6 prior windows for a valid baseline
MIN_DAYS_BETWEEN_ALERTS        = 6     # suppress re-alert within this many days


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_last_velocity_alert_at(user_id: int, ticker: str) -> str | None:
    """Return the ISO timestamp of the last velocity alert for (user, ticker), or None."""
    state = get_alert_state(user_id, ticker)
    if state is None:
        return None
    return state.get("last_velocity_alert_at")


def _set_last_velocity_alert_at(user_id: int, ticker: str, ts: str) -> None:
    """Upsert last_velocity_alert_at for (user, ticker)."""
    stmt = upsert_stmt(alert_state, ["user_id", "ticker"]).values(
        user_id=user_id,
        ticker=ticker,
        last_velocity_alert_at=ts,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "ticker"],
        set_={"last_velocity_alert_at": ts},
    )
    with engine.begin() as conn:
        conn.execute(stmt)


def _get_latest_snapshot(ticker: str) -> dict | None:
    """Return the most recent score_snapshots row for ticker, or None."""
    try:
        with engine.begin() as conn:
            row = conn.execute(
                select(score_snapshots)
                .where(score_snapshots.c.ticker == ticker)
                .order_by(score_snapshots.c.snapshot_date.desc())
                .limit(1)
            ).mappings().first()
        return dict(row) if row else None
    except Exception:
        return None


def _ticker_name(ticker: str) -> str:
    """Best-effort full company name from config, fallback to ticker."""
    return TICKERS.get(ticker, {}).get("name", ticker)


# ── Per-user check ─────────────────────────────────────────────────────────────

def check_user(user_id: int) -> list[dict]:
    """
    For each ticker in the user's watchlist:
      1. Compute score velocity stats (from score_snapshots history)
      2. If velocity is in the top VELOCITY_THRESHOLD_PERCENTILE of history,
         and the user hasn't been alerted for this ticker recently,
         add it to the alert list and update the dedup timestamp.

    Returns a list of alert dicts ready for send_velocity_alert_email().
    """
    watchlist = get_watchlist(user_id)
    if not watchlist:
        return []

    now_utc = datetime.now(timezone.utc)
    alerts: list[dict] = []

    for row in watchlist:
        ticker = row["ticker"]
        try:
            stats = get_score_velocity_stats(ticker)
            if stats is None:
                continue  # insufficient history

            if stats["percentile"] < VELOCITY_THRESHOLD_PERCENTILE:
                continue  # not unusual enough

            if stats["n_windows"] < MIN_HISTORY_WINDOWS:
                continue  # not enough baseline to trust the percentile

            # De-duplication check
            last_at_str = _get_last_velocity_alert_at(user_id, ticker)
            if last_at_str:
                try:
                    last_at = datetime.fromisoformat(last_at_str)
                    if (now_utc - last_at).days < MIN_DAYS_BETWEEN_ALERTS:
                        print(
                            f"  [{ticker}] suppressed — alerted {(now_utc-last_at).days}d ago",
                            flush=True,
                        )
                        continue
                except ValueError:
                    pass  # malformed timestamp — treat as never alerted

            # Get latest score for the email body
            snap = _get_latest_snapshot(ticker)
            current_score = float(snap["score"]) if snap and snap.get("score") is not None else 50.0
            case          = snap.get("case", "NEUTRAL") if snap else "NEUTRAL"

            alerts.append({
                "ticker":        ticker,
                "name":          _ticker_name(ticker),
                "velocity":      stats["velocity"],
                "percentile":    stats["percentile"],
                "direction":     stats["direction"],
                "current_score": current_score,
                "case":          case,
            })

            # Mark alerted so we don't spam this user for the same ticker
            _set_last_velocity_alert_at(user_id, ticker, now_utc.isoformat())

        except Exception as exc:
            print(f"  [{ticker}] check failed (non-blocking): {exc}", flush=True)

    return alerts


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    init_db()
    print(f"[velocity-alerts] Starting — {datetime.now(timezone.utc).isoformat()}", flush=True)

    users = get_all_watchlist_users()
    print(f"[velocity-alerts] {len(users)} users with watchlists", flush=True)

    sent = 0
    for u in users:
        user_id = u["id"]
        email   = u["email"]
        try:
            alerts = check_user(user_id)
            if not alerts:
                continue
            print(
                f"[velocity-alerts] user={user_id} → {len(alerts)} alert(s): "
                + ", ".join(
                    f"{a['ticker']} ({a['velocity']:+.1f} pts/day, top {100-a['percentile']:.0f}%)"
                    for a in alerts
                ),
                flush=True,
            )
            send_velocity_alert_email(email, alerts)
            sent += 1
        except Exception as exc:
            print(f"[velocity-alerts] user={user_id} FAILED: {exc}", flush=True)

    print(
        f"[velocity-alerts] Done — sent to {sent}/{len(users)} users",
        flush=True,
    )


if __name__ == "__main__":
    main()
