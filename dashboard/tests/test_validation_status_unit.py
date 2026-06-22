"""
Unit tests for utils/validation_status.py -- the Model Validation
Dashboard's data layer. Per the explicit standard set for this feature
("don't add anything unless it is absolutely perfect and flawless"),
these tests check more than "doesn't crash": they verify the actual
disclosed numbers are word-for-word what the real source docstrings say,
that every signal always gets an entry (even on fetch failure), and that
nothing here silently overstates validation status.
"""

import re

import pandas as pd
import pytest

from utils import analysis
from utils.config import SIGNALS
from utils.validation_status import backtest_all_macro_signals, get_static_validation_summary


def _normalize_whitespace(text: str) -> str:
    """Docstrings wrap across lines for readability; collapse any run of
    whitespace (including newlines) to a single space before comparing
    fragments, so a harmless line-wrap doesn't register as a content
    mismatch."""
    return re.sub(r"\s+", " ", text).strip()


# ── get_static_validation_summary() ──────────────────────────────────────────

def test_returns_exactly_five_categories():
    summary = get_static_validation_summary()
    categories = {entry["category"] for entry in summary}
    assert len(summary) == 5
    assert categories == {
        "Confluence Score (per-ticker macro composite)",
        "Power Supercycle Score",
        "Insider Activity (Form 4 open-market buys/sells)",
        "Short Interest (FINRA consolidated)",
        "13F Institutional Positioning",
    }


def test_every_entry_has_required_fields_nonempty():
    for entry in get_static_validation_summary():
        for field in ("category", "status", "detail", "source"):
            assert entry.get(field), f"{entry.get('category')} missing or empty '{field}'"


def test_supercycle_backtest_numbers_match_source_docstring_verbatim():
    """
    The single most important test in this file: the Power Supercycle
    entry's disclosed backtest result must be word-for-word what
    compute_supercycle_score()'s actual docstring says RIGHT NOW, not a
    paraphrase that could quietly drift out of sync if the docstring is
    ever updated after a re-backtest. Reads the live docstring directly
    rather than hard-coding the expected text twice.
    """
    summary = get_static_validation_summary()
    supercycle = next(e for e in summary if e["category"] == "Power Supercycle Score")
    docstring = _normalize_whitespace(analysis.compute_supercycle_score.__doc__)
    detail = _normalize_whitespace(supercycle["detail"])

    # The specific, checkable numbers -- if a future re-backtest changes
    # these, this test should fail until validation_status.py is updated
    # to match, not the other way around.
    for fragment in ("all |r| < 0.07", "p > 0.5 pooled", "CEG, VST, NEE, ETN, VRT, PWR"):
        assert fragment in docstring, f"Expected fragment not found in current docstring: {fragment!r}"
        assert fragment in detail, (
            f"validation_status.py's claim has drifted from the source docstring: {fragment!r}"
        )


def test_confluence_backtest_numbers_match_source_docstring_verbatim():
    summary = get_static_validation_summary()
    confluence = next(e for e in summary if e["category"] == "Confluence Score (per-ticker macro composite)")
    docstring = _normalize_whitespace(analysis.compute_confluence.__doc__)
    detail = _normalize_whitespace(confluence["detail"])

    for fragment in ("pooled across 6 tickers", "it does not yet mean they're right"):
        assert fragment in docstring, f"Expected fragment not found in current docstring: {fragment!r}"
        assert fragment in detail, (
            f"validation_status.py's claim has drifted from the source docstring: {fragment!r}"
        )


def test_status_labels_never_overclaim_validation():
    """
    Confluence and Supercycle must NEVER be labeled as "validated" --
    their own backtests found no significant relationship. Insider/Short
    Interest must be framed as per-ticker/on-demand, never as a single
    blanket "validated" claim (that would overstate what a methodology
    being AVAILABLE means vs. a specific ticker actually having been
    tested and held up).
    """
    summary = get_static_validation_summary()
    for entry in summary:
        if "Confluence" in entry["category"] or "Supercycle" in entry["category"]:
            assert "NOT validated" in entry["status"]
            assert entry["status"] != "Validated"
        if "Insider" in entry["category"] or "Short Interest" in entry["category"]:
            assert "on demand" in entry["status"].lower()
            assert entry["status"] != "Validated"


# ── backtest_all_macro_signals() ─────────────────────────────────────────────

def test_backtest_returns_an_entry_for_every_signal(monkeypatch):
    """
    Every signal must get a result dict, even ones whose fetch fails --
    the Model Validation Dashboard's "N of M validated" count depends on
    every signal being represented, not silently dropped on error.
    """
    # Force every fetch to fail, to exercise the except-path for ALL
    # signals deterministically rather than relying on whichever ones
    # happen to fail due to no network access in this environment.
    monkeypatch.setattr(
        "utils.validation_status.fetch_signal_series",
        lambda cfg, start, end: (_ for _ in ()).throw(RuntimeError("no network")),
    )
    backtest_all_macro_signals.clear()  # bypass the 24h cache for this test
    results = backtest_all_macro_signals()

    assert set(results.keys()) == set(SIGNALS.keys())
    for sig_id, result in results.items():
        assert result["backtested"] is False, f"{sig_id} should not claim backtested on a forced failure"
        assert result["pcs"] is None


def test_backtest_result_shape_is_consistent_on_failure(monkeypatch):
    monkeypatch.setattr(
        "utils.validation_status.fetch_signal_series",
        lambda cfg, start, end: (_ for _ in ()).throw(RuntimeError("no network")),
    )
    backtest_all_macro_signals.clear()
    results = backtest_all_macro_signals()

    first = next(iter(results.values()))
    expected_keys = {"pcs", "backtested", "n_tested", "significance_rate", "avg_abs_r", "details"}
    assert set(first.keys()) == expected_keys
