"""Curated, genuinely-true macro fun facts for loading screens.

Single source of truth for both the build-time boot splash
(scripts/inject_boot_splash.py imports FACTS from here and inlines them as a JS
array) and the in-app loading splash (utils/theme.loading_splash). Keeping one
list prevents the two surfaces drifting apart.

Editorial rule, enforced by tests: every entry must be a TRUE, verifiable
statement about macroeconomics or markets. This product's whole positioning is
that it does not present fiction as fact — a loading screen is no exception. No
performance claims, no predictions, no "our signal did X". Just real, checkable
context a macro-curious reader would enjoy. Keep each to one line.
"""

from __future__ import annotations

import random

FACTS: tuple[str, ...] = (
    "An inverted yield curve — short rates above long rates — has preceded "
    "every U.S. recession of the past half-century.",

    "The Sahm Rule flags a downturn when the 3-month average unemployment rate "
    "rises half a point above its trailing 12-month low.",

    "Copper is nicknamed “Dr. Copper” for its long record of "
    "anticipating turns in the global economy.",

    "Initial jobless claims are one of the ten components of the Conference "
    "Board's Leading Economic Index.",

    "The Baltic Dry Index tracks the cost of shipping dry-bulk raw materials — "
    "a real-time read on global trade demand.",

    "A manufacturing PMI above 50 signals expansion; below 50 signals "
    "contraction.",

    "Building permits lead housing starts, which in turn lead residential "
    "construction activity.",

    "The VIX, Wall Street's “fear gauge,” infers expected 30-day S&P "
    "500 volatility from options prices.",

    "The EIA reports U.S. crude oil and gasoline inventories every week, "
    "typically on Wednesdays.",

    "The University of Michigan has surveyed U.S. consumer sentiment since the "
    "1940s.",

    "M2 — cash plus deposits and near-money — is a monetary aggregate the "
    "Federal Reserve tracks closely.",

    "Yield-curve inversions have historically led downturns by roughly 6 to 18 "
    "months, not immediately.",

    "Real yields — nominal Treasury yields minus expected inflation — tend to "
    "drive gold more than nominal rates do.",

    "Credit spreads, the extra yield on corporate over government bonds, tend "
    "to widen before recessions as default risk is repriced.",

    "A “soft landing” describes cooling inflation without tipping the "
    "economy into recession.",
)


def random_fact(rng: random.Random | None = None) -> str:
    """Return one fact at random. Accepts an injectable RNG for deterministic tests."""
    return (rng or random).choice(FACTS)


def all_facts() -> tuple[str, ...]:
    return FACTS
