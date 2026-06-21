"""
Shared fixtures for the Unstructured Alpha regression suite.

Run with:  pytest tests/  (from the dashboard/ directory)

These tests run fully offline-safe: pages that fetch live data (FRED, EIA,
yfinance) are expected to fall back to synthetic data or an empty Series
when network access is unavailable, and that fallback path itself is part
of what's under test — a page should never raise, even with zero network
access and zero API keys configured.

KNOWN BLIND SPOT — st.fragment bodies are NOT exercised by AppTest:
Confirmed empirically (not assumed) while wiring up live-price auto-refresh:
a real NameError inside an `@st.fragment(run_every=...)`-decorated function
(pages/5_Market_Overview.py's _render_live_index_quote, caused by a bad
import placement) did not surface during `at.run()` -- `at.exception` was
empty and none of the fragment's expected output appeared in `at.markdown`.
AppTest does not invoke fragment bodies at all; it only renders the parts of
the script that run unconditionally on a normal rerun. Every page test in
test_pages_render.py can pass cleanly while a fragment elsewhere on that same
page is silently broken. There is no test-suite-only fix for this (it is a
limitation of AppTest itself, not a gap in how these tests are written) --
any code living inside an st.fragment needs a live browser check before
trusting it, the same way it had to be caught here. Currently two fragments
exist in this codebase: Ticker Deep Dive's and Market Overview's live-price
auto-refresh. If you add another, verify it live; pytest passing is not
evidence it works.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make the dashboard root importable (tests/ is one level below it).
DASHBOARD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DASHBOARD_ROOT))
os.chdir(DASHBOARD_ROOT)

# Every AppTest-driven test runs the WHOLE app (app.py), which now calls
# utils.db.init_db() and gates every page behind a login -- point that at a
# throwaway file-based SQLite DB for the test session rather than the real
# local ~/.unstructured_alpha/data/app.db a developer might have data in,
# and rather than an in-memory DB (whose per-connection-pool semantics are
# less predictable across AppTest's script-execution model than a real,
# if temporary, file). Must be set before any test imports utils.db, since
# that module resolves its connection string once at import time.
_TEST_DB_FD, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="ua_test_")
os.environ["UNSTRUCTURED_ALPHA_DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

# Every routed page, exactly as registered in app.py's st.navigation() call.
# If this list and app.py drift apart, test_app_structure.py will fail loudly
# rather than silently testing the wrong set of pages.
ROUTED_PAGES = [
    "pages/home_page.py",
    "pages/1_Signal_Dashboard.py",
    "pages/3_Ticker_Deep_Dive.py",
    "pages/4_Power_Supercycle.py",
    "pages/5_Market_Overview.py",
    "pages/6_Stock_Screener.py",
    "pages/8_About.py",
    "pages/9_AI_Assistant.py",
    "pages/10_Alerts.py",
]

# pages/2_Signal_Analysis.py and pages/7_Macro_Monitor.py used to be kept
# around as harmless "this page moved" redirect stubs (consolidated into
# Ticker Deep Dive and Market Overview respectively) because an earlier
# sandbox environment couldn't delete files. They were genuinely deleted
# once a real filesystem could do it -- RETIRED_STUB_PAGES and its test no
# longer apply and were removed along with the files.


@pytest.fixture
def app_test():
    """
    Returns a factory that gives back a *freshly run* AppTest already
    switched to the requested page.

    Every page is now gated behind a login (utils.auth_ui.require_login()),
    so before the first .run(), this injects a fake logged-in user directly
    into session_state -- bypassing the actual login form, which is tested
    on its own terms in tests/test_auth_and_multitenancy_unit.py. Without
    this, every page-render test would just be testing the login screen.

    IMPORTANT: streamlit.testing.v1.AppTest.switch_page() does NOT
    automatically rerun the app — you must call .run() again after
    switching, or you're silently asserting against whatever page ran
    last (usually the home page), not the one you think you're testing.
    This bit us once already; this fixture exists specifically so no
    test can make that mistake again.
    """
    from streamlit.testing.v1 import AppTest

    def _make(page_path: str = None, timeout: int = 120):
        at = AppTest.from_file(str(DASHBOARD_ROOT / "app.py"), default_timeout=timeout)
        at.session_state["user"] = {"id": 1, "email": "test@example.com"}
        at.run()
        if page_path:
            at.switch_page(page_path)
            at.run()
        return at

    return _make
