"""Guards on the batch scoring cron.

Render killed the first score-core run nine minutes in: "Ran out of memory
(used over 512MB)". The run had a wall-clock deadline but no memory guard, so
it was killed rather than stopping, and an OOM kill loses the whole run — which
then repeats identically the following night. That is why score_snapshots held
43 rows weeks after the cron was scheduled.

These tests cover the guard itself and the failure modes that would make it
worse than useless: tripping on a healthy run, or never tripping at all.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

DASHBOARD = Path(__file__).resolve().parent.parent

# Subprocess-based runs touch the network and take ~1min; deselect with
#   pytest -m 'not slow'
slow = pytest.mark.slow


def _run(env_extra: dict[str, str], *args: str) -> str:
    env = {**os.environ, **env_extra}
    proc = subprocess.run(
        [sys.executable, "-m", "cron.score_universe", "--dry-run", *args],
        cwd=DASHBOARD, env=env, capture_output=True, text=True, timeout=300,
    )
    return proc.stdout + proc.stderr


# ── The guard ─────────────────────────────────────────────────────────────────

@slow
def test_memory_guard_stops_cleanly_instead_of_being_killed():
    """A limit below the import baseline must halt the run gracefully."""
    out = _run({"SCORE_MAX_RSS_MB": "50"}, "--tier", "core", "--budget", "50")
    assert "memory_guard_reached" in out
    # Crucially it still reaches run_complete: a clean stop, not a kill.
    assert "run_complete" in out


@slow
def test_healthy_run_is_not_stopped_by_the_guard():
    """The guard must not fire at the default limit on a small run.

    This is the regression that matters most: a guard reading PEAK rss would
    trip on every check after the first spike and silently stop all real work.
    """
    out = _run({}, "--tier", "core", "--budget", "3")
    assert "memory_guard_reached" not in out
    assert "run_complete" in out


# ── The reading ───────────────────────────────────────────────────────────────

def test_rss_reader_returns_a_plausible_current_value():
    sys.path.insert(0, str(DASHBOARD))
    from cron.score_universe import _rss_mb

    mb = _rss_mb()
    assert mb > 0, "could not read RSS at all"
    assert mb < 100_000, "implausible RSS — units are probably wrong"


@pytest.mark.skipif(
    not Path("/proc/self/statm").exists(),
    reason=(
        "Current-RSS reads come from /proc/self/statm, which only exists on "
        "Linux. The cron runs on Linux; the getrusage fallback used on macOS is "
        "peak-based and deliberately conservative, so this behaviour cannot be "
        "asserted here."
    ),
)
def test_rss_reader_reports_current_not_peak():
    """ru_maxrss never falls, so a peak-based guard halts healthy runs.

    Allocating and freeing a large block should not leave the reading
    permanently elevated by that block's full size.
    """
    sys.path.insert(0, str(DASHBOARD))
    from cron.score_universe import _rss_mb

    before = _rss_mb()
    blob = bytearray(180 * 1024 * 1024)  # 180MB
    during = _rss_mb()
    del blob
    import gc
    gc.collect()
    after = _rss_mb()

    assert during > before, "reader did not observe the allocation at all"
    # A peak-based reader would keep `after` at roughly `during`.
    assert after < during - 50, (
        f"reading stayed at {after:.0f}MB after freeing 180MB (peak was "
        f"{during:.0f}MB) — this looks like a peak metric, which would trip the "
        "guard permanently after any single spike"
    )


def test_rss_reader_never_raises(monkeypatch):
    """An unreadable RSS must yield 0.0, which cannot trip the guard."""
    sys.path.insert(0, str(DASHBOARD))
    import cron.score_universe as su

    def boom(*a, **k):
        raise OSError("no /proc here")

    monkeypatch.setattr("builtins.open", boom)
    monkeypatch.setattr(su, "sys", sys)
    # resource may still work; either way it must not raise.
    assert su._rss_mb() >= 0.0


# ── Configuration ─────────────────────────────────────────────────────────────

def test_default_limit_leaves_headroom_under_the_starter_ceiling():
    sys.path.insert(0, str(DASHBOARD))
    from cron.score_universe import DEFAULT_MAX_RSS_MB

    assert DEFAULT_MAX_RSS_MB < 512, "guard must fire before Render's OOM kill"
    assert DEFAULT_MAX_RSS_MB > 270, (
        "measured baseline is ~270MB with signals loaded; a limit at or below "
        "that would stop every run before it scored anything"
    )


def test_limit_is_overridable_by_env():
    """So the limit can be raised with the plan without a code change."""
    sys.path.insert(0, str(DASHBOARD))
    src = (DASHBOARD / "cron" / "score_universe.py").read_text()
    assert "SCORE_MAX_RSS_MB" in src


def test_guard_is_checked_before_the_deadline():
    """Otherwise a memory stop gets misreported as a timeout."""
    src = (DASHBOARD / "cron" / "score_universe.py").read_text()
    assert src.index("memory_guard_reached") < src.index("deadline_reached")
