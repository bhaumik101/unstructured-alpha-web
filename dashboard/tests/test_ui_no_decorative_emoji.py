"""Guard the institutional-UI standard: no decorative emoji in navigation.

The product is positioned as a credible financial-research tool, and decorative
emoji in tab labels, expander headers, and section titles read as consumer-app
novelty rather than institutional. This test locks in the cleanup for the
logic-safe navigation surface so a new page cannot quietly reintroduce it.

Deliberately SCOPED to display-only, logic-safe call patterns:
  st.tabs, st.expander, st.subheader/header, and markdown section headers.

It intentionally does NOT police:
  - st.radio / st.selectbox options — those strings are often the RETURN VALUE
    the page compares against downstream, so stripping an emoji there can change
    behaviour, not just appearance.
  - directional/data glyphs (arrows, the neutral/excluded marks) — those
    communicate data and are explicitly allowed.
  - inline HTML built with st.markdown(unsafe_allow_html=True) — too broad to
    assert safely here; handled case by case.

Scope can widen later, but only where a change is provably display-only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PAGES = Path(__file__).resolve().parent.parent / "pages"

# Emoji / pictographic ranges. Excludes the arrow and geometric-shape glyphs the
# product uses to communicate direction and signal state.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\U0001F900-\U0001F9FF\U0000FE0F]"
)
_ALLOWED = set("▲▼△▽↑↓→←⊘")

# Display-only call patterns this test governs.
_GOVERNED = re.compile(
    r'st\.tabs\(|st\.expander\(|st\.subheader\(|st\.header\('
    r'|st\.markdown\(\s*["\']#{1,6}\s'
)


def _rendered_emoji(line: str) -> list[str]:
    return [c for c in _EMOJI.findall(line) if c not in _ALLOWED]


def _active_pages() -> list[Path]:
    # pages/retired/ is not routable; scope to active pages only.
    return sorted(PAGES.glob("*.py"))


def test_no_decorative_emoji_in_governed_navigation():
    offenders = []
    for path in _active_pages():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not _GOVERNED.search(line):
                continue
            found = _rendered_emoji(line)
            if found:
                offenders.append(f"{path.name}:{i} {''.join(found)}  {line.strip()[:70]}")
    assert not offenders, (
        "decorative emoji found in tab/expander/section-header labels — the "
        "institutional-UI standard forbids them in navigation. Remove or, if the "
        "glyph communicates data, confirm it is in the allowed set.\n  "
        + "\n  ".join(offenders)
    )


def test_governed_pattern_actually_matches_something():
    """Guard against the regex silently matching nothing (a vacuous pass)."""
    hits = 0
    for path in _active_pages():
        for line in path.read_text(encoding="utf-8").splitlines():
            if _GOVERNED.search(line):
                hits += 1
    assert hits > 20, (
        f"only {hits} governed lines found; the detector may be broken and the "
        "emoji test would then pass vacuously"
    )


@pytest.mark.parametrize("sample", [
    'st.tabs(["Signal Dashboard", "Regime Playbook"])',
    'with st.expander("Past issues"):',
    'st.markdown("### Top-Line KPIs")',
])
def test_clean_labels_pass(sample):
    assert not _rendered_emoji(sample)


@pytest.mark.parametrize("sample", [
    'st.tabs(["\U0001F4E1 Signal Dashboard"])',
    'st.markdown("### \U0001F4B0 Revenue")',
])
def test_dirty_labels_are_detected(sample):
    assert _GOVERNED.search(sample) and _rendered_emoji(sample)
