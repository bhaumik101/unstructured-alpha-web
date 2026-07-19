#!/usr/bin/env python3
# cron/score_universe.py
# Unstructured Alpha — Batch Confluence-Score Worker
#
# Precomputes Confluence Scores for the qualifying universe (~5.3k common stocks,
# see utils/scoring_universe.py) and writes them to score_snapshots, so Deep Dive,
# the screener and the recommender READ a score instead of computing one cold.
#
# WHY THIS IS TRACTABLE
#   The 47 macro signals are ticker-INDEPENDENT. They're fetched once and reused
#   for every ticker in the run (via the module-level cache in utils/fetchers),
#   so the marginal cost per ticker is a batched price fetch plus correlation
#   math — not 47 more network calls.
#
# DESIGN RULES
#   • Runs OFF the interactive path — this is a cron/worker, never the web process.
#   • Bounded: chunked batch fetches, a hard ticker budget, and a wall-clock
#     deadline, so a run can't grow without limit or overlap the next one.
#   • Memory-safe: prices are released and the heap trimmed between chunks.
#   • Idempotent: record_score_snapshot upserts on (ticker, snapshot_date), and a
#     FAILED compute never writes — so a bad run cannot overwrite good data.
#   • Isolated per ticker: one bad symbol never aborts the run.
#
# TIERS (cadence lives in render.yaml, not here)
#   core : the curated tickers + everything users actually watch  → run daily
#   rest : the remaining qualifying universe, rotated in daily slices so the whole
#          universe is refreshed over --rotate-days without scoring 5k every day
#
# Run manually (from dashboard/):
#   python -m cron.score_universe --tier core --dry-run
#   python -m cron.score_universe --tier rest --rotate-days 7

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_here = Path(__file__).resolve().parent.parent   # dashboard/
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

CHUNK_SIZE = 120          # symbols per batched price request
DEFAULT_BUDGET = 1200     # max tickers scored in one run
DEFAULT_DEADLINE_MIN = 50  # wall-clock guard


def _log(event: str, **fields):
    """Structured line when observability is available, plain print otherwise."""
    try:
        from utils.observability import log_event
        log_event(event, **fields)
    except Exception:
        pass
    print(f"[score_universe] {event} " +
          " ".join(f"{k}={v}" for k, v in fields.items()), flush=True)


def _core_tickers() -> list[str]:
    """Curated tickers + every ticker any user actually watches."""
    out: set[str] = set()
    try:
        from utils.config import TICKERS
        out.update(TICKERS.keys())
    except Exception:
        pass
    try:  # anything on a real watchlist is worth keeping fresh daily
        from sqlalchemy import select
        from utils.db import engine, watchlist
        with engine.begin() as conn:
            for r in conn.execute(select(watchlist.c.ticker).distinct()).fetchall():
                if r[0]:
                    out.add(str(r[0]).upper().strip())
    except Exception:
        pass
    return sorted(out)


def _rest_slice(scoreable: dict, core: set[str], rotate_days: int) -> list[str]:
    """
    Today's slice of the non-core universe. Deterministic rotation by day-of-year
    so consecutive runs cover different symbols and the whole universe is
    refreshed every `rotate_days` — no cursor/state to keep in sync.
    """
    rest = sorted(s for s in scoreable if s not in core)
    if not rest or rotate_days <= 1:
        return rest
    day = datetime.now(timezone.utc).timetuple().tm_yday % rotate_days
    return [s for i, s in enumerate(rest) if i % rotate_days == day]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["core", "rest", "all"], default="core")
    ap.add_argument("--rotate-days", type=int, default=7)
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--deadline-min", type=int, default=DEFAULT_DEADLINE_MIN)
    ap.add_argument("--dry-run", action="store_true",
                    help="select + gate tickers but write nothing")
    args = ap.parse_args()

    t0 = time.monotonic()
    deadline = t0 + args.deadline_min * 60

    from utils.db import init_db
    from utils.scoring_universe import (
        build_scoring_universe, qualifies_on_price, OK,
    )
    from utils.ticker_score import compute_full_ticker_score, price_window
    from utils.fetchers import fetch_prices_batch
    from utils.score_history import record_score_snapshot
    try:
        from utils.memory import release_memory
    except Exception:
        release_memory = lambda: None            # noqa: E731

    init_db()

    universe = build_scoring_universe()
    scoreable = universe["scoreable"]
    core = set(_core_tickers())

    if args.tier == "core":
        # Everything in core is scored regardless of the offline classifier: these
        # are curated tickers and symbols real users chose to watch. The price
        # gate below still applies, so nothing gets a score without real data.
        targets = sorted(core)
    elif args.tier == "rest":
        targets = _rest_slice(scoreable, core, args.rotate_days)
    else:
        targets = sorted(set(scoreable) | core)

    targets = targets[: args.budget]

    # WHICH score this run produces — these are DIFFERENT metrics, not two
    # precisions of the same one (measured on AAPL: 45.6 full vs 56.3 macro-only),
    # so they're stored under distinct score_kind values and never conflated.
    #   core → the full Confluence Score, matching Ticker Deep Dive exactly.
    #          Costly (4 network calls/ticker) but this tier is small.
    #   rest → macro + momentum only: the same blend the Screener already labels
    #          "Macro + Momentum Rank". ~425x faster, which is the only reason
    #          scoring thousands of tickers is possible at all.
    want_optional = args.tier == "core"
    score_kind = "full" if want_optional else "macro_momentum"

    _log("run_start", tier=args.tier, universe=len(scoreable), core=len(core),
         targets=len(targets), score_kind=score_kind, dry_run=args.dry_run)

    start_px, end_px = price_window()
    stats = {"scored": 0, "written": 0, "gated": 0, "failed": 0, "chunks": 0}
    gate_reasons: dict[str, int] = {}

    for i in range(0, len(targets), CHUNK_SIZE):
        if time.monotonic() > deadline:
            _log("deadline_reached", scored=stats["scored"])
            break
        chunk = tuple(targets[i:i + CHUNK_SIZE])
        stats["chunks"] += 1
        try:
            prices = fetch_prices_batch(chunk, start_px, end_px)
        except Exception as exc:
            _log("chunk_fetch_failed", chunk=i // CHUNK_SIZE, error=str(exc)[:120])
            continue

        for tkr in chunk:
            try:
                series = prices.get(tkr)
                reason = qualifies_on_price(series)
                if reason != OK:
                    stats["gated"] += 1
                    gate_reasons[reason] = gate_reasons.get(reason, 0) + 1
                    continue
                full = compute_full_ticker_score(tkr, price_series=series,
                                                 include_optional=want_optional)
                conf = (full or {}).get("confluence") or {}
                score = conf.get("overall_score")
                if score is None:
                    stats["failed"] += 1
                    continue
                stats["scored"] += 1
                if not args.dry_run:
                    # Only a SUCCESSFUL compute ever writes — a failure must not
                    # overwrite a good prior snapshot.
                    record_score_snapshot(tkr, float(score),
                                          conf.get("case", ""), conf.get("conviction", ""),
                                          kind=score_kind)
                    stats["written"] += 1
            except Exception:
                stats["failed"] += 1
                continue

        del prices
        release_memory()      # keep peak RSS flat across chunks

    _log("run_complete", tier=args.tier, duration_s=round(time.monotonic() - t0, 1),
         **stats, **{f"gate_{k}": v for k, v in gate_reasons.items()})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:                      # never fail the cron loudly
        print(f"[score_universe] fatal: {exc}", file=sys.stderr, flush=True)
    sys.exit(0)
