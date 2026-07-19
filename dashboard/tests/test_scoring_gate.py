"""Tests for the price-based qualification gate (utils.scoring_universe)."""
import pandas as pd

from utils import scoring_universe as su


def _series(n, price=50.0):
    return pd.Series([price] * n)


def test_full_history_normal_price_qualifies():
    assert su.qualifies_on_price(_series(300, 50.0)) == su.OK


def test_short_history_rejected():
    assert su.qualifies_on_price(_series(50, 50.0)) == su.EXCL_SHORT_HISTORY


def test_exact_minimum_history_qualifies():
    assert su.qualifies_on_price(_series(su.MIN_HISTORY_DAYS, 50.0)) == su.OK


def test_penny_stock_rejected():
    assert su.qualifies_on_price(_series(300, 0.42)) == su.EXCL_PENNY


def test_empty_and_none_rejected():
    assert su.qualifies_on_price(None) == su.EXCL_NO_DATA
    assert su.qualifies_on_price(pd.Series(dtype=float)) == su.EXCL_NO_DATA


def test_all_nan_rejected():
    assert su.qualifies_on_price(pd.Series([float("nan")] * 300)) == su.EXCL_NO_DATA


def test_nans_dropped_before_history_check():
    # 300 rows but only 40 real observations -> insufficient history, not "ok"
    s = pd.Series([50.0] * 40 + [float("nan")] * 260)
    assert su.qualifies_on_price(s) == su.EXCL_SHORT_HISTORY


def test_latest_price_is_what_counts():
    # long history but the name has collapsed below $1 -> reject
    s = pd.Series([50.0] * 299 + [0.30])
    assert su.qualifies_on_price(s) == su.EXCL_PENNY


def test_thresholds_are_overridable():
    assert su.qualifies_on_price(_series(60, 50.0), min_days=30) == su.OK
    assert su.qualifies_on_price(_series(300, 0.5), min_price=0.1) == su.OK


def test_never_raises_on_garbage():
    for junk in ("not a series", 123, {"a": 1}, object()):
        assert isinstance(su.qualifies_on_price(junk), str)
