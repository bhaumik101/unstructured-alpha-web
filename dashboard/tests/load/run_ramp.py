#!/usr/bin/env python3
"""
Drive a staged Locust ramp (1 → 5 → 10 → 25 → 50 users) against the SEO
service and print a compact per-stage summary (RPS, p50/p95/p99, failures).

Each stage runs headless for a fixed duration and writes Locust CSVs under
results/. Safe against production: read-only endpoints only.

    python tests/load/run_ramp.py                      # default host
    python tests/load/run_ramp.py --host https://seo.unstructuredalpha.com
    python tests/load/run_ramp.py --duration 60        # seconds per stage
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys

STAGES = [1, 5, 10, 25, 50]
HERE = os.path.dirname(os.path.abspath(__file__))
LOCUSTFILE = os.path.join(HERE, "locustfile.py")
RESULTS = os.path.join(HERE, "..", "..", "results")


def run_stage(users: int, host: str, duration: int) -> str:
    os.makedirs(RESULTS, exist_ok=True)
    prefix = os.path.join(RESULTS, f"stage_{users:02d}")
    spawn = max(1, users // 5) or 1
    cmd = [
        sys.executable, "-m", "locust", "-f", LOCUSTFILE, "--headless",
        "-u", str(users), "-r", str(spawn), "-t", f"{duration}s",
        "--host", host, "--csv", prefix, "--only-summary",
        "--stop-timeout", "10",
    ]
    print(f"\n=== stage: {users} users ({duration}s, spawn {spawn}/s) ===", flush=True)
    subprocess.run(cmd, check=False)
    return prefix + "_stats.csv"


def summarize(users: int, stats_csv: str) -> dict | None:
    if not os.path.exists(stats_csv):
        return None
    with open(stats_csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
    agg = next((r for r in rows if r.get("Name") == "Aggregated"), None)
    if not agg:
        return None
    return {
        "users": users,
        "reqs": agg.get("Request Count"),
        "fails": agg.get("Failure Count"),
        "rps": agg.get("Requests/s"),
        "p50": agg.get("50%"),
        "p95": agg.get("95%"),
        "p99": agg.get("99%"),
        "max": agg.get("Max Response Time"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="https://seo.unstructuredalpha.com")
    ap.add_argument("--duration", type=int, default=45, help="seconds per stage")
    args = ap.parse_args()

    summaries = []
    for u in STAGES:
        stats = run_stage(u, args.host, args.duration)
        s = summarize(u, stats)
        if s:
            summaries.append(s)

    print("\n\n================  RAMP SUMMARY  ================")
    hdr = f"{'users':>5} {'reqs':>7} {'fails':>6} {'rps':>7} {'p50':>7} {'p95':>8} {'p99':>8} {'max':>8}"
    print(hdr)
    print("-" * len(hdr))
    for s in summaries:
        print(f"{s['users']:>5} {s['reqs']:>7} {s['fails']:>6} "
              f"{float(s['rps']):>7.1f} {s['p50']:>7} {s['p95']:>8} {s['p99']:>8} {s['max']:>8}")


if __name__ == "__main__":
    main()
