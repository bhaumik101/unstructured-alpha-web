"""Tests for the slow-operation timing helper.

The point of utils.observability.timed is that a slow production operation
(e.g. the 47-signal provider sweep degrading to 5s) becomes a greppable,
attributable log line instead of an invisible "the site feels slow". These tests
pin: it logs when slow, stays quiet when fast, never swallows the block's
exception, and still flags a slow FAILURE.
"""

from __future__ import annotations

import logging
import time

import pytest

from utils.observability import timed


def _capture(monkeypatch):
    events = []
    import utils.observability as obs
    monkeypatch.setattr(obs, "log_event",
                        lambda event, level=logging.INFO, **f: events.append((event, level, f)))
    return events


def test_slow_operation_is_logged(monkeypatch):
    events = _capture(monkeypatch)
    with timed("unit_slow", threshold_ms=0):   # threshold 0 => always "slow"
        pass
    assert events, "a slow operation must log"
    name, level, fields = events[0]
    assert name == "slow_operation"
    assert level == logging.WARNING
    assert fields["operation"] == "unit_slow"
    assert "ms" in fields and fields["ms"] >= 0


def test_fast_operation_is_silent_by_default(monkeypatch):
    events = _capture(monkeypatch)
    with timed("unit_fast", threshold_ms=10_000):  # nothing here takes 10s
        pass
    assert events == [], "a fast operation must not log (keeps the signal clean)"


def test_exception_propagates_and_is_flagged(monkeypatch):
    events = _capture(monkeypatch)
    with pytest.raises(ValueError):
        with timed("unit_boom", threshold_ms=10_000):
            raise ValueError("boom")
    # even though it was fast, a failure is logged (a slow/broken op must be visible)
    assert events, "a failing operation must be logged even under the threshold"
    assert events[0][2]["errored"] is True


def test_timing_never_raises_from_logging(monkeypatch):
    """If log_event itself blows up, timed must NOT break the wrapped block —
    observability is best-effort and can never turn a slow op into a crash."""
    import utils.observability as obs
    monkeypatch.setattr(obs, "log_event",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("log down")))
    # The block succeeds; a throwing logger in the finally must be swallowed.
    ran = []
    with timed("x", threshold_ms=0):
        ran.append(True)
    assert ran == [True]  # completed cleanly despite the broken logger


def test_fields_are_passed_through(monkeypatch):
    events = _capture(monkeypatch)
    with timed("with_fields", threshold_ms=0, ticker="NVDA", n=47):
        pass
    fields = events[0][2]
    assert fields["ticker"] == "NVDA" and fields["n"] == 47


def test_signals_cache_wraps_the_sweep():
    """The 47-signal cold sweep must be wrapped so a slow provider is visible."""
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "utils" / "signals_cache.py").read_text()
    assert 'timed("get_all_signal_scores"' in src or "timed(\"get_all_signal_scores\"" in src \
        or "get_all_signal_scores" in src and "_timed(" in src
