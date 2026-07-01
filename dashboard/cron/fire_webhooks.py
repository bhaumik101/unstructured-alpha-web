#!/usr/bin/env python3
# cron/fire_webhooks.py
# Unstructured Alpha — Proactive Webhook Alert Cron
#
# Runs on a schedule (every hour via Render Cron). For every user with a
# webhook URL configured, it evaluates their full watchlist against the
# latest signal data and fires any threshold crossings to their webhook.
#
# WHY a separate cron instead of only page-load firing:
#   The page-load path (alerts.evaluate_ticker → daemon thread → webhook)
#   is immediate but passive — it only runs when the user opens the Watchlist
#   page. Users who set up a webhook precisely BECAUSE they want push alerts
#   without having to visit the site need this proactive sweep. The cron
#   guarantees delivery within ~60 minutes of a real threshold crossing,
#   independent of site traffic.
#
# DUPLICATE PROTECTION: The alert evaluation engine (utils/alerts.py) tracks
# last-seen state per user/ticker in the alert_state table and only fires
# when a value crosses a threshold (not when it merely stays on one side).
# Running this hourly is therefore safe — the same crossing can only fire
# once, regardless of how many times this cron runs while the condition holds.
#
# IMPORTANT: This script runs OUTSIDE Streamlit. Do NOT import anything that
# calls st.* at module level. Use environment variables, not st.secrets.
#
# Run manually (from the dashboard/ directory):
#   python -m cron.fire_webhooks
# or:
#   python cron/fire_webhooks.py

import sys
from pathlib import Path

# Ensure dashboard/ is on sys.path so `utils.*` imports resolve correctly
# whether this runs as a module (python -m cron.fire_webhooks) or a direct
# script (python cron/fire_webhooks.py).
_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from utils.db import init_db
from utils.webhook import get_all_webhook_users, fire_alerts_for_user
from utils.alerts import evaluate_watchlist


def main() -> None:
    init_db()

    webhook_users = get_all_webhook_users()
    print(f"[fire_webhooks] {len(webhook_users)} user(s) with webhooks configured")

    total_alerts = 0
    total_fired = 0

    for u in webhook_users:
        user_id = u["id"]
        email = u["email"]
        try:
            new_alerts = evaluate_watchlist(user_id)
            if not new_alerts:
                print(f"[fire_webhooks] user={user_id} ({email}): no new alerts")
                continue

            # fire_alerts_for_user() re-reads the webhook_url from DB — this
            # is intentional: the user might have updated it since the loop
            # started, and evaluate_watchlist() can take several seconds per
            # user. We want the freshest URL, not a snapshot from loop start.
            fired = fire_alerts_for_user(user_id, new_alerts)
            total_alerts += len(new_alerts)
            total_fired += fired
            print(
                f"[fire_webhooks] user={user_id} ({email}): "
                f"{len(new_alerts)} alert(s), {fired} delivered"
            )
        except Exception as exc:
            # One user's error must not abort the sweep for everyone else.
            print(f"[fire_webhooks] user={user_id} ({email}): ERROR — {exc}")

    print(
        f"[fire_webhooks] Done. "
        f"{total_alerts} total alert(s) across {len(webhook_users)} user(s), "
        f"{total_fired} successfully delivered."
    )


if __name__ == "__main__":
    main()
