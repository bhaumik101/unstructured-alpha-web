# utils/model_version.py
# Unstructured Alpha — Scoring model versioning
#
# WHY THIS EXISTS: "Explain the Move" compares a ticker's Confluence Score at
# two points in time and attributes the change to specific signals/factors. That
# attribution is only honest if BOTH scores were produced by equivalent scoring
# logic. If the formula, the per-signal weighting scheme, or the signal→factor
# mapping changed between the two dates, part of the score movement is a MODEL
# change, not a market change — and the product must say so rather than present a
# clean macro attribution.
#
# This is deliberately lightweight: two short version strings stamped onto every
# component snapshot. Not an ML model registry.
#
# BUMP MODEL_VERSION whenever compute_full_ticker_score's math changes: the
# macro/momentum split (0.80/0.20), the optional-signal slice (0.12), the weight
# formula max(0.15,|r|)*(pcs/10), or the confluence blend. The signal-registry
# version below is derived automatically from the signal set + factor mapping, so
# adding/removing a signal or remapping a factor family changes it without a
# manual bump.

from __future__ import annotations

import hashlib

# Human-readable scoring-formula version. Bump on any change to the score math.
# Format: YYYY.MM.patch of the scoring logic (NOT the app release).
MODEL_VERSION: str = "2026.07.1"


def signal_registry_version() -> str:
    """
    A short, deterministic fingerprint of the signal universe + factor mapping.
    Changes automatically when a signal is added/removed or its factor family is
    remapped, so historical comparisons can detect a taxonomy/coverage shift even
    when MODEL_VERSION itself didn't move.

    Derived from the canonical taxonomy (utils.taxonomy.SIGNAL_FACTOR) so it stays
    in lockstep with the single source of truth for signal→factor mapping. Falls
    back to a stable sentinel if taxonomy can't be imported (keeps this module
    dependency-light and crash-proof).
    """
    try:
        from utils.taxonomy import SIGNAL_FACTOR
        # Sort so ordering never affects the hash; include the mapping so a
        # remap (not just add/remove) changes the fingerprint.
        payload = ";".join(f"{k}:{SIGNAL_FACTOR[k]}" for k in sorted(SIGNAL_FACTOR))
    except Exception:
        payload = "unknown-registry"
    return "sr_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8]


def model_fingerprint() -> dict:
    """Convenience: the full version stamp attached to a component snapshot."""
    return {
        "model_version": MODEL_VERSION,
        "signal_registry_version": signal_registry_version(),
    }
