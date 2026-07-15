"""
Explain the Move — SIDE QUEST SUCCESS TEST (wave 5).

Encodes the spec's exact acceptance scenarios so they can never silently regress:
a high-coverage ticker must satisfy all 7 "within 5 seconds" criteria, and the
limited-coverage / no-snapshot / signal-unavailable / mobile states must each be
honest and safe. Pure engine — no config/DB stubs needed.
"""
import re
from utils import score_attribution as sa


def _s(sid, fac, fn, sc, nw, c, av=True, rawv=None, asof=None):
    return {"id": sid, "name": fn, "score": sc, "norm_weight": nw, "contribution": c,
            "factor": fac, "factor_name": fn, "available": av, "significant": True,
            "weight": nw, "r": 0.3, "raw_value": rawv, "as_of": asof}


def _comp(final, sigs, na=None, gen=True, mv="2026.07.1", reg="sr_a"):
    return {"ticker": "NVDA", "final_score": final, "reconstructed_score": final,
            "signals": sigs, "components": [],
            "coverage": {"n_available": na if na is not None else len(sigs),
                         "tier": "moderate", "generates_score": gen},
            "model_version": mv, "signal_registry_version": reg}


def test_high_coverage_satisfies_all_seven_success_points():
    A = _comp(69.0, [_s("ten_year_yield", "rates", "Real Rates", 70, .24, 20.0, rawv=2.3, asof="2026-07-07"),
                     _s("yield_curve", "rates", "Real Rates", 60, .10, 8.0, rawv=0.4, asof="2026-07-07"),
                     _s("net_liquidity", "liquidity", "Liquidity", 65, .20, 16.0),
                     _s("hyperscaler_capex", "capex_tech", "AI Infrastructure", 68, .18, 15.0),
                     _s("hy_spread", "credit", "Credit", 40, .10, 10.0)])
    B = _comp(54.0, [_s("ten_year_yield", "rates", "Real Rates", 40, .24, 11.9, rawv=1.9, asof="2026-07-13"),
                     _s("yield_curve", "rates", "Real Rates", 42, .10, 5.2, rawv=0.1, asof="2026-07-13"),
                     _s("net_liquidity", "liquidity", "Liquidity", 47, .20, 11.6),
                     _s("hyperscaler_capex", "capex_tech", "AI Infrastructure", 60, .18, 12.9),
                     _s("hy_spread", "credit", "Credit", 45, .10, 12.4)])
    a = sa.attribute_move(A, B, window_label="this week")
    h = sa.render_attribution_html(a)
    assert a["state"] == "ok" and abs(a["reconciliation_delta"]) < 0.05
    assert a["total_change"] != 0                                    # 1 how much
    assert a["window_label"]                                         # 2 period
    assert len([f for f in a["factors"] if f["direction"] == "down"]) >= 2   # 3 two drivers
    assert a["pos_total"] != 0                                       # 4 offset
    assert "n_available" in a["coverage"]                            # 5 coverage
    assert "model_changed" in a                                      # 6 methodology flag
    assert "Why it matters" in h and "raw 2.3" in h and "updated 2026-07-13" in h  # 7 signal detail


def test_limited_coverage_is_honest():
    a = sa.attribute_move(_comp(50.0, [_s("retail_sales", "consumer", "Consumer", 60, 1.0, 50.0)], na=1),
                          _comp(45.8, [_s("retail_sales", "consumer", "Consumer", 47, 1.0, 45.8)], na=1))
    assert a["state"] == "insufficient_coverage" and "limited" in a["summary"].lower()


def test_no_snapshot_is_honest():
    B = _comp(54.0, [_s("s1", "rates", "Real Rates", 40, 1.0, 54.0)])
    assert sa.attribute_move(None, B)["state"] == "no_comparison"


def test_signal_unavailable_classified():
    d = sa.attribute_move(_comp(20.0, [_s("s1", "rates", "Real Rates", 60, .5, 20.0, av=True)]),
                          _comp(15.0, [_s("s1", "rates", "Real Rates", 50, .5, 15.0, av=False)]))
    assert d["factors"][0]["signals"][0]["cause"] == "DATA_LOSS"


def test_render_is_mobile_safe():
    A = _comp(60.0, [_s("s1", "rates", "Real Rates", 60, .5, 30.0), _s("s2", "credit", "Credit", 60, .5, 30.0)])
    B = _comp(46.0, [_s("s1", "rates", "Real Rates", 40, .5, 20.0), _s("s2", "credit", "Credit", 52, .5, 26.0)])
    h = sa.render_attribution_html(sa.attribute_move(A, B))
    assert not re.findall(r"width:\s*\d{3,}px|min-width:\s*\d{3,}px|<table", h)
    assert "NaN" not in h and h.count("<div") == h.count("</div")
