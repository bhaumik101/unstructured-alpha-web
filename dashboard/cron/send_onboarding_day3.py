#!/usr/bin/env python3
# cron/send_onboarding_day3.py
# Unstructured Alpha — Day-3 Onboarding Email Cron
#
# Runs daily at 14:00 UTC (10:00 AM ET).
# Targets email-verified users who signed up 3–4 days ago and have NOT yet
# received this specific email (guarded by a new column `day3_email_sent`
# on the users table — added as TEXT "true"/"" via the generic migration path).
#
# Email content: "3 features you probably haven't tried yet"
# - Best Ideas page
# - Ticker Deep Dive AI explanation
# - Watchlist Score Report Card
# + soft Pro upgrade CTA for free users
#
# Run manually from dashboard/:
#   python -m cron.send_onboarding_day3

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_here = Path(__file__).resolve().parent.parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from sqlalchemy import select, update
from utils.db import init_db, engine, users
from utils.email import send_day3_onboarding_email, EmailSendError
from utils.billing import get_user_tier

# ── Config ────────────────────────────────────────────────────────────────────
DAY3_MIN = 3   # send after this many days since signup
DAY3_MAX = 4   # but not after this many (avoid late stale sends)


# ── Recipient lookup ──────────────────────────────────────────────────────────

def _get_recipients() -> list[dict]:
    """
    Return email-verified users who signed up 3–4 days ago and haven't
    received the day-3 email yet.
    """
    now       = datetime.now(timezone.utc)
    min_ago   = (now - timedelta(days=DAY3_MAX)).isoformat()
    max_ago   = (now - timedelta(days=DAY3_MIN)).isoformat()

    try:
        with engine.begin() as conn:
            rows = conn.execute(
                select(
                    users.c.id,
                    users.c.email,
                    users.c.subscription_tier,
                    users.c.created_at,
                )
                .where(users.c.email_verified == True)          # noqa: E712
                .where(users.c.created_at >= min_ago)
                .where(users.c.created_at <= max_ago)
                .where(
                    (users.c.day3_email_sent == None) |         # noqa: E711
                    (users.c.day3_email_sent == "")
                )
            ).fetchall()
        return [
            {"id": r[0], "email": r[1], "tier": r[2], "created_at": r[3]}
            for r in rows
        ]
    except Exception as exc:
        print(f"[day3] DB query failed: {exc}", flush=True)
        return []


def _mark_sent(user_id: int) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(day3_email_sent="true")
            )
    except Exception as exc:
        print(f"[day3] mark_sent failed for user {user_id}: {exc}", flush=True)


# ── Machine's top bull ticker (for personalisation) ───────────────────────────

def _get_top_bull() -> tuple[str | None, float | None, str]:
    try:
        from utils.top_tickers import get_top_tickers
        result = get_top_tickers(signal_scores_hash=0)
        bull = result.get("bullish", [])
        if bull:
            best = bull[0]
            return best.get("ticker"), float(best.get("score", 0)), "Bullish"
        return None, None, "Mixed"
    except Exception:
        return None, None, "Mixed"


def _get_regime() -> str:
    try:
        from utils.signals_cache import get_all_signal_scores
        scores = get_all_signal_scores()
        bull = sum(1 for v in scores.values() if v.get("status") == "bullish")
        bear = sum(1 for v in scores.values() if v.get("status") == "bearish")
        total = max(len(scores), 1)
        if bull / total >= 0.5:
            return "Bullish"
        if bear / total >= 0.5:
            return "Bearish"
        return "Mixed"
    except Exception:
        return "Mixed"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[day3] starting — {datetime.now(timezone.utc).isoformat()}", flush=True)

    init_db()

    recipients = _get_recipients()
    print(f"[day3] qualifying recipients: {len(recipients)}", flush=True)
    if not recipients:
        print("[day3] nobody qualifies — done.", flush=True)
        return

    # Compute personalisation once
    top_ticker, top_score, regime = _get_top_bull()
    print(f"[day3] top bull: {top_ticker} ({top_score}), regime: {regime}", flush=True)

    sent = failed = 0
    for rec in recipients:
        try:
            is_pro = rec["tier"] == "pro"
            send_day3_onboarding_email(
                rec["email"],
                is_pro=is_pro,
                top_bull_ticker=top_ticker,
                top_bull_score=top_score,
                regime_label=regime,
            )
            _mark_sent(rec["id"])
            sent += 1
            print(f"[day3] sent to {rec['email']!r}", flush=True)
        except EmailSendError as exc:
            failed += 1
            print(f"[day3] SEND FAILED to {rec['email']!r}: {exc}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"[day3] unexpected error for {rec['email']!r}: {exc}", flush=True)

    print(f"[day3] done — sent={sent} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
