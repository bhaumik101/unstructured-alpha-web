"""
utils/accuracy.py — honest accuracy statistics for the prediction track record.

THE PROBLEM THIS FIXES
----------------------
A raw hit rate is not evidence. `3 of 3 correct` renders as "100.0%" and, sorted
by accuracy, outranks a signal that is 61% across 200 predictions — even though
the first is indistinguishable from luck and the second is a real edge.

For a product positioned on precision, publishing an unqualified percentage is
worse than publishing nothing: it invites a user to bet money on noise, and one
sophisticated reader checking the sample size destroys trust in every other
number on the page.

WHAT THIS ADDS
--------------
  • Wilson score confidence intervals — correct for small n and for proportions
    near 0/1, unlike the normal approximation which produces impossible bounds.
  • An explicit evidence tier driven by sample size.
  • A significance test against the directional baseline (~50%, a coin flip):
    a signal only "beats chance" when the LOWER bound of its interval clears it.
  • A ranking key that puts well-evidenced edges above small-sample flukes.

Pure standard library, no scipy — safe to import anywhere.
"""
from __future__ import annotations

import math

# Directional calls are bull/bear, so the naive baseline is a coin flip.
BASELINE = 0.50

# Sample-size tiers. Deliberately conservative: below MIN_REPORTABLE we refuse to
# publish a headline rate at all rather than dress up noise as a number.
MIN_REPORTABLE = 20
TIER_PRELIMINARY = 20
TIER_MODERATE = 50
TIER_STRONG = 100

TIER_INSUFFICIENT = "insufficient"
TIER_PRELIM = "preliminary"
TIER_MOD = "moderate"
TIER_STR = "strong"

TIER_LABELS = {
    TIER_INSUFFICIENT: "Insufficient evidence",
    TIER_PRELIM:       "Preliminary",
    TIER_MOD:          "Moderate evidence",
    TIER_STR:          "Strong evidence",
}


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Wilson score interval for a binomial proportion, as (lo, hi) in 0..1.

    Chosen over the normal approximation because at the sample sizes this product
    actually has (often <30 resolved predictions per signal) the normal interval
    is badly wrong and can extend below 0 or above 1. Returns (0.0, 1.0) — total
    ignorance — when there's no data, never a fake point estimate.
    """
    try:
        n = int(n)
        successes = int(successes)
        if n <= 0:
            return (0.0, 1.0)
        successes = max(0, min(successes, n))
        p = successes / n
        z2 = z * z
        denom = 1.0 + z2 / n
        center = (p + z2 / (2 * n)) / denom
        margin = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
        return (max(0.0, center - margin), min(1.0, center + margin))
    except Exception:
        return (0.0, 1.0)


def evidence_tier(n: int) -> str:
    """Sample-size tier. Sample size IS the headline caveat, so it's explicit."""
    try:
        n = int(n)
    except Exception:
        return TIER_INSUFFICIENT
    if n >= TIER_STRONG:
        return TIER_STR
    if n >= TIER_MODERATE:
        return TIER_MOD
    if n >= TIER_PRELIMINARY:
        return TIER_PRELIM
    return TIER_INSUFFICIENT


def summarize(correct: list, baseline: float = BASELINE) -> dict:
    """
    Turn a list of 1/0 outcomes into an honest, publishable summary.

    Returns:
        n            — resolved predictions
        hits         — number correct
        rate         — hit rate % (None when below MIN_REPORTABLE: we do not
                       publish a headline number we can't stand behind)
        raw_rate     — hit rate % regardless of sample size (for internal/debug)
        ci_low/high  — Wilson 95% interval, %
        tier         — evidence tier id
        tier_label   — human label
        beats_chance — True only if the interval's LOWER bound clears the
                       baseline. This is the honest "does it have skill?" test.
        verdict      — short plain-English readout
    """
    vals = []
    for v in (correct or []):
        try:
            if v is None:
                continue
            vals.append(1 if int(v) == 1 else 0)
        except Exception:
            continue

    n = len(vals)
    hits = sum(vals)
    lo, hi = wilson_interval(hits, n)
    tier = evidence_tier(n)
    raw_rate = round(100 * hits / n, 1) if n else None
    reportable = n >= MIN_REPORTABLE

    beats = bool(n and lo > baseline)
    worse = bool(n and hi < baseline)

    if not n:
        verdict = "No resolved predictions yet."
    elif not reportable:
        verdict = f"Only {n} resolved — too few to judge."
    elif beats:
        verdict = f"Beats chance ({raw_rate:.0f}% over {n})."
    elif worse:
        verdict = f"Worse than chance ({raw_rate:.0f}% over {n})."
    else:
        verdict = f"Not distinguishable from chance ({raw_rate:.0f}% over {n})."

    return {
        "n": n,
        "hits": hits,
        "rate": raw_rate if reportable else None,
        "raw_rate": raw_rate,
        "ci_low": round(100 * lo, 1) if n else None,
        "ci_high": round(100 * hi, 1) if n else None,
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "beats_chance": beats,
        "worse_than_chance": worse,
        "reportable": reportable,
        "verdict": verdict,
    }


def rank_key(summary: dict) -> tuple:
    """
    Sort key that ranks by EVIDENCE, not by raw percentage.

    Ordering: signals that beat chance first, then by the lower confidence bound
    (the conservative estimate of the edge), then by sample size. This is what
    stops `3/3 = 100%` outranking `122/200 = 61%` — the small sample has a lower
    bound near chance, so it sorts below.

    Use as: sorted(items, key=lambda r: rank_key(r["summary_12w"]))
    """
    try:
        return (
            0 if summary.get("beats_chance") else 1,
            -(summary.get("ci_low") or 0.0),
            -(summary.get("n") or 0),
        )
    except Exception:
        return (1, 0.0, 0)
