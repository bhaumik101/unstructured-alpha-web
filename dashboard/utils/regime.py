"""Single source of truth for the macro-regime read.

Before this module the regime was computed independently in at least two places
that had drifted: the sticky header bar (utils/header.py, off persisted
snapshots) and the home hero "LIVE MACRO READ" (pages/home_page.py, off the live
2h cache). On 2026-07-23 the landing page showed BOTH at once with different
numbers — header up14 down8 flat22 excl3 vs hero 15/8/20 — which, for a product
whose entire pitch is data trust, is the most damaging possible bug: a
knowledgeable visitor sees two contradictory macro reads above the fold.

Root causes were two: different DATA SOURCES (snapshots vs live cache) and
different COMPUTATION (each site rolled its own count + label thresholds). This
module fixes the computation half — one function, one set of thresholds — and
callers fix the data half by feeding it the SAME source. The header must be
cheap on every page, so the canonical source is the persisted snapshot
(score_history.get_latest_signal_states); the home hero now reads the same.

A grep found ~28 sites independently classifying bull/bear/neutral. Migrating
the two regime HEADLINE surfaces (header + hero) removes the visible
contradiction; the rest can adopt this incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from utils.config import SIGNAL_COUNT as _SIGNAL_COUNT
except Exception:  # pragma: no cover - config always importable in app
    _SIGNAL_COUNT = 47


# Label thresholds, lifted verbatim from the header bar so behaviour is
# unchanged. Expressed against the BULLISH / BEARISH share of *scored* signals.
_RISK_ON_BULL = 0.58
_RISK_OFF_BEAR = 0.52
_LEAN_BULL = 0.48
_LEAN_BEAR = 0.44


@dataclass(frozen=True)
class Regime:
    bullish: int
    bearish: int
    neutral: int
    scored: int
    excluded: int
    total: int
    bull_pct: float          # of scored, 0..1
    bear_pct: float          # of scored, 0..1
    label: str
    color: str
    bg: str

    @property
    def bull_pct_display(self) -> int:
        return round(self.bull_pct * 100)

    @property
    def bear_pct_display(self) -> int:
        return round(self.bear_pct * 100)


def _label(bull_pct: float, bear_pct: float, has_data: bool) -> tuple[str, str, str]:
    if not has_data:
        return "AWAITING SNAPSHOT", "#8F9AAD", "rgba(143,154,173,0.05)"
    if bull_pct >= _RISK_ON_BULL:
        return "RISK-ON", "#00D566", "rgba(0,213,102,0.06)"
    if bear_pct >= _RISK_OFF_BEAR:
        return "RISK-OFF", "#FF4444", "rgba(255,68,68,0.06)"
    if bull_pct >= _LEAN_BULL:
        return "LEANING BULLISH", "#00A847", "rgba(0,168,71,0.05)"
    if bear_pct >= _LEAN_BEAR:
        return "LEANING BEARISH", "#CC3333", "rgba(204,51,51,0.05)"
    return "MIXED SIGNALS", "#6B7FBF", "rgba(107,127,191,0.05)"


def compute_macro_regime(signals: dict | None, total: int | None = None) -> Regime:
    """Classify a signals dict into one canonical regime read.

    `signals` maps signal_id -> {"status": "bullish|bearish|neutral", "error": ...}.
    Accepts either the snapshot shape (get_latest_signal_states) or the live
    cache shape (get_all_signal_scores) — both carry `status` and an error flag.

    `excluded` is total - scored, so the numbers ALWAYS reconcile to the
    advertised SIGNAL_COUNT rather than silently dropping the signals that
    failed to load this cycle. This is the invariant that was broken on the
    landing page (bar showed excl3 while the banner said 4).
    """
    total = int(total if total is not None else _SIGNAL_COUNT)
    signals = signals or {}

    def _ok(v) -> bool:
        return isinstance(v, dict) and not v.get("error")

    bullish = sum(1 for v in signals.values() if _ok(v) and v.get("status") == "bullish")
    bearish = sum(1 for v in signals.values() if _ok(v) and v.get("status") == "bearish")
    neutral = sum(1 for v in signals.values() if _ok(v) and v.get("status") == "neutral")
    scored = bullish + bearish + neutral
    excluded = max(0, total - scored)

    denom = max(1, scored)
    bull_pct = bullish / denom
    bear_pct = bearish / denom
    label, color, bg = _label(bull_pct, bear_pct, has_data=scored > 0)

    return Regime(
        bullish=bullish, bearish=bearish, neutral=neutral,
        scored=scored, excluded=excluded, total=total,
        bull_pct=bull_pct, bear_pct=bear_pct,
        label=label, color=color, bg=bg,
    )
