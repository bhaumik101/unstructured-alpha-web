"""
utils/strategy.py
Unstructured Alpha — Signal-Based Strategy Backtester

Builds a composite macro score from daily-frequency signals (all freely
available via FRED + yfinance), then simulates a rules-based strategy
that goes long, reduces exposure, or moves to cash depending on the score.
Compares against SPY buy-and-hold as the benchmark.

Signals used (all daily frequency — critical for meaningful backtest):
  yield_curve      : T10Y2Y   (FRED) — inverted = bearish
  hy_spread        : BAMLH0A0HYM2 (FRED) — wide = bearish
  vix              : ^VIX     (yfinance) — high = bearish
  ten_year_yield   : ^TNX     (yfinance) — high = bearish for growth
  copper_gold_ratio: HG=F / GLD (yfinance) — falling = risk-off
  put_call_ratio   : CPCE     (FRED) — high = fear = contrarian bullish

Strategy rules (applied to the rolling composite score, 0-100):
  score ≥ 65  →  Long 100% SPY
  35 < score < 65  →  Long 50% SPY + 50% cash (reduces exposure)
  score ≤ 35  →  Flat/Cash (0% in SPY)

Backtest window: 2010-01-01 to present (daily bars).
All signals are percentile-ranked vs. a trailing 252-day (1-year) window
to make them stationary and comparable — same methodology as the live dashboard.
"""

from __future__ import annotations

import warnings
from datetime import datetime, date

import numpy as np
import pandas as pd
import yfinance as yf

# Suppress noisy yfinance / pandas warnings during backtest
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Constants ─────────────────────────────────────────────────────────────────

BACKTEST_START = "2010-01-01"
ROLLING_WINDOW = 252          # days for percentile scoring
REBALANCE_COST = 0.001        # 0.1% round-trip transaction cost per trade

# Signal definitions: (source, series_id, inverse)
# inverse=True means a higher raw value = worse macro (score gets flipped)
_SIGNAL_DEFS: list[dict] = [
    {"name": "Yield Curve (10Y-2Y)",   "source": "fred",     "series": "T10Y2Y",         "inverse": True,  "weight": 1.5},
    {"name": "HY Credit Spread",       "source": "fred",     "series": "BAMLH0A0HYM2",   "inverse": True,  "weight": 1.5},
    {"name": "VIX (Fear Index)",        "source": "yfinance", "series": "^VIX",           "inverse": True,  "weight": 1.0},
    {"name": "10Y Treasury Yield",     "source": "yfinance", "series": "^TNX",           "inverse": True,  "weight": 1.0},
    {"name": "Copper/Gold Ratio",      "source": "yfinance_ratio", "series": ["HG=F","GLD"], "inverse": False, "weight": 1.0},
    {"name": "Put/Call Ratio",         "source": "fred",     "series": "CPCE",           "inverse": True,  "weight": 0.75},
    {"name": "M2 Money Supply",        "source": "fred",     "series": "M2SL",           "inverse": False, "weight": 0.75},
]

# ── Data Fetching ─────────────────────────────────────────────────────────────

def _fetch_fred(series_id: str, start: str) -> pd.Series:
    """Pull a FRED series via pandas_datareader. Returns a daily-indexed Series."""
    try:
        import pandas_datareader.data as web
        s = web.DataReader(series_id, "fred", start=start)
        return s.squeeze().rename(series_id)
    except Exception:
        return pd.Series(dtype=float, name=series_id)


def _fetch_yf(ticker: str, start: str) -> pd.Series:
    """Pull daily Close from yfinance."""
    try:
        df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        if df.empty:
            return pd.Series(dtype=float, name=ticker)
        # Handle multi-level columns
        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"].squeeze()
        else:
            close = df["Close"]
        return close.rename(ticker)
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def _fetch_spy(start: str) -> pd.Series:
    """SPY daily Close for the benchmark and strategy P&L."""
    return _fetch_yf("SPY", start)


def _fetch_signal_raw(sig: dict, start: str) -> pd.Series:
    """Return raw (unscored) time series for one signal definition."""
    src = sig["source"]
    if src == "fred":
        return _fetch_fred(sig["series"], start)
    elif src == "yfinance":
        return _fetch_yf(sig["series"], start)
    elif src == "yfinance_ratio":
        num = _fetch_yf(sig["series"][0], start)
        den = _fetch_yf(sig["series"][1], start)
        ratio = (num / den).dropna()
        ratio.name = f"{sig['series'][0]}/{sig['series'][1]}"
        return ratio
    return pd.Series(dtype=float)


# ── Scoring ───────────────────────────────────────────────────────────────────

def _rolling_percentile(s: pd.Series, window: int = ROLLING_WINDOW) -> pd.Series:
    """
    At each date, rank the current value against the trailing `window` values
    and express as a percentile (0-100). Requires at least `window` history
    before any score is produced.
    """
    scores = []
    arr = s.values
    for i in range(len(arr)):
        if i < window:
            scores.append(np.nan)
            continue
        window_vals = arr[i - window: i]
        pct = float(np.sum(window_vals <= arr[i]) / window * 100)
        scores.append(pct)
    return pd.Series(scores, index=s.index, name=s.name)


def _score_signal(raw: pd.Series, inverse: bool) -> pd.Series:
    """Percentile-score a raw signal and flip if inverse."""
    scored = _rolling_percentile(raw)
    if inverse:
        scored = 100 - scored
    return scored


# ── Composite Score ───────────────────────────────────────────────────────────

def _build_composite(
    scored_signals: list[tuple[str, pd.Series, float]],
    spy_index: pd.DatetimeIndex,
) -> pd.Series:
    """
    Weighted average of all signal scores, reindexed to SPY trading days
    and forward-filled (since FRED publishes less frequently than daily).
    """
    daily_scores = {}
    total_weight = sum(w for _, _, w in scored_signals)
    for name, series, weight in scored_signals:
        # Forward-fill to daily — FRED monthly/weekly data doesn't update every day
        daily = series.reindex(spy_index, method="ffill")
        daily_scores[name] = daily * (weight / total_weight)

    if not daily_scores:
        return pd.Series(np.nan, index=spy_index)

    df = pd.DataFrame(daily_scores)
    composite = df.sum(axis=1, min_count=1)  # NaN if all signals are NaN
    return composite.rename("composite_score")


# ── Strategy Simulation ───────────────────────────────────────────────────────

def _run_strategy(
    spy: pd.Series,
    composite: pd.Series,
    long_threshold: float = 65.0,
    reduce_threshold: float = 35.0,
    reduce_weight: float = 0.5,
) -> pd.DataFrame:
    """
    Simulate the rules-based strategy on SPY daily returns.

    Position sizing:
      composite >= long_threshold  → 1.0 (fully long)
      reduce_threshold < composite < long_threshold → reduce_weight (partial)
      composite <= reduce_threshold → 0.0 (cash)

    Transaction cost applied on any change in position.
    """
    # Align on common dates
    common = spy.index.intersection(composite.index)
    spy_ret = spy.pct_change().reindex(common).fillna(0)
    score   = composite.reindex(common).ffill()

    # Previous day's score drives today's position (no lookahead bias)
    prev_score = score.shift(1)

    position = pd.Series(np.nan, index=common)
    position[prev_score >= long_threshold] = 1.0
    position[(prev_score > reduce_threshold) & (prev_score < long_threshold)] = reduce_weight
    position[prev_score <= reduce_threshold] = 0.0
    position = position.fillna(reduce_weight)  # Default until score available

    # Transaction costs
    pos_change = position.diff().abs().fillna(0)
    costs = pos_change * REBALANCE_COST

    # Strategy daily returns
    strat_ret = position * spy_ret - costs

    # Cumulative returns
    spy_cum   = (1 + spy_ret).cumprod()
    strat_cum = (1 + strat_ret).cumprod()

    return pd.DataFrame({
        "spy_price":       spy.reindex(common),
        "spy_ret":         spy_ret,
        "strat_ret":       strat_ret,
        "spy_cum":         spy_cum,
        "strat_cum":       strat_cum,
        "position":        position,
        "composite_score": score,
    })


# ── Performance Metrics ───────────────────────────────────────────────────────

def _metrics(cum_returns: pd.Series, daily_returns: pd.Series) -> dict:
    """Compute annualised performance metrics."""
    n_years = len(daily_returns) / 252
    if n_years < 0.1:
        return {}

    total_ret  = cum_returns.iloc[-1] - 1
    cagr       = (1 + total_ret) ** (1 / n_years) - 1
    vol        = daily_returns.std() * np.sqrt(252)
    sharpe     = (daily_returns.mean() * 252) / (vol + 1e-9)
    rolling_max = cum_returns.cummax()
    drawdown   = (cum_returns - rolling_max) / rolling_max
    max_dd     = drawdown.min()
    win_days   = (daily_returns > 0).sum() / max(1, len(daily_returns))
    calmar     = cagr / abs(max_dd) if max_dd != 0 else 0

    return {
        "total_return": round(total_ret * 100, 1),
        "cagr":         round(cagr * 100, 1),
        "volatility":   round(vol * 100, 1),
        "sharpe":       round(sharpe, 2),
        "max_drawdown": round(max_dd * 100, 1),
        "win_rate":     round(win_days * 100, 1),
        "calmar":       round(calmar, 2),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def run_backtest(
    start: str = BACKTEST_START,
    long_threshold: float = 65.0,
    reduce_threshold: float = 35.0,
    reduce_weight: float = 0.5,
) -> dict:
    """
    Full backtest pipeline. Returns a dict with:
      - results_df      : pd.DataFrame — daily price/score/return series
      - signal_scores   : dict of {signal_name: pd.Series} — individual signal scores
      - strategy_metrics: dict — CAGR, Sharpe, max drawdown, etc. for strategy
      - benchmark_metrics: dict — same for SPY buy-and-hold
      - signal_defs     : list[dict] — signal metadata for display
      - params          : dict — backtest parameters used
      - error           : str | None
    """
    try:
        # 1. Fetch SPY (benchmark + strategy vehicle)
        spy = _fetch_spy(start)
        if spy.empty or len(spy) < ROLLING_WINDOW + 50:
            return {"error": "Could not fetch SPY data for backtest."}

        spy_index = spy.index

        # 2. Fetch + score each signal
        scored_signals: list[tuple[str, pd.Series, float]] = []
        raw_series: dict[str, pd.Series] = {}
        for sig in _SIGNAL_DEFS:
            raw = _fetch_signal_raw(sig, start)
            if raw.empty or raw.dropna().empty:
                continue
            # Resample to business-day frequency to align with SPY
            raw_daily = raw.resample("B").last().ffill()
            scored    = _score_signal(raw_daily, sig["inverse"])
            raw_series[sig["name"]] = raw_daily
            scored_signals.append((sig["name"], scored, sig["weight"]))

        if len(scored_signals) < 3:
            return {"error": "Fewer than 3 signals loaded — backtest aborted."}

        # 3. Build composite score
        composite = _build_composite(scored_signals, spy_index)

        # 4. Run strategy simulation
        results = _run_strategy(spy, composite, long_threshold, reduce_threshold, reduce_weight)

        # Drop rows before any composite score exists (warm-up period)
        results = results.dropna(subset=["composite_score"])

        # Renormalize cumulative returns to 1.0 at the first date
        for col in ["spy_cum", "strat_cum"]:
            results[col] = results[col] / results[col].iloc[0]

        # 5. Performance metrics
        strat_m = _metrics(results["strat_cum"], results["strat_ret"])
        bench_m = _metrics(results["spy_cum"],   results["spy_ret"])

        # 6. Signal metadata for display
        signal_scores_out = {name: series for name, series, _ in scored_signals}

        return {
            "results_df":        results,
            "signal_scores":     signal_scores_out,
            "strategy_metrics":  strat_m,
            "benchmark_metrics": bench_m,
            "signal_defs":       _SIGNAL_DEFS,
            "params": {
                "start":            start,
                "long_threshold":   long_threshold,
                "reduce_threshold": reduce_threshold,
                "reduce_weight":    reduce_weight,
                "n_signals":        len(scored_signals),
                "rolling_window":   ROLLING_WINDOW,
            },
            "error": None,
        }

    except Exception as exc:
        return {"error": str(exc)}


def get_current_position(backtest_result: dict) -> dict:
    """
    Extract today's signal state from a completed backtest.
    Returns position, composite score, and each signal's current score.
    """
    if backtest_result.get("error"):
        return {}
    df = backtest_result["results_df"]
    if df.empty:
        return {}
    last = df.iloc[-1]
    score = float(last["composite_score"])
    pos   = float(last["position"])
    pos_label = "LONG" if pos >= 0.9 else ("REDUCED" if pos > 0.1 else "CASH")

    signal_current = {}
    for name, series in backtest_result["signal_scores"].items():
        last_score = series.dropna().iloc[-1] if not series.dropna().empty else None
        signal_current[name] = round(float(last_score), 1) if last_score is not None else None

    return {
        "composite_score": round(score, 1),
        "position":        pos_label,
        "position_pct":    round(pos * 100, 0),
        "signal_scores":   signal_current,
        "as_of":           df.index[-1].strftime("%Y-%m-%d"),
    }
