from __future__ import annotations

import pandas as pd

from utils.score_cache import (
    FullScoreCache,
    canonical_signal_ids,
    get_session_result,
    make_full_score_cache_key,
    set_session_result,
)


def _key(ticker="AAPL", signals=("vix", "yield_curve"), optional=True,
         model="2026.07.1", now=1_800_000_000):
    return make_full_score_cache_key(
        ticker, signals, optional, now=now, model_version=model, registry_version="sr_test"
    )


def test_same_ticker_and_canonical_signal_tuple_is_cached():
    cache = FullScoreCache(max_entries=4)
    calls = []
    first, first_status = cache.get_or_compute(
        _key(signals=("vix", "yield_curve")), lambda: calls.append(1) or {"value": 1}
    )
    second, second_status = cache.get_or_compute(
        _key(signals=("yield_curve", "vix", "vix")), lambda: calls.append(2) or {"value": 2}
    )
    assert first == second == {"value": 1}
    assert (first_status, second_status) == ("miss", "hit")
    assert calls == [1]


def test_ticker_signal_model_and_optional_changes_are_cache_misses():
    cache = FullScoreCache(max_entries=8)
    keys = [
        _key("AAPL"),
        _key("NVDA"),
        _key("AAPL", signals=("vix",)),
        _key("AAPL", optional=False),
        _key("AAPL", model="2026.08.0"),
    ]
    statuses = [cache.get_or_compute(key, lambda i=i: {"value": i})[1] for i, key in enumerate(keys)]
    assert statuses == ["miss"] * len(keys)
    assert len(cache) == len(keys)


def test_none_and_explicit_empty_signal_sets_never_collide():
    assert canonical_signal_ids(None) == ("auto", ())
    assert canonical_signal_ids([]) == ("explicit", ())
    assert make_full_score_cache_key("AAPL", None, True, now=0) != make_full_score_cache_key(
        "AAPL", [], True, now=0
    )


def test_targeted_refresh_clears_only_intended_result():
    cache = FullScoreCache(max_entries=8)
    intended = _key("AAPL", ("vix",))
    other_signals = _key("AAPL", ("yield_curve",))
    other_ticker = _key("NVDA", ("vix",))
    for key in (intended, other_signals, other_ticker):
        cache.get_or_compute(key, lambda key=key: {"key": key})

    assert cache.clear_result("AAPL", ("vix",), True) == 1
    assert cache.get_or_compute(intended, lambda: {"new": True})[1] == "miss"
    assert cache.get_or_compute(other_signals, lambda: {"new": True})[1] == "hit"
    assert cache.get_or_compute(other_ticker, lambda: {"new": True})[1] == "hit"


def test_segmented_control_state_change_reuses_session_object():
    state = {"section": "Overview"}
    key = _key()
    result = {"large": object()}
    set_session_result(state, key, result)
    state["section"] = "Deep Correlation Scan"
    assert get_session_result(state, key) is result


def test_provisional_results_are_not_cached():
    cache = FullScoreCache(max_entries=4)
    calls = []
    key = _key()
    first = cache.get_or_compute(
        key, lambda: calls.append(1) or {"is_complete": False, "score_kind": "provisional"}
    )
    second = cache.get_or_compute(
        key, lambda: calls.append(2) or {"is_complete": True, "score_kind": "full"}
    )
    assert first[1] == "miss_degraded"
    assert second[1] == "miss"
    assert calls == [1, 2]


def test_complete_and_macro_only_results_have_distinct_keys():
    full = _key(optional=True)
    macro = _key(optional=False)
    assert full != macro


def test_optional_source_failure_is_explicitly_provisional(monkeypatch):
    import utils.ticker_score as scoring

    unavailable = pd.DataFrame()
    unavailable.attrs["fetch_error"] = True
    monkeypatch.setattr(scoring, "fetch_federal_contracts", lambda *a, **k: unavailable)
    monkeypatch.setattr(scoring, "fetch_insider_transactions_detail", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(scoring, "fetch_short_interest", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(scoring, "fetch_13f_holdings", lambda *a, **k: pd.DataFrame())

    prices = pd.Series(
        range(1, 31), index=pd.date_range("2026-01-01", periods=30), dtype=float
    )
    result = scoring.compute_full_ticker_score(
        "AAPL", signal_ids=[], price_series=prices, include_optional=True
    )
    assert result["is_complete"] is False
    assert result["score_kind"] == "provisional"
    assert result["source_errors"] == ["federal_contracts"]
