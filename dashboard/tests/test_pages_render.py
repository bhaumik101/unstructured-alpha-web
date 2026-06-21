"""
Every routed page must render with zero exceptions, with no API keys
configured (the worst case: every signal falls back to synthetic data,
every price fetch may fail). This is the single most important regression
test in this suite — it is the automated version of the manual "ast.parse +
AppTest across all pages" check that's been run by hand after every change
so far in this project. A bad series ID, a missing dict key in a fallback
path, or a KeyError in a chart builder should fail HERE, not get caught
days later by a user screenshot.
"""

import pytest

from tests.conftest import ROUTED_PAGES


@pytest.mark.parametrize("page_path", ROUTED_PAGES)
def test_page_renders_without_exception(app_test, page_path):
    at = app_test(page_path)
    assert not at.exception, (
        f"{page_path} raised: " + "\n".join(str(e) for e in at.exception)
    )


def test_about_page_backtest_button_runs_without_exception(app_test):
    """
    Exercises the "Run Live Backtest" button click on the About page, not
    just the page's initial render — this is the only way to actually
    execute compute_backtested_pcs() / _backtest_all_signals(), since that
    code path is gated behind a button and never runs on a plain page load.
    """
    at = app_test("pages/8_About.py")
    btn = next((b for b in at.button if b.key == "run_pcs_backtest"), None)
    assert btn is not None, "Run Live Backtest button not found on About page"
    btn.click().run()
    assert not at.exception, (
        "Backtest button raised: " + "\n".join(str(e) for e in at.exception)
    )


def test_not_logged_in_path_renders_without_exception():
    """
    Every test above uses the app_test fixture, which injects a fake
    logged-in user into session_state BEFORE the first .run() -- meaning
    none of them ever exercise require_login()'s actual not-logged-in
    branch, the one that now also instantiates a CookieManager() for the
    "remember me" check (utils/auth_ui.py). This test runs app.py fresh,
    with no session_state injected at all, specifically to confirm that
    branch doesn't raise now that the cookie component is wired in.

    What this does NOT confirm: AppTest has no real browser attached, so
    cookies.ready() is always False here, and require_login() calls
    st.stop() immediately after that check -- this test only proves the
    script doesn't crash before reaching that point. It says nothing
    about whether a real "remember me" cookie round-trip works; that
    requires a live browser (see tests/conftest.py's module docstring).
    """
    from streamlit.testing.v1 import AppTest
    from tests.conftest import DASHBOARD_ROOT

    at = AppTest.from_file(str(DASHBOARD_ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, (
        "Not-logged-in path raised: " + "\n".join(str(e) for e in at.exception)
    )
