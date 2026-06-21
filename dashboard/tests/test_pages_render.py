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
