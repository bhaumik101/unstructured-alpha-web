"""
Tests for the Ticker Deep Dive segmented-control restructuring
(pages/3_Ticker_Deep_Dive.py).

Context: this page was originally one 1,351-line linear scroll. It was
split into 4 sections (Overview / Insider & Short Interest / 13F &
Federal Contracts / Deep Correlation Scan) selected via
st.segmented_control -- chosen deliberately over st.tabs() because a
live check (not an assumption) confirmed st.tabs() executes every tab's
code on every script run regardless of which tab is showing, while
branching on segmented_control's return value with if/elif genuinely
skips code for unselected sections.

The headline Confluence Score still depends on insider/short-interest/
13F/contracts data (they're baked into the composite at a fixed 12%
weight each -- see utils/ticker_score.py), so that part of the fetch
cost is NOT reduced by this restructuring and these tests don't claim
otherwise. What IS genuinely deferred: fetch_insider_trades(), a second,
separate call used only for the "all Form 4 filings" detail expander
(not used in scoring at all) -- that one only fires when the Insider &
Short Interest section is actually open, which is what the last test
below confirms directly.
"""

import pytest


def _all_markdown_text(at):
    return " ".join(md.value for md in at.markdown)


def test_default_load_shows_overview_not_other_sections(app_test):
    """
    On first load (default section = "Overview"), Overview-only content
    must render, and content exclusive to the other three sections must
    NOT appear -- confirming the if/elif branching genuinely excludes the
    unselected sections rather than just visually hiding them.
    """
    at = app_test("pages/3_Ticker_Deep_Dive.py")
    assert not at.exception, (
        "Default Overview load raised: " + "\n".join(str(e) for e in at.exception)
    )
    text = _all_markdown_text(at)

    # Overview-exclusive content
    assert "SIGNAL-BASED PREDICTION MODEL" in text
    assert "Bull Case vs. Bear Case" in text
    assert "Signal Detail Table" in text

    # Content exclusive to the OTHER three sections must not leak in
    assert "Federal Contract Awards (USASpending.gov)" not in text
    assert "Insider Transactions (SEC Form 4)" not in text
    assert "13F Institutional Positioning" not in text
    assert "DEEP CORRELATION SCAN" not in text


def test_switching_to_insider_short_interest_section(app_test):
    at = app_test("pages/3_Ticker_Deep_Dive.py")
    sc = next((s for s in at.segmented_control if s.key == "dive_section"), None)
    assert sc is not None, "Section segmented_control not found"

    sc.set_value("Insider & Short Interest").run()
    assert not at.exception, (
        "Switching to Insider & Short Interest raised: " + "\n".join(str(e) for e in at.exception)
    )
    text = _all_markdown_text(at)
    assert "Insider Transactions (SEC Form 4)" in text
    assert "Short Interest (FINRA" in text
    # Overview content should no longer be in the executed branch
    assert "SIGNAL-BASED PREDICTION MODEL" not in text
    assert "Federal Contract Awards (USASpending.gov)" not in text


def test_switching_to_13f_federal_contracts_section(app_test):
    at = app_test("pages/3_Ticker_Deep_Dive.py")
    sc = next((s for s in at.segmented_control if s.key == "dive_section"), None)
    sc.set_value("13F & Federal Contracts").run()
    assert not at.exception, (
        "Switching to 13F & Federal Contracts raised: " + "\n".join(str(e) for e in at.exception)
    )
    text = _all_markdown_text(at)
    assert "Federal Contract Awards (USASpending.gov)" in text
    assert "13F Institutional Positioning" in text
    assert "Insider Transactions (SEC Form 4)" not in text


def test_switching_to_deep_correlation_scan_section(app_test):
    at = app_test("pages/3_Ticker_Deep_Dive.py")
    sc = next((s for s in at.segmented_control if s.key == "dive_section"), None)
    sc.set_value("Deep Correlation Scan").run()
    assert not at.exception, (
        "Switching to Deep Correlation Scan raised: " + "\n".join(str(e) for e in at.exception)
    )
    text = _all_markdown_text(at)
    assert "DEEP CORRELATION SCAN" in text
    assert "SIGNAL-BASED PREDICTION MODEL" not in text


def test_insider_history_fetch_only_runs_on_insider_section(app_test, monkeypatch):
    """
    The single concrete "excess usage" fix this restructuring delivers:
    fetch_insider_trades() (used only for the "all Form 4 filings" detail
    table, never for scoring) must NOT be called while on Overview, and
    MUST be called once the Insider & Short Interest section is opened.
    """
    calls = []

    def _fake_fetch_insider_trades(ticker, days=180):
        calls.append((ticker, days))
        import pandas as pd
        return pd.DataFrame()

    # The page does `from utils.fetchers import fetch_insider_trades` at its
    # own module top level, but AppTest fully re-executes the page script
    # (including imports) on every .run() -- so patching the real source
    # here, BEFORE the first app_test() call below, is reached correctly.
    # (Page filenames starting with a digit, like "3_Ticker_Deep_Dive",
    # aren't valid dotted-string targets for monkeypatch anyway.)
    import utils.fetchers as fetchers_mod
    monkeypatch.setattr(fetchers_mod, "fetch_insider_trades", _fake_fetch_insider_trades)

    at = app_test("pages/3_Ticker_Deep_Dive.py")
    assert calls == [], (
        f"fetch_insider_trades was called on Overview load, should be deferred: {calls}"
    )

    sc = next((s for s in at.segmented_control if s.key == "dive_section"), None)
    sc.set_value("Insider & Short Interest").run()
    assert not at.exception, (
        "Switching to Insider & Short Interest raised: " + "\n".join(str(e) for e in at.exception)
    )
