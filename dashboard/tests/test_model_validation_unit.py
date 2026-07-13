"""
Unit tests for utils/model_validation.py — the Model Validation Center engine
(Point 9). HERMETIC: stubs utils.config so the confidence/validation labelling
is validated against hand-derived ground truth (no DB, no network).
"""

import sys
import types

import pytest

_stub = types.ModuleType("utils.config")
_stub.CATEGORIES = {"macro": {"name": "Macro & Liquidity"}, "financials": {"name": "Financials & Credit"}}
_stub.SIGNALS = {
    "ata_trucking": {"tier": 1, "pcs": 9, "source": "fred", "series_id": "TRUCKD11",
                     "frequency": "monthly", "lag_weeks": 6, "name": "ATA Trucking",
                     "category": "macro", "source_url": "https://x"},
    "hy_spread": {"tier": 1, "pcs": 8, "source": "fred", "frequency": "weekly",
                  "lag_weeks": 2, "name": "High-Yield Spread", "category": "financials"},
    "vix": {"tier": 2, "pcs": 6, "source": "cboe", "frequency": "daily", "name": "VIX", "category": "macro"},
    "retail_fear_gauge": {"tier": 3, "pcs": 3, "source": "internal", "frequency": "daily",
                          "name": "Retail Fear Gauge", "category": "macro"},
}
sys.modules.setdefault("utils.config", _stub)

from utils import model_validation as mv  # noqa: E402
from utils.config import SIGNALS          # noqa: E402


def test_core_tier1_record():
    r = mv.signal_validation_record("ata_trucking", SIGNALS["ata_trucking"])
    assert r["weight_label"] == "Core"
    # tier-1 with no measured reliability is capped at Moderate — never overclaims
    assert r["confidence"] == "Moderate"
    assert r["experimental"] is False
    assert "not yet out-of-sample" in r["validation_status"]
    assert "monthly" in r["known_limitation"]
    assert r["source"] == "FRED"


def test_experimental_tier3_record():
    r = mv.signal_validation_record("retail_fear_gauge", SIGNALS["retail_fear_gauge"])
    assert r["weight_label"] == "Experimental"
    assert r["confidence"] == "Limited"
    assert r["experimental"] is True
    assert "Experimental" in r["validation_status"]
    assert "regimes" in r["known_limitation"]


def test_measured_reliability_overrides():
    hi = mv.signal_validation_record("ata_trucking", SIGNALS["ata_trucking"],
                                     reliability={"score": 75, "label": "Reliable"})
    assert hi["confidence"] == "High"
    assert hi["validation_status"] == "Reliable"
    lo = mv.signal_validation_record("ata_trucking", SIGNALS["ata_trucking"], reliability={"score": 30})
    assert lo["confidence"] == "Limited"


def test_table_sorting_and_wrapper():
    recs = mv.build_validation_table(SIGNALS)
    ids = [r["id"] for r in recs]
    assert ids[0] == "ata_trucking" and ids[1] == "hy_spread"      # Core, pcs desc
    assert ids.index("vix") < ids.index("retail_fear_gauge")       # Supporting before Experimental
    assert ids[-1] == "retail_fear_gauge"
    # reliabilities passed as the validate_all_macro_signals wrapper shape
    recs2 = mv.build_validation_table(SIGNALS, reliabilities={"ata_trucking": {"reliability": {"score": 80}}})
    ata = next(r for r in recs2 if r["id"] == "ata_trucking")
    assert ata["confidence"] == "High"


def test_summary_and_render():
    recs = mv.build_validation_table(SIGNALS)
    s = mv.validation_summary(recs)
    assert s["total"] == 4 and s["core"] == 2 and s["supporting"] == 1
    assert s["experimental"] == 1 and s["limited_confidence"] == 1
    assert "Model Validation Center" in mv.render_summary_html(s)
    comps = [{"category": "Confluence Score", "status": "Backtested — NOT validated",
              "detail": "no significant relationship", "source": "analysis.py"}]
    hc = mv.render_composites_html(comps)
    assert "Confluence Score" in hc and "NOT validated" in hc
    assert hc.count("<div") >= hc.count("</div")
