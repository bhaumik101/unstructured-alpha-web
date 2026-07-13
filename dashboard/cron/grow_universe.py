#!/usr/bin/env python3
# cron/grow_universe.py
# Unstructured Alpha — Daily Universe Growth Cron
#
# Designed to run as a Render Cron Job once a day. Two jobs:
#   1. Seed the dynamic universe with big-cap names across the industries we
#      cover, so the tracked universe keeps growing and common tickers are
#      already present for the next customer.
#   2. Pre-warm each seeded ticker's Confluence Score (record a snapshot), so
#      its Ticker Deep Dive and screener rows load instantly instead of
#      computing cold on first view.
#
# Everything is best-effort and isolated per ticker — one bad symbol or a
# transient yfinance error never aborts the run.
#
# Run manually (from the dashboard/ directory):
#   python -m cron.grow_universe

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from utils.db import init_db
from utils.universe import add_to_universe, universe_size

# Big, liquid names grouped by the industries the platform's signals cover.
# Deliberately household names — the point is fast, familiar data for customers.
BIG_NAMES = {
    "Technology / AI Infrastructure": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD", "TSM",
        "ORCL", "CRM", "ADBE", "PLTR", "SMCI", "MU", "ARM", "DELL", "ANET",
    ],
    "Financials & Credit": [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "SCHW", "BLK", "AXP", "V", "MA",
    ],
    "Energy & Oil": [
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY", "WMB", "KMI",
    ],
    "Power & Nuclear / Utilities": [
        "CEG", "VST", "NEE", "DUK", "SO", "D", "AEP", "ETN", "GEV", "SMR", "CCJ",
    ],
    "Healthcare & Biotech": [
        "UNH", "JNJ", "LLY", "MRK", "ABBV", "PFE", "TMO", "ISRG", "VRTX", "AMGN",
    ],
    "Industrials": [
        "CAT", "DE", "HON", "GE", "BA", "UNP", "UPS", "LMT", "RTX", "PWR", "URI",
    ],
    "Consumer": [
        "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "PG", "KO", "PEP",
    ],
    "Materials / Broad Macro": [
        "FCX", "NEM", "LIN", "SHW", "SPY", "QQQ", "IWM", "DIA",
    ],
}


def main() -> None:
    print(f"[grow_universe] starting at {datetime.now(timezone.utc).isoformat()}", flush=True)
    init_db()

    prewarm = "--no-prewarm" not in sys.argv
    added = 0
    warmed = 0
    failed = 0

    # Lazy import — only needed when pre-warming, and it's heavy.
    _score = None
    _snap = None
    if prewarm:
        try:
            from utils.ticker_score import compute_full_ticker_score as _score
            from utils.score_history import record_score_snapshot as _snap
        except Exception as e:
            print(f"[grow_universe] pre-warm unavailable ({e}); seeding only", flush=True)
            prewarm = False

    for industry, tickers in BIG_NAMES.items():
        for t in tickers:
            if add_to_universe(t, source="daily", sector=industry):
                added += 1
            if prewarm and _score and _snap:
                try:
                    r = _score(t)
                    c = r["confluence"]
                    _snap(t, c["overall_score"], c["case"], c["conviction"])
                    warmed += 1
                    time.sleep(0.4)   # gentle on yfinance/FRED rate limits
                except Exception:
                    failed += 1

    size = universe_size()
    print(f"[grow_universe] done — seeded {added} names, pre-warmed {warmed} "
          f"({failed} warm failures). Universe now: {size['total']} total "
          f"({size['static']} core + {size['added']} added).", flush=True)


if __name__ == "__main__":
    main()
