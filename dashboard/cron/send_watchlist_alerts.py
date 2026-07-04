#!/usr/bin/env python3
# cron/send_watchlist_alerts.py
# Unstructured Alpha — Watchlist Threshold-Crossing Email Cron
#
# Runs every hour via Render Cron (same schedule as fire_webhooks.py).
# For every verified user with at least one watchlist entry, it evaluates
# their watchlist and emails them about any new threshold crossings.
#
# WHY this exists separately from fire_webhooks.py:
#   fire_webhooks.py only covers users who have a Discord/Slack webhook URL
#   configured. Most users have no webhook configured and rely on the in-app
#   alert feed — but the in-app feed is passive (only updates on page load).
#   This cron gives every watchlist user push-style email delivery regardless
#   of whether they've set up a webhook, so threshold crossings reach them
#   within ~60 minutes of occurring even if they never visit the site.
#
# DUPLICATE PROTECTION: The alert evaluation engine (utils/alerts.py) tracks
# the last-seen state per user/ticker in the alert_state table and only creates
# a new alert row when a value actually *crosses* a threshold (not when it
# merely stays on one side of it). Running this hourly is therefore safe —
# the same crossing can only fire once per user, regardless of how many times
# this cron runs while the condition holds.
#
# IMPORTANT: This script runs OUTSIDE Streamlit. Do NOT import anything that
# calls st.* at module level. Configuration is read from environment variables
# (DATABASE_URL, RESEND_API_KEY, RESEND_FROM_EMAIL, FRED_API_KEY, EIA_API_KEY),
# which Render injects identically for the web service and all cron jobs.
#
# Run manually (from the dashboard/ directory):
#   python -m cron.send_watchlist_alerts
# or:
#   python cron/send_watchlist_alerts.py

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure dashboard/ is on sys.path so `utils.*` imports resolve correctly
# whether this runs as a module or a direct script.
_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from utils.db import init_db
from utils.alerts_db import get_all_watchlist_users
from utils.alerts import evaluate_watchlist
from utils.email import send_watchlist_alert_email, EmailSendError


def main() -> None:
    print(
        f"[watchlist-alerts] starting at {datetime.now(timezone.utc).isoformat()}",
        flush=True,
    )

    init_db()

    watchlist_users = get_all_watchlist_users()
    print(
        f"[watchlist-alerts] {len(watchlist_users)} user(s) with watchlist entries",
        flush=True,
    )

    if not watchlist_users:
        print("[watchlist-alerts] no watchlist users — nothing to do. done.", flush=True)
        return

    total_alerts = 0
    total_sent = 0
    total_failed = 0

    for u in watchlist_users:
        user_id = u["id"]
        email = u["email"]
        try:
            new_alerts = evaluate_watchlist(user_id)
            if not new_alerts:
                # No threshold crossings for this user — nothing to email.
                continue

            try:
                send_watchlist_alert_email(email, new_alerts)
                total_sent += 1
                total_alerts += len(new_alerts)
                print(
                    f"[watchlist-alerts] user={user_id} ({email}): "
                    f"{len(new_alerts)} alert(s) emailed",
                    flush=True,
                )
            except EmailSendError as exc:
                total_failed += 1
                print(
                    f"[watchlist-alerts] user={user_id} ({email}): "
                    f"email FAILED — {exc}",
                    flush=True,
                )

        except Exception as exc:
            # One user's evaluation error must not abort the sweep.
            print(
                f"[watchlist-alerts] user={user_id} ({email}): "
                f"evaluate_watchlist ERROR — {exc}",
                flush=True,
            )

    print(
        f"[watchlist-alerts] done. "
        f"{total_alerts} alert(s) across {total_sent} email(s) sent, "
        f"{total_failed} failed.",
        flush=True,
    )


if __name__ == "__main__":
    main()
