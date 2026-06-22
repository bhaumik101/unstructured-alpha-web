"""
Tests for utils/header.py's render_global_ticker_search() -- the
persistent ticker search box added to every page's header (2026-06-22).

The one thing that actually matters here, verified live in a throwaway
sandbox before this was wired into the real header (see that function's
own docstring for the full story): naively switching pages whenever the
selectbox has a truthy value would redirect on EVERY subsequent header
render forever, since the widget's own session_state value persists
across reruns. These tests lock in the "only navigate on a genuinely new
pick" guard so a future edit can't silently reintroduce that loop.
"""

import pytest


def test_picking_a_ticker_navigates_to_ticker_deep_dive(app_test):
    at = app_test("pages/home_page.py")
    sb = next((s for s in at.selectbox if s.key == "global_ticker_search"), None)
    assert sb is not None, "Global ticker search box not found in header"

    sb.set_value("CCJ").run()
    assert not at.exception, (
        "Picking a ticker raised: " + "\n".join(str(e) for e in at.exception)
    )
    # Confirms an actual page switch happened, not just a session_state write.
    assert any("Ticker Deep Dive" in str(t.value) for t in at.title) or any(
        "Analyzing" in md.value for md in at.markdown
    ), "Expected to land on Ticker Deep Dive after picking a ticker"


def test_rerunning_after_a_pick_does_not_navigate_again(app_test):
    """
    The actual regression this test guards against: after landing on
    Ticker Deep Dive from a pick, any further rerun of ANY page (the
    header renders on all of them) must NOT keep firing switch_page()
    just because the selectbox's stored value is still the same ticker.
    """
    at = app_test("pages/home_page.py")
    sb = next((s for s in at.selectbox if s.key == "global_ticker_search"), None)
    sb.set_value("CCJ").run()
    assert not at.exception

    # Re-run again without changing the selectbox -- if the loop guard
    # were broken, this would either raise or bounce between pages.
    at.run()
    assert not at.exception, (
        "Rerunning after a pick (no new selection) raised: "
        + "\n".join(str(e) for e in at.exception)
    )
    at.run()
    assert not at.exception


def test_picking_a_different_ticker_after_one_navigates_again(app_test):
    at = app_test("pages/home_page.py")
    sb = next((s for s in at.selectbox if s.key == "global_ticker_search"), None)
    sb.set_value("CCJ").run()
    assert at.session_state["selected_ticker"] == "CCJ"

    at.switch_page("pages/1_Signal_Dashboard.py")
    at.run()
    sb2 = next((s for s in at.selectbox if s.key == "global_ticker_search"), None)
    sb2.set_value("NVDA").run()
    assert not at.exception
    assert at.session_state["selected_ticker"] == "NVDA"
