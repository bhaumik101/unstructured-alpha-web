"""Guards that stop a backtest from overstating what it knows.

The Portfolio Suite backtest runs on `score_snapshots`, which at the time of
writing held 43 rows across 25 tickers spanning under four weeks. Three
separate problems followed from that, none of which announced themselves:

1. **Annualisation.** CAGR is `(1 + total_return) ** (1 / years) - 1`. Over a
   28-day sample `years` is 0.077, so the exponent is ~13 and a 5% gain renders
   as +87% CAGR — displayed beside SPY as though comparable. Sharpe over ~20
   daily observations has a standard error near 0.22, so a printed 1.5 is not
   distinguishable from 1.1 or 1.9.

2. **Look-ahead.** Positions were selected with
   `get_indexer([rebalance_date], method="nearest")`, which resolves to the
   closest snapshot in *either* direction. When the nearest snapshot postdated
   the rebalance, the backtest picked holdings using a score that did not exist
   yet, while the page captioned the result "genuinely out-of-sample".

3. **Costs.** A weekly-rebalanced long/short book paying nothing in spread,
   commission or borrow is not a strategy anyone can run.

Nothing here makes a short sample trustworthy. The point is to make the report
say what the sample can support and stay silent where it cannot, rather than
printing a confident number that happens to be arithmetic on noise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

# ── Thresholds ────────────────────────────────────────────────────────────────
# Annualising a sub-year sample is the single most misleading thing a backtest
# can do, so CAGR is withheld below a year rather than extrapolated.
MIN_DAYS_FOR_CAGR = 365

# Sharpe's standard error is approximately sqrt((1 + S^2/2) / n). At n=252 and
# S=1 that is ~0.077, which is tight enough to report. At n=60 it is ~0.158.
# Below 60 observations the point estimate carries no useful information.
MIN_OBS_FOR_SHARPE = 60

# Fewer than this many rebalances is a handful of draws, not a track record.
MIN_REBALANCES = 12

# Round-trip cost in basis points per unit of turnover: retail commission plus
# half-spread on liquid US equities. Deliberately conservative — understating
# costs is what makes paper strategies look tradeable.
DEFAULT_COST_BPS = 10.0

# Annual borrow cost on the short leg for generally-available names.
DEFAULT_BORROW_BPS_ANNUAL = 50.0


@dataclass
class Sufficiency:
    """Whether a result may be reported, and what to say if not."""

    ok: bool
    days: int
    observations: int
    rebalances: int
    reasons: list[str]

    @property
    def headline(self) -> str:
        if self.ok:
            return "Sample is large enough to report annualised statistics."
        return "Sample too short for annualised statistics."


def assess(equity: pd.Series, rebalances: int) -> Sufficiency:
    """Decide what this sample can support."""
    if equity is None or equity.empty:
        return Sufficiency(False, 0, 0, rebalances, ["No equity curve was produced."])

    days = int((equity.index[-1] - equity.index[0]).days)
    obs = int(len(equity))
    reasons: list[str] = []

    if days < MIN_DAYS_FOR_CAGR:
        reasons.append(
            f"Spans {days} days; {MIN_DAYS_FOR_CAGR} are needed before a return "
            "can be annualised without inflating it."
        )
    if obs < MIN_OBS_FOR_SHARPE:
        reasons.append(
            f"Has {obs} daily observations; Sharpe needs at least "
            f"{MIN_OBS_FOR_SHARPE} to be distinguishable from noise."
        )
    if rebalances < MIN_REBALANCES:
        reasons.append(
            f"Contains {rebalances} rebalances; at least {MIN_REBALANCES} are "
            "needed before the result reflects a process rather than a few draws."
        )
    return Sufficiency(not reasons, days, obs, rebalances, reasons)


def total_return(equity: pd.Series) -> float | None:
    """Cumulative return. Always safe to report — it makes no time claim."""
    if equity is None or len(equity) < 2 or equity.iloc[0] == 0:
        return None
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series) -> float | None:
    """Annualised return, or None when the sample is under a year.

    Returning None rather than a number is the entire point: the previous
    implementation raised a four-week return to the 13th power and printed the
    result next to SPY's genuine multi-year CAGR.
    """
    if equity is None or len(equity) < 2:
        return None
    days = (equity.index[-1] - equity.index[0]).days
    if days < MIN_DAYS_FOR_CAGR:
        return None
    tr = total_return(equity)
    if tr is None or tr <= -1:
        return None
    return float((1 + tr) ** (365.25 / days) - 1)


def sharpe(equity: pd.Series, risk_free_annual: float = 0.0) -> tuple[float, float] | None:
    """(Sharpe, standard error), or None when there are too few observations.

    The standard error is returned alongside the estimate because a Sharpe
    without one invites reading 1.5 as meaningfully better than 1.2 when the
    sample cannot separate them. Uses the approximation
    se ~ sqrt((1 + S^2 / 2) / n).
    """
    if equity is None or len(equity) < 2:
        return None
    rets = equity.pct_change().dropna()
    n = len(rets)
    if n < MIN_OBS_FOR_SHARPE:
        return None
    sd = float(rets.std())
    if sd <= 0:
        return None
    excess = float(rets.mean()) - (risk_free_annual / 252.0)
    s = (excess * 252.0) / (sd * math.sqrt(252.0))
    se = math.sqrt((1 + (s ** 2) / 2) / n)
    return float(s), float(se)


def max_drawdown(equity: pd.Series) -> float | None:
    """Worst peak-to-trough decline. Safe on any sample length."""
    if equity is None or len(equity) < 2:
        return None
    peak = equity.cummax()
    return float(((equity - peak) / peak).min())


def turnover_cost(
    prev_holdings: set[str],
    new_holdings: set[str],
    cost_bps: float = DEFAULT_COST_BPS,
) -> float:
    """Cost of moving from one book to the next, as a return drag.

    Turnover is the share of the book that changed. Rebalancing 5 of 10 names
    is 50% turnover; at 10bps round-trip that is 5bps off the period return.
    """
    if not prev_holdings and not new_holdings:
        return 0.0
    universe = prev_holdings | new_holdings
    if not universe:
        return 0.0
    changed = len(prev_holdings.symmetric_difference(new_holdings))
    turnover = changed / max(len(universe), 1)
    return float(turnover * cost_bps / 10_000.0)


def borrow_cost(days_held: int, borrow_bps_annual: float = DEFAULT_BORROW_BPS_ANNUAL) -> float:
    """Financing drag on a short leg held for `days_held`."""
    if days_held <= 0:
        return 0.0
    return float(borrow_bps_annual / 10_000.0 * days_held / 365.25)


def point_in_time_row(pivot: pd.DataFrame, as_of: Any) -> pd.Series | None:
    """Most recent snapshot at or before `as_of` — never after.

    Replaces `get_indexer(..., method="nearest")`, which resolves in either
    direction and so could hand the backtest a score from the future. This is
    the difference between a walk-forward test and a look-ahead one, and it is
    invisible in the output: a peeking backtest simply looks better.
    """
    if pivot is None or pivot.empty:
        return None
    try:
        ts = pd.Timestamp(as_of)
    except (ValueError, TypeError):
        return None

    idx = pd.to_datetime(pd.Series(list(pivot.index)))
    eligible = idx[idx <= ts]
    if eligible.empty:
        return None  # no information existed yet; the caller must skip this date
    return pivot.iloc[int(eligible.idxmax())]


def stale_score_mask(
    pivot: pd.DataFrame,
    as_of: Any,
    max_age_days: int = 45,
) -> pd.Series:
    """True where a ticker's most recent score is too old to act on.

    An unbounded forward-fill carries one snapshot forward indefinitely, so a
    ticker scored once in June still appears to carry a live signal in December.
    """
    ts = pd.Timestamp(as_of)
    out = {}
    for col in pivot.columns:
        series = pivot[col].dropna()
        if series.empty:
            out[col] = True
            continue
        dates = pd.to_datetime(pd.Series(list(series.index)))
        prior = dates[dates <= ts]
        out[col] = True if prior.empty else (ts - prior.max()).days > max_age_days
    return pd.Series(out)


def report(equity: pd.Series, rebalances: int, risk_free_annual: float = 0.0) -> dict[str, Any]:
    """Statistics with every unsupported figure set to None.

    Callers render "—" for None rather than substituting a computed value; the
    absence is the finding.
    """
    suff = assess(equity, rebalances)
    sh = sharpe(equity, risk_free_annual)
    return {
        "sufficiency": suff,
        "total_return": total_return(equity),
        "cagr": cagr(equity),
        "sharpe": sh[0] if sh else None,
        "sharpe_se": sh[1] if sh else None,
        "max_drawdown": max_drawdown(equity),
        "days": suff.days,
        "observations": suff.observations,
        "rebalances": rebalances,
    }
