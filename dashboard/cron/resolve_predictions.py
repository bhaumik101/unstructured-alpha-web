#!/usr/bin/env python3
# cron/resolve_predictions.py
# Unstructured Alpha — Nightly Prediction Auto-Resolution Cron
#
# Designed to run as a Render Cron Job at 02:00 UTC daily.
# Finds pending predictions whose forward windows (4w/8w/12w) have expired,
# fetches realized prices via yfinance, and marks them correct/incorrect.
#
# Run manually (from the dashboard/ directory):
#   python -m cron.resolve_predictions
# or:
#   python cron/resolve_predictions.py

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the dashboard/ directory is on sys.path so `utils.*` imports work
_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from utils.db import init_db
from utils.prediction_log import resolve_pending


def main() -> None:
    print(f"[resolve] starting at {datetime.now(timezone.utc).isoformat()}", flush=True)

    init_db()

    # Resolve up to 200 predictions per run — generous cap for a nightly cron.
    # In steady state this processes only a handful of rows (one convergence
    # event per ticker per day at most), so the yfinance batch fetch stays fast.
    resolved = resolve_pending(max_resolve=200)

    print(f"[resolve] done — resolved={resolved}", flush=True)


if __name__ == "__main__":
    main()
