"""Sample RSS of a real scoring-cron run to find what grows.

Baseline imports measured at 208MB and a 120-symbol price frame at 0.5MB, yet
the core run was killed at Render's 512MB ceiling nine minutes in. That gap can
only be explained by growth during the run, so this launches the cron as a
subprocess and samples its resident memory once a second.

    python scripts/profile_cron_run.py --tier core --budget 200
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="core")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()

    try:
        import psutil
    except ImportError:
        print("psutil required: pip install psutil")
        return 1

    cmd = [
        sys.executable, "-m", "cron.score_universe",
        "--tier", args.tier, "--budget", str(args.budget), "--dry-run",
    ]
    print(f"launching: {' '.join(cmd)}\n")
    proc = subprocess.Popen(cmd, cwd=DASHBOARD,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ps = psutil.Process(proc.pid)

    samples: list[tuple[float, float]] = []
    start = time.time()
    peak = 0.0
    try:
        while proc.poll() is None:
            try:
                rss = ps.memory_info().rss / 1024 / 1024
            except psutil.NoSuchProcess:
                break
            elapsed = time.time() - start
            samples.append((elapsed, rss))
            peak = max(peak, rss)
            if len(samples) % 10 == 0:
                print(f"  t={elapsed:6.0f}s  rss={rss:7.1f} MB  peak={peak:7.1f} MB")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        proc.terminate()

    print("\n" + "=" * 58)
    if not samples:
        print("no samples collected")
        return 1

    first = samples[0][1]
    last = samples[-1][1]
    print(f"  duration        {samples[-1][0]:.0f}s")
    print(f"  first sample    {first:.1f} MB")
    print(f"  final sample    {last:.1f} MB")
    print(f"  PEAK            {peak:.1f} MB")
    print(f"  growth          {last - first:+.1f} MB over the run")
    print(f"  Starter ceiling 512 MB -> {'EXCEEDED' if peak > 512 else 'fits'}")

    # Growth rate tells us whether this scales with ticker count.
    if samples[-1][0] > 30:
        rate = (last - first) / samples[-1][0]
        print(f"  growth rate     {rate * 60:+.1f} MB/min")
        if rate > 0.05:
            projected = first + rate * (args.budget / max(args.budget, 1)) * samples[-1][0] * 3
            print(f"  -> memory scales with tickers processed; a 600-ticker run "
                  f"would land near {projected:.0f} MB")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
