"""
Tests for the price / daily % change / mini sparkline additions to
Watchlist (pages/10_Watchlist.py) and Stock Screener
(pages/6_Stock_Screener.py), both now built on the shared
utils/quotes.py module (2026-06-22, per explicit user request).

Mocks utils.quotes.get_batch_quotes() with deterministic, synthetic
quote data rather than depending on live yfinance access -- fast,
reproducible, and exercises the actual rendering code path end to end
(price formatting, % change color logic, sparkline chart construction),
not just "did the underlying fetch function get called."

Cleans up the watchlist row it creates afterward -- this suite's
AppTest-based tests share one real (file-based) test DB across the
whole session (see tests/conftest.py), so a row left behind would
otherwise leak into any later test that lists user_id=1's watchlist.
"""

import pandas as pd
import pytest

from utils import alerts_db

_TEST_TICKER = "ZZTQUOTE"  # deliberately not a real ticker used elsewhere in this suite


def _fake_quote_series(n=80, start=100.0):
    dates = pd.date_range("2025-01-02", periods=n, freq="D")
    import numpy as np
    rng = np.random.default_rng(3)
    vals = start * (1 + rng.normal(0, 0.01, n)).cumprod()
    return pd.Series(vals, index=dates)


@pytest.fixture
def _watchlist_with_one_ticker():
    # init_db() is normally called lazily by the FIRST AppTest run of any
    # page (app.py calls it at startup) -- this fixture writes directly to
    # the DB before any app_test() call happens in the test body, so it
    # needs to ensure the tables exist itself when this file runs in
    # isolation (running the full suite together happens to already have
    # them from an earlier test, which is exactly the kind of order-
    # dependent assumption worth not relying on).
    alerts_db.init_db()
    alerts_db.add_to_watchlist(1, _TEST_TICKER, score_bull_threshold=65.0,
                                score_bear_threshold=35.0, price_move_pct_threshold=5.0)
    yield
    alerts_db.remove_from_watchlist(1, _TEST_TICKER)


def test_watchlist_shows_price_and_change_for_watched_ticker(app_test, monkeypatch, _watchlist_with_one_ticker):
    series = _fake_quote_series()
    fake_quote = {"last": 123.45, "chg_1d": 2.0, "chg_1d_pct": 1.65, "returns": {}, "series": series}

    import utils.quotes as quotes_mod
    monkeypatch.setattr(quotes_mod, "get_batch_quotes", lambda tickers, _v=5: {_TEST_TICKER: fake_quote})

    at = app_test("pages/10_Watchlist.py")
    assert not at.exception, (
        "Watchlist with a watched ticker raised: " + "\n".join(str(e) for e in at.exception)
    )
    all_text = " ".join(md.value for md in at.markdown)
    assert "123.45" in all_text
    assert "1.65" in all_text
    # AppTest doesn't model st.plotly_chart as a distinct queryable element
    # type (no at.plotly_chart) -- the absence of an exception with a real,
    # non-empty price series passed to mini_sparkline() is the available
    # confirmation that the chart construction path itself didn't error.


def test_watchlist_handles_missing_quote_gracefully(app_test, monkeypatch, _watchlist_with_one_ticker):
    """A ticker get_batch_quotes() couldn't fetch a quote for (bad symbol,
    yfinance hiccup, etc.) must show "unavailable" captions, never crash
    the page or fabricate a fake price."""
    import utils.quotes as quotes_mod
    monkeypatch.setattr(quotes_mod, "get_batch_quotes", lambda tickers, _v=5: {_TEST_TICKER: {}})

    at = app_test("pages/10_Watchlist.py")
    assert not at.exception, (
        "Watchlist with an unavailable quote raised: " + "\n".join(str(e) for e in at.exception)
    )
    all_captions = " ".join(c.value for c in at.caption)
    assert "unavailable" in all_captions.lower()


def test_screener_shows_price_and_1d_change_columns(app_test, monkeypatch):
    import utils.quotes as quotes_mod

    def _fake_batch(tickers, _v=5):
        return {t: {"last": 50.0, "chg_1d": 1.0, "chg_1d_pct": 2.0, "returns": {}, "series": _fake_quote_series()}
                for t in tickers}

    monkeypatch.setattr(quotes_mod, "get_batch_quotes", _fake_batch)

    at = app_test("pages/6_Stock_Screener.py")
    assert not at.exception, (
        "Stock Screener raised: " + "\n".join(str(e) for e in at.exception)
    )
    dataframes = at.dataframe
    assert len(dataframes) >= 1
    found_price_col = any(
        "Price" in df.value.columns and "1D %" in df.value.columns
        for df in dataframes
        if hasattr(df.value, "columns")
    )
    assert found_price_col, "Expected a 'Price' and '1D %' column in the screener results table"
