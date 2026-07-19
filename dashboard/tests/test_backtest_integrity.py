"""Tests for backtest integrity guards.

The scenario driving these is the one that was live: ~28 days of score history,
which the old code annualised into a CAGR an order of magnitude larger than the
actual gain and reported beside SPY. The tests reconstruct that exact sample and
assert the figures are withheld rather than extrapolated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from utils.backtest_integrity import (
    DEFAULT_COST_BPS,
    MIN_DAYS_FOR_CAGR,
    MIN_OBS_FOR_SHARPE,
    MIN_REBALANCES,
    assess,
    borrow_cost,
    cagr,
    max_drawdown,
    point_in_time_row,
    report,
    sharpe,
    stale_score_mask,
    total_return,
    turnover_cost,
)


def _equity(days: int, total_gain: float = 0.05, seed: int = 3) -> pd.Series:
    """Equity curve spanning `days` calendar days with a given total gain."""
    idx = pd.bdate_range("2026-06-22", periods=max(int(days * 5 / 7), 2))
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.004, len(idx))
    drift = (1 + total_gain) ** (1 / len(idx)) - 1
    return pd.Series(100 * np.cumprod(1 + drift + noise), index=idx)


# ── The live scenario ─────────────────────────────────────────────────────────

def test_four_week_sample_does_not_report_a_cagr():
    """The bug: a few percent over four weeks annualised into tens of percent."""
    eq = _equity(days=28, total_gain=0.05)
    assert cagr(eq) is None

    # Assert the distortion as a ratio rather than a fixed percentage: the exact
    # figure depends on the sample's noise, but annualising a ~27-day window
    # raises the return to roughly the 13th power regardless.
    actual = total_return(eq)
    naive_years = (eq.index[-1] - eq.index[0]).days / 365.25
    naive = (1 + actual) ** (1 / naive_years) - 1
    assert naive > actual * 5, (
        f"naive annualisation turned {actual:.1%} into {naive:.1%} — this is the "
        "inflation the guard exists to prevent"
    )


def test_four_week_sample_does_not_report_a_sharpe():
    eq = _equity(days=28)
    assert sharpe(eq) is None


def test_four_week_sample_still_reports_total_return():
    """Cumulative return makes no time claim, so it stays."""
    eq = _equity(days=28, total_gain=0.05)
    assert total_return(eq) == pytest.approx(0.05, abs=0.03)


def test_four_week_sample_still_reports_drawdown():
    assert max_drawdown(_equity(days=28)) is not None


def test_report_withholds_exactly_the_unsupported_fields():
    r = report(_equity(days=28), rebalances=4)
    assert r["cagr"] is None
    assert r["sharpe"] is None
    assert r["total_return"] is not None
    assert r["max_drawdown"] is not None
    assert r["sufficiency"].ok is False


def test_sufficiency_explains_every_failure():
    s = assess(_equity(days=28), rebalances=4)
    assert not s.ok
    joined = " ".join(s.reasons)
    assert "annualised" in joined
    assert "Sharpe" in joined
    assert "rebalances" in joined
    assert len(s.reasons) == 3


# ── Thresholds ────────────────────────────────────────────────────────────────

def test_two_year_sample_reports_everything():
    eq = _equity(days=730, total_gain=0.40)
    r = report(eq, rebalances=100)
    assert r["sufficiency"].ok
    assert r["cagr"] is not None
    assert r["sharpe"] is not None


def test_cagr_boundary_at_one_year():
    assert cagr(_equity(days=MIN_DAYS_FOR_CAGR - 40)) is None
    assert cagr(_equity(days=MIN_DAYS_FOR_CAGR + 60)) is not None


def test_cagr_is_correct_when_it_is_reported():
    """Exactly doubling over two years is ~41.4% CAGR."""
    idx = pd.to_datetime(["2024-01-01", "2026-01-01"])
    eq = pd.Series([100.0, 200.0], index=idx)
    assert cagr(eq) == pytest.approx(0.414, abs=0.01)


def test_sharpe_returns_a_standard_error():
    eq = _equity(days=900)
    result = sharpe(eq)
    assert result is not None
    s, se = result
    assert se > 0
    # se ~ sqrt((1 + s^2/2) / n)
    n = len(eq) - 1
    assert se == pytest.approx(((1 + s * s / 2) / n) ** 0.5, rel=0.01)


def test_sharpe_standard_error_shrinks_with_sample_size():
    _, se_short = sharpe(_equity(days=200))
    _, se_long = sharpe(_equity(days=1200))
    assert se_long < se_short


def test_sharpe_none_below_observation_floor():
    eq = _equity(days=int(MIN_OBS_FOR_SHARPE * 7 / 5) - 20)
    assert len(eq) < MIN_OBS_FOR_SHARPE
    assert sharpe(eq) is None


def test_rebalance_floor_blocks_otherwise_long_samples():
    """Two years with three rebalances is three draws, not a track record."""
    s = assess(_equity(days=800), rebalances=3)
    assert not s.ok
    assert any("rebalances" in r for r in s.reasons)
    assert MIN_REBALANCES > 3


# ── Look-ahead ────────────────────────────────────────────────────────────────

@pytest.fixture
def pivot() -> pd.DataFrame:
    return pd.DataFrame(
        {"AAPL": [50.0, 60.0, 70.0], "CCJ": [40.0, 45.0, 80.0]},
        index=["2026-06-01", "2026-06-15", "2026-07-01"],
    )


def test_point_in_time_never_looks_forward(pivot):
    """The bug: method='nearest' resolved to 2026-07-01 for a 2026-06-25 rebalance.

    2026-06-25 is 10 days after the 06-15 snapshot and 6 days before 07-01, so
    "nearest" picked the future one and the backtest traded on a score that did
    not exist yet.
    """
    row = point_in_time_row(pivot, "2026-06-25")
    assert row["AAPL"] == 60.0, "must use the 06-15 snapshot, not 07-01"
    assert row["CCJ"] == 45.0


def test_point_in_time_uses_exact_match_when_present(pivot):
    assert point_in_time_row(pivot, "2026-06-15")["AAPL"] == 60.0


def test_point_in_time_returns_none_before_any_data(pivot):
    """No information existed yet; the caller must skip, not guess."""
    assert point_in_time_row(pivot, "2026-01-01") is None


def test_point_in_time_uses_latest_when_date_is_after_all_data(pivot):
    assert point_in_time_row(pivot, "2027-01-01")["AAPL"] == 70.0


def test_point_in_time_handles_empty_and_garbage():
    assert point_in_time_row(pd.DataFrame(), "2026-06-01") is None
    assert point_in_time_row(pd.DataFrame({"A": [1]}, index=["2026-01-01"]), "nope") is None


# ── Staleness ─────────────────────────────────────────────────────────────────

def test_stale_mask_flags_scores_beyond_the_age_limit(pivot):
    """Unbounded ffill made a June score look live in December."""
    mask = stale_score_mask(pivot, "2026-12-01", max_age_days=45)
    assert mask["AAPL"] and mask["CCJ"]


def test_stale_mask_passes_fresh_scores(pivot):
    mask = stale_score_mask(pivot, "2026-07-10", max_age_days=45)
    assert not mask["AAPL"] and not mask["CCJ"]


def test_stale_mask_flags_tickers_with_no_prior_score(pivot):
    assert stale_score_mask(pivot, "2026-01-01", max_age_days=45).all()


# ── Costs ─────────────────────────────────────────────────────────────────────

def test_turnover_cost_of_a_full_rotation():
    """Nothing retained: 4 of 4 names changed on each side -> 100% turnover."""
    cost = turnover_cost({"A", "B"}, {"C", "D"}, cost_bps=10)
    assert cost == pytest.approx(10 / 10_000)


def test_turnover_cost_of_no_change_is_zero():
    assert turnover_cost({"A", "B"}, {"A", "B"}) == 0.0


def test_turnover_cost_is_proportional():
    half = turnover_cost({"A", "B", "C", "D"}, {"A", "B", "C", "E"}, cost_bps=10)
    full = turnover_cost({"A", "B"}, {"C", "D"}, cost_bps=10)
    assert 0 < half < full


def test_turnover_cost_on_empty_books():
    assert turnover_cost(set(), set()) == 0.0


def test_costs_are_not_zero_by_default():
    """A backtest paying nothing is not a strategy anyone can run."""
    assert DEFAULT_COST_BPS > 0
    assert turnover_cost({"A"}, {"B"}) > 0


def test_borrow_cost_scales_with_holding_period():
    week = borrow_cost(7)
    year = borrow_cost(365)
    assert year > week > 0
    assert year == pytest.approx(50 / 10_000, rel=0.01)


def test_borrow_cost_zero_for_no_holding():
    assert borrow_cost(0) == 0.0


# ── Degenerate inputs ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("fn", [total_return, cagr, max_drawdown])
def test_metrics_on_empty_series(fn):
    assert fn(pd.Series(dtype=float)) is None


def test_assess_on_empty_series():
    s = assess(pd.Series(dtype=float), rebalances=0)
    assert not s.ok and s.days == 0


def test_flat_equity_has_no_sharpe():
    idx = pd.bdate_range("2024-01-01", periods=400)
    assert sharpe(pd.Series(100.0, index=idx)) is None
