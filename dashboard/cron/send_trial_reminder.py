#!/usr/bin/env python3
# cron/send_trial_reminder.py
# Unstructured Alpha — Day-6 Trial-End Reminder Cron
#
# Designed to run as a Render Cron Job at 10:00 ET daily (15:00 UTC).
# Finds every Pro user whose trial ends within the next 20–32 hours
# (i.e. day 6 of a 7-day trial) and sends them a "trial ends tomorrow" email.
#
# Why 20–32 hours rather than exactly 24? Cron fires at a fixed clock time,
# but trial_end_at is spread across the day depending on when each user
# signed up. A 12-hour window around "24h from now" captures everyone whose
# trial ends "tomorrow" regardless of signup time, without double-firing.
#
# Run manually (from the dashboard/ directory):
#   python -m cron.send_trial_reminder
# or:
#   python cron/send_trial_reminder.py

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from sqlalchemy import select

from utils.db import engine, users, init_db


def _get_trial_ending_users() -> list[tuple[str, str]]:
    """
    Return [(email, trial_end_at_iso)] for Pro users whose trial ends
    within the next 20–32 hours (day-6 window).
    """
    now = datetime.now(timezone.utc)
    window_start = (now + timedelta(hours=20)).isoformat()
    window_end   = (now + timedelta(hours=32)).isoformat()

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(users.c.email, users.c.trial_end_at)
                .where(users.c.subscription_tier == "pro")
                .where(users.c.trial_end_at.isnot(None))
                .where(users.c.trial_end_at >= window_start)
                .where(users.c.trial_end_at <= window_end)
                .where(users.c.email_verified == True)   # noqa: E712
            ).fetchall()
        return [(row[0], row[1]) for row in rows]
    except Exception as exc:
        print(f"[trial-reminder] DB query failed: {exc}", flush=True)
        return []


def main() -> None:
    print(f"[trial-reminder] starting at {datetime.now(timezone.utc).isoformat()}", flush=True)
    init_db()

    candidates = _get_trial_ending_users()
    print(f"[trial-reminder] users in day-6 window: {len(candidates)}", flush=True)

    if not candidates:
        print("[trial-reminder] no users to remind. done.", flush=True)
        return

    from utils.email import send_trial_reminder_email, EmailSendError

    sent, failed = 0, 0
    for email_addr, trial_end_iso in candidates:
        try:
            # Format the trial_end_at datetime for the email copy.
            trial_dt = datetime.fromisoformat(trial_end_iso.replace("Z", "+00:00"))
            trial_end_display = trial_dt.strftime("%-d %B %Y")   # e.g. "1 July 2026"
        except Exception:
            trial_end_display = "tomorrow"

        try:
            send_trial_reminder_email(
                to_email=email_addr,
                trial_end_display=trial_end_display,
            )
            sent += 1
            print(f"[trial-reminder] sent to {email_addr!r} (trial ends {trial_end_display})", flush=True)
        except EmailSendError as exc:
            failed += 1
            print(f"[trial-reminder] FAILED to {email_addr!r}: {exc}", flush=True)

    print(f"[trial-reminder] done — sent={sent} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
