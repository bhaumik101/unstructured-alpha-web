"""Every routed page must be render-tested — no page can slip the net.

test_pages_render.py parametrizes over ROUTED_PAGES (a hand-maintained list in
conftest) and asserts each renders without exception. That guarantee is only as
good as the list: add a page to app.py's st.navigation() and forget conftest,
and a brand-new feature ships with zero render coverage. This test makes the two
lists prove they agree, so "every feature works" stays true as pages are added.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.conftest import ROUTED_PAGES

DASHBOARD = Path(__file__).resolve().parent.parent


def _pages_registered_in_app() -> set[str]:
    """Extract every st.Page("pages/...") path from the real router."""
    app = (DASHBOARD / "app.py").read_text(encoding="utf-8")
    return set(re.findall(r'st\.Page\(\s*["\'](pages/[^"\']+\.py)["\']', app))


def test_routed_pages_matches_the_actual_router():
    registered = _pages_registered_in_app()
    listed = set(ROUTED_PAGES)

    missing_from_tests = registered - listed
    stale_in_tests = listed - registered

    assert not missing_from_tests, (
        "these pages are in app.py's st.navigation() but NOT in conftest "
        "ROUTED_PAGES, so they get no render coverage — add them:\n  "
        + "\n  ".join(sorted(missing_from_tests))
    )
    assert not stale_in_tests, (
        "these pages are render-tested but no longer registered in app.py "
        "(retired?) — remove them from ROUTED_PAGES:\n  "
        + "\n  ".join(sorted(stale_in_tests))
    )


def test_every_routed_page_file_exists():
    for p in ROUTED_PAGES:
        assert (DASHBOARD / p).exists(), f"routed page file missing: {p}"


def test_router_has_a_plausible_page_count():
    """Guard against the regex silently matching nothing."""
    assert len(_pages_registered_in_app()) >= 25
