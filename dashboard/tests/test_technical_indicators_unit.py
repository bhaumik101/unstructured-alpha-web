"""
Unit tests for utils/analysis.py's compute_rsi() (added 2026-06-22, per
explicit user request for "volume, RSI and other basic indicators" on
Ticker Deep Dive). Verified against hand-calculable synthetic cases --
exact known boundary values, not just "doesn't crash" -- per the
standing project rule that every new signal/indicator must be validated
against known ground truth before shipping.
"""

import numpy as np
import pandas as pd
import pytest

from utils.analysis import compute_rsi


def _monotonic_series(n=30, step=1.0, start=100.0):
    return pd.Series(start + step * np.arange(n), index=pd.date_range("2025-01-01", periods=n, freq="D"))


def test_rsi_is_100_when_price_only_ever_rises():
    """Zero losses anywhere in the lookback -- RS = avg_gain / 0 = infinity,
    which the textbook formula maps to RSI = 100. Hand-verifiable: every
    single change is a gain of the same size, so avg_loss is exactly 0."""
    price = _monotonic_series(n=30, step=2.0)
    rsi = compute_rsi(price, period=14)
    assert rsi.dropna().iloc[-1] == pytest.approx(100.0, abs=1e-6)


def test_rsi_is_0_when_price_only_ever_falls():
    price = _monotonic_series(n=30, step=-2.0)
    rsi = compute_rsi(price, period=14)
    assert rsi.dropna().iloc[-1] == pytest.approx(0.0, abs=1e-6)


def test_rsi_is_50_for_a_perfectly_flat_price():
    """No movement at all -- avg_gain and avg_loss are both exactly 0,
    the 0/0 edge case the implementation explicitly handles as the
    textbook-convention neutral reading rather than NaN."""
    price = pd.Series([100.0] * 30, index=pd.date_range("2025-01-01", periods=30, freq="D"))
    rsi = compute_rsi(price, period=14)
    assert rsi.dropna().iloc[-1] == pytest.approx(50.0, abs=1e-6)


def test_rsi_is_always_bounded_0_to_100():
    """Property check across several different random walks -- RSI must
    never escape its defined range regardless of the input series."""
    rng = np.random.default_rng(11)
    for seed in range(5):
        vals = 100 + np.cumsum(rng.normal(0, 2, 100))
        price = pd.Series(vals, index=pd.date_range("2025-01-01", periods=100, freq="D"))
        rsi = compute_rsi(price, period=14).dropna()
        assert (rsi >= -1e-9).all() and (rsi <= 100 + 1e-9).all()


def test_rsi_first_period_points_are_nan():
    """min_periods=period in the underlying ewm() means there shouldn't be
    a "confident" RSI reading before at least `period` price changes have
    been observed."""
    price = _monotonic_series(n=30, step=1.0)
    rsi = compute_rsi(price, period=14)
    assert rsi.iloc[:14].isna().all()
    assert rsi.iloc[14:].notna().all()


def test_rsi_empty_series_returns_empty():
    empty = pd.Series(dtype=float)
    result = compute_rsi(empty)
    assert result.empty


def test_rsi_moderate_uptrend_sits_above_50_not_below():
    """A directional sanity check that doesn't depend on the trickier
    exact-convergence math above: a price that rises more often than it
    falls (e.g. 60% up days) must show RSI meaningfully above 50, since
    avg_gain is genuinely larger than avg_loss over the lookback -- this
    is the actual property RSI is supposed to capture, checked the
    simple, robust way rather than chasing an exact asymptotic value for
    a constructed edge case."""
    rng = np.random.default_rng(42)
    n = 60
    steps = np.where(rng.random(n) < 0.65, 1.0, -1.0)  # 65% up days
    vals = 100 + np.cumsum(steps)
    price = pd.Series(vals, index=pd.date_range("2025-01-01", periods=n, freq="D"))
    rsi = compute_rsi(price, period=14).dropna()
    assert rsi.iloc[-1] > 55.0
