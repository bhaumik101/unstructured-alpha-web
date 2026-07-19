"""Tests for utils.accuracy — the statistics that keep the track record honest."""
from utils import accuracy as acc


# ── Wilson interval ──────────────────────────────────────────────────────────
def test_wilson_matches_known_value():
    # 8/10 at 95%: Wilson is approximately (0.49, 0.94)
    lo, hi = acc.wilson_interval(8, 10)
    assert 0.44 < lo < 0.52
    assert 0.92 < hi < 0.97


def test_wilson_stays_within_bounds_at_extremes():
    # The normal approximation would go below 0 / above 1 here; Wilson must not.
    for succ, n in [(0, 5), (5, 5), (0, 1), (1, 1), (0, 100), (100, 100)]:
        lo, hi = acc.wilson_interval(succ, n)
        assert 0.0 <= lo <= hi <= 1.0


def test_wilson_narrows_as_sample_grows():
    w_small = acc.wilson_interval(6, 10)
    w_large = acc.wilson_interval(600, 1000)
    assert (w_large[1] - w_large[0]) < (w_small[1] - w_small[0])


def test_wilson_no_data_is_total_ignorance():
    assert acc.wilson_interval(0, 0) == (0.0, 1.0)
    assert acc.wilson_interval(5, 0) == (0.0, 1.0)


def test_wilson_never_raises():
    for a, b in [(None, None), ("x", "y"), (-5, 10), (50, 10)]:
        lo, hi = acc.wilson_interval(a, b)
        assert 0.0 <= lo <= hi <= 1.0


# ── evidence tiers ───────────────────────────────────────────────────────────
def test_evidence_tiers():
    assert acc.evidence_tier(0) == acc.TIER_INSUFFICIENT
    assert acc.evidence_tier(19) == acc.TIER_INSUFFICIENT
    assert acc.evidence_tier(20) == acc.TIER_PRELIM
    assert acc.evidence_tier(50) == acc.TIER_MOD
    assert acc.evidence_tier(100) == acc.TIER_STR
    assert acc.evidence_tier("junk") == acc.TIER_INSUFFICIENT


# ── the core honesty guarantees ──────────────────────────────────────────────
def test_small_sample_perfect_record_is_NOT_reportable():
    """3/3 = 100% must not be published as a headline rate."""
    s = acc.summarize([1, 1, 1])
    assert s["raw_rate"] == 100.0
    assert s["rate"] is None, "must refuse to publish a rate on n=3"
    assert s["reportable"] is False
    assert s["beats_chance"] is False, "3/3 cannot clear the baseline"
    assert s["tier"] == acc.TIER_INSUFFICIENT
    assert "too few" in s["verdict"]


def test_large_sample_real_edge_beats_chance():
    s = acc.summarize([1] * 122 + [0] * 78)      # 61% over 200
    assert s["rate"] == 61.0
    assert s["beats_chance"] is True
    assert s["ci_low"] > 50.0
    assert s["tier"] == acc.TIER_STR


def test_coin_flip_large_sample_is_not_skill():
    s = acc.summarize([1] * 100 + [0] * 100)     # exactly 50% over 200
    assert s["beats_chance"] is False
    assert "not distinguishable" in s["verdict"].lower()


def test_clearly_bad_signal_flagged_worse_than_chance():
    s = acc.summarize([1] * 40 + [0] * 160)      # 20% over 200
    assert s["worse_than_chance"] is True
    assert "worse than chance" in s["verdict"].lower()


def test_none_values_are_ignored_not_counted():
    s = acc.summarize([1, None, 0, None, 1])
    assert s["n"] == 3 and s["hits"] == 2


def test_empty_input():
    s = acc.summarize([])
    assert s["n"] == 0 and s["rate"] is None and s["beats_chance"] is False
    assert "No resolved" in s["verdict"]


def test_summarize_never_raises_on_junk():
    s = acc.summarize(["x", None, {}, 1])
    assert isinstance(s, dict) and s["n"] >= 0


# ── ranking: the actual bug this prevents ────────────────────────────────────
def test_ranking_puts_evidenced_edge_above_small_sample_fluke():
    fluke = acc.summarize([1, 1, 1])                       # 100% on n=3
    real = acc.summarize([1] * 122 + [0] * 78)             # 61% on n=200
    ranked = sorted([fluke, real], key=acc.rank_key)
    assert ranked[0] is real, "61% over 200 must outrank 100% over 3"


def test_ranking_prefers_larger_sample_at_similar_edge():
    small = acc.summarize([1] * 21 + [0] * 9)    # 70% over 30
    large = acc.summarize([1] * 140 + [0] * 60)  # 70% over 200
    ranked = sorted([small, large], key=acc.rank_key)
    assert ranked[0] is large
