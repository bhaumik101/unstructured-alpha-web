"""Measure peak RSS at each stage of the scoring cron.

The score-core cron was killed by Render's 512MB Starter ceiling. Before paying
for a larger instance it is worth knowing whether the memory goes to the work
(chunk size, price frames) or to the baseline (imports), because only the first
is fixable by tuning and only the second justifies a bigger box.

    python scripts/measure_cron_memory.py
"""

from __future__ import annotations

import gc
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def rss_mb() -> float:
    """Resident set size in MB."""
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except ImportError:
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux reports KB, macOS reports bytes.
        return peak / 1024 / 1024 if sys.platform == "darwin" else peak / 1024


def stage(label: str) -> float:
    gc.collect()
    mb = rss_mb()
    print(f"  {label:<44} {mb:8.1f} MB")
    return mb


print("\nPeak RSS by stage (Render Starter ceiling = 512MB)\n" + "-" * 60)

base = stage("0. interpreter only")

import pandas  # noqa: E402
stage("1. + pandas")

import numpy  # noqa: E402
stage("2. + numpy")

import scipy.stats  # noqa: E402
stage("3. + scipy.stats")

import yfinance  # noqa: E402
stage("4. + yfinance")

try:
    import streamlit  # noqa: E402
    st_mb = stage("5. + streamlit")
except ImportError:
    st_mb = None
    print("  5. streamlit not installed")

import plotly.graph_objects  # noqa: E402
stage("6. + plotly")

from utils import config  # noqa: E402
cfg_mb = stage("7. + utils.config (47 signal defs)")

from utils.scoring_universe import build_scoring_universe  # noqa: E402
stage("8. + utils.scoring_universe")

from cron import score_universe  # noqa: E402
imports_done = stage("9. + cron.score_universe (all imports)")

print("-" * 60)
print(f"  BASELINE BEFORE ANY WORK{'':<20} {imports_done:8.1f} MB")
print(f"  Headroom left on Starter{'':<20} {512 - imports_done:8.1f} MB")
print("-" * 60)

# Now measure the actual work: one chunk of batched price history.
print("\nWork phase\n" + "-" * 60)

try:
    from utils.signals_cache import get_all_signal_scores

    get_all_signal_scores()
    after_signals = stage("10. + all 47 macro signals fetched")
except Exception as exc:
    after_signals = imports_done
    print(f"  10. signal fetch skipped: {str(exc)[:44]}")

CHUNK = int(os.environ.get("CHUNK", "120"))
try:
    import yfinance as yf

    universe = list(config.TICKERS)[:CHUNK]
    px = yf.download(universe, period="2y", auto_adjust=True,
                     progress=False, threads=False)["Close"]
    after_chunk = stage(f"11. + one {CHUNK}-symbol price chunk")
    print(f"      frame: {px.shape[0]} rows x {px.shape[1]} cols, "
          f"{px.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    del px
    gc.collect()
    stage("12. after releasing the chunk")
except Exception as exc:
    after_chunk = after_signals
    print(f"  11. price fetch failed: {str(exc)[:44]}")

print("-" * 60)
print(f"\nVERDICT")
pct = imports_done / 512 * 100
print(f"  Imports alone consume {imports_done:.0f}MB = {pct:.0f}% of the Starter ceiling.")
if st_mb is not None:
    print(f"  Streamlit is imported by a batch worker that never renders a page.")
print(f"  Tuning CHUNK_SIZE only affects the work phase, which is the "
      f"{after_chunk - imports_done:.0f}MB above baseline.\n")
