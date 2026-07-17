"""Tests for utils.guards — resource caps + downsampling."""
import pandas as pd

from utils import guards


def test_caps_are_positive_ints():
    for name in ("MAX_PORTFOLIO_HOLDINGS", "MAX_BASKET_TICKERS", "MAX_EXPORT_ROWS",
                 "MAX_CHART_POINTS", "MAX_LOOKBACK_YEARS", "MAX_TICKERS_PER_REQUEST"):
        v = getattr(guards, name)
        assert isinstance(v, int) and v >= 1


def test_clamp():
    assert guards.clamp(5, 1, 10) == 5
    assert guards.clamp(-3, 1, 10) == 1
    assert guards.clamp(99, 1, 10) == 10


def test_cap_list_truncates():
    out, trunc = guards.cap_list(list(range(100)), 10)
    assert out == list(range(10)) and trunc is True


def test_cap_list_no_truncate():
    out, trunc = guards.cap_list([1, 2, 3], 10)
    assert out == [1, 2, 3] and trunc is False


def test_downsample_series_keeps_endpoints():
    s = pd.Series(range(10000))
    ds = guards.downsample_for_chart(s, max_points=500)
    assert len(ds) <= 502
    assert ds.iloc[0] == 0
    assert ds.iloc[-1] == 9999  # latest value preserved


def test_downsample_short_series_unchanged():
    s = pd.Series(range(100))
    assert guards.downsample_for_chart(s, max_points=500) is s


def test_downsample_xy():
    x = list(range(10000)); y = list(range(10000))
    x2, y2 = guards.downsample_for_chart(x, y, max_points=500)
    assert len(x2) <= 502 and x2[-1] == 9999 and y2[-1] == 9999


def test_downsample_never_raises_on_junk():
    # Non-sized input should return unchanged, not raise.
    assert guards.downsample_for_chart(None) is None
