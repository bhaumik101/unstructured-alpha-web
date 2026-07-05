#!/usr/bin/env python3
# cron/send_reengagement.py
# Unstructured Alpha — Re-engagement Email Cron
#
# Runs daily at 17:00 UTC (1:00 PM ET) via Render Cron.
# Finds verified users who haven't logged in for >= INACTIVE_DAYS and
# sends them a "here's what you missed" email showing their watchlist
# score movers and any macro signal flips since they were last active.
#
# QUALIFYING CRITERIA (all must be true):
#   - email_verified = True
#   - last_login_at <= now - INACTIVE_DAYS (or NULL — never logged in after signup)
#   - Has at least 1 watchlist ticker
#   - last_reengagement_at IS NULL  OR  last_reengagement_at <= now - RESEND_DAYS
#     (prevents re-sending the same user more often than once per week)
#
# WHAT'S IN THE EMAIL:
#   - Top movers on their watchlist since they were last active
#   - Macro signal flips since they were last active
#   - Current overall regime (Bullish / Bearish / Mixed)
#   - Single CTA: "Check Your Watchlist →"
#
# Tone is friendly, not pushy. It's showing value, not scolding.
#
# Run manually from dashboard/:
#   python -m cron.send_reengagement

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_here = Path(__file__).resolve().parent.parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from sqlalchemy import select, text
from utils.db import init_db, engine, users, watchlist, score_snapshots, signal_snapshots
from utils.email import send_reengagement_email, EmailSendError

# ── Config ───────────────────────────────────────────────────────────────────

INACTIVE_DAYS  = 5    # users inactive >= this many days qualify
RESEND_DAYS    = 7    # don't re-send to the same user within this many days
MIN_SCORE_DELTA = 3.0  # only report a mover if |delta| >= this


# ── Recipient lookup ──────────────────────────────────────────────────────────

def _get_inactive_recipients() -> list[tuple[str, int, str | None]]:
    """
    Return [(email, user_id, last_login_at_iso)] for qualifying users.
    Qualifying = verified, not recently re-engaged, has a watchlist entry.
    """
    now       = datetime.now(timezone.utc)
    cutoff    = (now - timedelta(days=INACTIVE_DAYS)).isoformat()
    resend_ok = (now - timedelta(days=RESEND_DAYS)).isoformat()

    try:
        with engine.begin() as conn:
            # Users who are verified and last logged in before the cutoff
            # (or have never logged in at all — last_login_at IS NULL)
            rows = conn.execute(
                select(users.c.id, users.c.email, users.c.last_login_at)
                .where(users.c.email_verified == True)           # noqa: E712
                .where(
                    (users.c.last_login_at == None) |            # noqa: E711
                    (users.c.last_login_at <= cutoff)
                )
                .where(
                    (users.c.last_reengagement_at == None) |     # noqa: E711
                    (users.c.last_reengagement_at <= resend_ok)
                )
            ).fetchall()
    except Exception as exc:
        print(f"[reengagement] DB query failed: {exc}", flush=True)
        return []

    # Filter to users who actually have watchlist entries
    result = []
    for row in rows:
        user_id, email, last_login = row[0], row[1], row[2]
        try:
            with engine.begin() as conn:
                count = conn.execute(
                    select(watchlist.c.id)
                    .where(watchlist.c.user_id == user_id)
                    .limit(1)
                ).fetchone()
            if count is None:
                continue  # no watchlist — nothing to show
        except Exception:
            continue
        result.append((email, user_id, last_login))

    return result


# ── Watchlist movers ──────────────────────────────────────────────────────────

def _get_watchlist_tickers(user_id: int) -> list[str]:
    try:
        with engine.begin() as conn:
            rows = conn.execute(
                select(watchlist.c.ticker)
                .where(watchlist.c.user_id == user_id)
                .order_by(watchlist.c.added_at.desc())
            ).fetchall()
        return [r[0].upper() for r in rows]
    except Exception:
        return []


def _compute_movers(tickers: list[str], since_iso: str | None) -> list[dict]:
    """
    Compute score deltas for each ticker since `since_iso` (ISO datetime).
    Falls back to 7-day lookback if since_iso is None.
    Returns up to 4 movers sorted by |delta|.
    """
    if not tickers:
        return []

    # Lookback: from last login, or 7 days if never logged in
    if since_iso:
        # Take just the date part for the snapshot query
        cutoff_date = since_iso[:10]
    else:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        with engine.begin() as conn:
            rows = conn.execute(
                select(
                    score_snapshots.c.ticker,
                    score_snapshots.c.score,
                    score_snapshots.c.snapshot_date,
                )
                .where(score_snapshots.c.ticker.in_(tickers))
                .where(score_snapshots.c.snapshot_date >= cutoff_date)
                .order_by(score_snapshots.c.ticker, score_snapshots.c.snapshot_date)
            ).fetchall()
    except Exception:
        return []

    from collections import defaultdict
    by_ticker: dict[str, list] = defaultdict(list)
    for r in rows:
        if r[1] is not None:
            by_ticker[r[0]].append((r[2], float(r[1])))

    # Get ticker names
    name_map: dict[str, str] = {}
    try:
        from utils.signals_cache import get_all_signal_scores
        from utils.top_tickers import get_top_tickers
        result = get_top_tickers(signal_scores_hash=0)
        for row in result.get("all", []):
            name_map[row["ticker"]] = row.get("name", row["ticker"])
    except Exception:
        pass

    movers = []
    for ticker, entries in by_ticker.items():
        entries.sort()
        if len(entries) < 2:
            continue
        old_score = entries[0][1]
        cur_score = entries[-1][1]
        delta     = round(cur_score - old_score, 1)
        if abs(delta) < MIN_SCORE_DELTA:
            continue
        case = "BULL" if cur_score >= 65 else ("BEAR" if cur_score <= 35 else "NEUT")
        movers.append({
            "ticker": ticker,
            "name":   name_map.get(ticker, ticker),
            "score":  round(cur_score, 1),
            "delta":  delta,
            "case":   case,
        })

    movers.sort(key=lambda x: -abs(x["delta"]))
    return movers[:4]


# ── Signal flips ──────────────────────────────────────────────────────────────

def _get_signal_flips(since_iso: str | None, max_days: int = 14) -> list[dict]:
    """
    Signal flips since `since_iso`, capped at `max_days` lookback.
    Returns list of {name, from_status, to_status}.
    """
    if since_iso:
        cutoff_date = since_iso[:10]
        # Don't look back more than max_days even if user was gone longer
        floor_date = (datetime.now(timezone.utc) - timedelta(days=max_days)).strftime("%Y-%m-%d")
        cutoff_date = max(cutoff_date, floor_date)
    else:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        from utils.score_history import get_signal_diff
        # We can't pass an exact date to get_signal_diff easily, but we can
        # pass days_back computed from the cutoff
        days_back = (datetime.now(timezone.utc).date() -
                     datetime.fromisoformat(cutoff_date).date()).days
        days_back = max(1, min(days_back, max_days))
        diff = get_signal_diff(days_back=days_back)
        flips = []
        for f in diff.get("flipped_bullish", []):
            flips.append({
                "name":        f["name"],
                "from_status": f.get("from_status", "bearish"),
                "to_status":   "bullish",
            })
        for f in diff.get("flipped_bearish", []):
            flips.append({
                "name":        f["name"],
                "from_status": f.get("from_status", "bullish"),
                "to_status":   "bearish",
            })
        return flips[:4]
    except Exception as exc:
        print(f"[reengagement] signal flips failed: {exc}", flush=True)
        return []


# ── Regime ────────────────────────────────────────────────────────────────────

def _get_regime_label() -> str:
    try:
        from utils.signals_cache import get_all_signal_scores
        scores = get_all_signal_scores()
        bull = sum(1 for v in scores.values() if v.get("status") == "bullish")
        bear = sum(1 for v in scores.values() if v.get("status") == "bearish")
        total = max(bull + bear + sum(1 for v in scores.values() if v.get("status") == "neutral"), 1)
        if bull / total >= 0.5:
            return "Bullish"
        if bear / total >= 0.5:
            return "Bearish"
        return "Mixed"
    except Exception:
        return "Mixed"


# ── Mark sent ─────────────────────────────────────────────────────────────────

def _mark_reengaged(user_id: int) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with engine.begin() as conn:
            conn.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(last_reengagement_at=now_iso)
            )
    except Exception as exc:
        print(f"[reengagement] failed to mark user {user_id}: {exc}", flush=True)


# ── Days away ─────────────────────────────────────────────────────────────────

def _days_away(last_login_iso: str | None) -> int:
    if last_login_iso is None:
        return INACTIVE_DAYS  # unknown — just say the minimum
    try:
        then = datetime.fromisoformat(last_login_iso)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return max(INACTIVE_DAYS, (datetime.now(timezone.utc) - then).days)
    except Exception:
        return INACTIVE_DAYS


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[reengagement] starting — {datetime.now(timezone.utc).isoformat()}", flush=True)

    init_db()

    recipients = _get_inactive_recipients()
    print(f"[reengagement] qualifying inactive users: {len(recipients)}", flush=True)
    if not recipients:
        print("[reengagement] nobody qualifies — done.", flush=True)
        return

    # Compute regime once — same for all users
    regime_label = _get_regime_label()
    print(f"[reengagement] current regime: {regime_label}", flush=True)

    sent, failed, skipped = 0, 0, 0
    for email_addr, user_id, last_login_iso in recipients:
        try:
            tickers = _get_watchlist_tickers(user_id)
            if not tickers:
                skipped += 1
                continue

            movers = _compute_movers(tickers, last_login_iso)
            flips  = _get_signal_flips(last_login_iso)
            days   = _days_away(last_login_iso)

            # Only send if there's something substantive to show
            if not movers and not flips:
                print(
                    f"[reengagement] user {user_id} ({email_addr!r}): "
                    f"no movers or flips — skipping",
                    flush=True,
                )
                skipped += 1
                continue

            print(
                f"[reengagement] user {user_id}: {len(tickers)} tickers, "
                f"{len(movers)} movers, {len(flips)} flips, {days}d away",
                flush=True,
            )

            send_reengagement_email(
                email_addr,
                days_away=days,
                movers=movers or None,
                signal_flips=flips or None,
                regime_label=regime_label,
            )
            _mark_reengaged(user_id)
            sent += 1
            print(f"[reengagement] sent to {email_addr!r}", flush=True)

        except EmailSendError as exc:
            failed += 1
            print(f"[reengagement] SEND FAILED to {email_addr!r}: {exc}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"[reengagement] unexpected error for {email_addr!r}: {exc}", flush=True)

    print(
        f"[reengagement] done — sent={sent} skipped={skipped} failed={failed}",
        flush=True,
    )


if __name__ == "__main__":
    main()
