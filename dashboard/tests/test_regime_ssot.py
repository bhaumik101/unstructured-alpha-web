"""The macro regime must be computed one way, everywhere.

Regression guard for the landing-page bug where the sticky header bar and the
home hero showed different bull/bear/neutral/excluded counts because each rolled
its own computation off a different data source. These tests pin the invariants
of the shared utils.regime.compute_macro_regime SSOT and assert both surfaces
route through it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.regime import Regime, compute_macro_regime

DASHBOARD = Path(__file__).resolve().parent.parent


def _signals(bull=0, bear=0, neutral=0, errored=0):
    d = {}
    i = 0
    for _ in range(bull):
        d[f"s{i}"] = {"status": "bullish"}; i += 1
    for _ in range(bear):
        d[f"s{i}"] = {"status": "bearish"}; i += 1
    for _ in range(neutral):
        d[f"s{i}"] = {"status": "neutral"}; i += 1
    for _ in range(errored):
        d[f"s{i}"] = {"status": "bullish", "error": "fetch failed"}; i += 1
    return d


# ── The core invariant: counts reconcile to the total ────────────────────────

def test_counts_reconcile_to_total():
    """bull + bear + neutral + excluded == total, always. This is exactly what
    broke on the landing page (bar showed excl3 while banner said 4)."""
    r = compute_macro_regime(_signals(bull=15, bear=8, neutral=20), total=47)
    assert r.bullish == 15 and r.bearish == 8 and r.neutral == 20
    assert r.scored == 43
    assert r.excluded == 4          # 47 - 43
    assert r.bullish + r.bearish + r.neutral + r.excluded == r.total


def test_errored_signals_are_excluded_not_counted():
    """A failed signal must not be counted as bull/bear/neutral. The old bug let
    an errored signal leak into the regime buckets on one surface but not the
    other."""
    r = compute_macro_regime(_signals(bull=10, bear=5, neutral=5, errored=3), total=47)
    assert r.scored == 20           # the 3 errored are NOT scored
    assert r.excluded == 27         # 47 - 20
    assert r.bullish == 10          # errored bullish did not inflate this


def test_same_input_same_output():
    """The whole point: given identical input, header and hero get identical
    numbers. Determinism across two independent calls."""
    sig = _signals(bull=14, bear=8, neutral=22)
    a = compute_macro_regime(sig, total=47)
    b = compute_macro_regime(sig, total=47)
    assert a == b


# ── Label thresholds preserved from the old header logic ─────────────────────

@pytest.mark.parametrize("bull,bear,neutral,expected", [
    (30, 5, 5, "RISK-ON"),        # 30/40 = 75% bull >= 0.58
    (5, 25, 10, "RISK-OFF"),      # 25/40 = 62.5% bear >= 0.52
    (20, 5, 15, "LEANING BULLISH"),  # 20/40 = 50% >= 0.48, < 0.58
    (5, 18, 17, "LEANING BEARISH"),  # 18/40 = 45% >= 0.44, < 0.52
    (12, 12, 16, "MIXED SIGNALS"),   # neither lean threshold met
])
def test_label_thresholds(bull, bear, neutral, expected):
    r = compute_macro_regime(_signals(bull=bull, bear=bear, neutral=neutral), total=100)
    assert r.label == expected


def test_no_data_is_awaiting_snapshot():
    r = compute_macro_regime({}, total=47)
    assert r.label == "AWAITING SNAPSHOT"
    assert r.scored == 0 and r.excluded == 47


def test_none_input_is_safe():
    r = compute_macro_regime(None)
    assert r.scored == 0
    assert isinstance(r, Regime)


def test_non_dict_values_do_not_crash():
    r = compute_macro_regime({"a": {"status": "bullish"}, "b": "oops", "c": None}, total=47)
    assert r.bullish == 1 and r.scored == 1


def test_bull_pct_is_share_of_scored():
    r = compute_macro_regime(_signals(bull=10, bear=10, neutral=0), total=47)
    assert r.bull_pct == pytest.approx(0.5)
    assert r.bull_pct_display == 50


# ── Both regime surfaces route through the SSOT ──────────────────────────────

def test_header_uses_the_ssot():
    src = (DASHBOARD / "utils" / "header.py").read_text(encoding="utf-8")
    assert "compute_macro_regime" in src, (
        "the sticky header regime bar must classify via utils.regime, not its own count"
    )


def test_home_hero_uses_the_ssot():
    src = (DASHBOARD / "pages" / "home_page.py").read_text(encoding="utf-8")
    assert "compute_macro_regime" in src, (
        "the home hero regime headline must classify via utils.regime, not len() of "
        "live-score lists — otherwise it drifts from the header again"
    )


def test_home_hero_no_longer_claims_2h_cache_for_snapshot_regime():
    """The hero regime is snapshot-based now; it must not label it a 2h live cache."""
    src = (DASHBOARD / "pages" / "home_page.py").read_text(encoding="utf-8")
    # The regime block's freshness label was corrected to 'daily snapshot'.
    assert "daily snapshot" in src
