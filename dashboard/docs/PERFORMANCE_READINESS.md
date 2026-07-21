# Core Performance and Product-Readiness Pass

Date: 2026-07-21  
Branch: `performance/core-readiness-pass`  
Scoring model: `2026.07.1` (mathematics unchanged)

## Outcome

The canonical full ticker result is now reusable across Ticker Deep Dive,
exports, alert evaluation, and score-move jobs. Streamlit widget reruns reuse the
same in-session object and do not hash, copy, fetch, or recalculate the result.
Compatible stored full-score snapshots can render before a live refresh.

No macro-only score is presented as the complete Confluence Score. A failed
optional provider produces a clearly marked `provisional` result, is not cached
as complete, and is not written over the last compatible complete snapshot.

## Measured timings

Measurements used live provider calls on 2026-07-21. Each cold case cleared all
source caches first. Network variability means cold differences are directional,
not a controlled provider benchmark.

| Ticker | Before cold | Before source-warm rerun | After cold | After full-cache hit |
|---|---:|---:|---:|---:|
| AAPL | 14.609s | 0.574s | 15.511s | <0.001s |
| NVDA | 8.928s | 0.422s | 7.721s | <0.001s |
| CCJ | 4.916s | 0.237s | 4.078s | <0.001s |
| LEU | 21.555s | 0.236s | 6.659s | <0.001s |

The after-change scores differed by 0.4–0.6 points from the earlier run because
live inputs changed between measurements; scoring mathematics was not modified.

A separate instrumented CCJ cold sample took 10.125s:

| Stage | Duration |
|---|---:|
| Signal-series retrieval and scoring | 8.081s |
| Price retrieval | 0.331s |
| Correlation calculation | 0.206s |
| Federal contracts | 0.629s |
| Insider transactions | 0.208s |
| Short interest | 0.669s |
| 13F | <0.001s (not applicable to CCJ) |

The remaining cold bottleneck is the breadth and latency of macro-series
retrieval, followed by optional provider latency. Warm full results eliminate
both from Streamlit reruns.

## Cache architecture

The worker-level full-result cache is a thread-safe, bounded LRU with per-key
request de-duplication. Its key contains:

- normalized ticker;
- `auto` versus `explicit` signal-selection mode;
- canonical sorted, deduplicated signal tuple;
- `include_optional`;
- model version;
- signal-registry version;
- 30-minute freshness bucket.

`None` and an explicit empty signal list do not collide. The cache holds at most
256 results. Targeted clear operations remove one ticker/configuration or one
ticker's results; no product action calls global `st.cache_data.clear()`.

Session state keeps up to 12 exact result objects, keyed by the same score key.
Switching segmented controls therefore does not recompute or re-hash the result.

The cache is process-local by design. A cron process cannot warm a different web
worker's memory. Durable first-paint support comes from compatible database
snapshots, not from pretending those processes share RAM.

## Snapshot-first policy

A snapshot is eligible only when all of these match:

- `score_kind == "full"`;
- current model version;
- current signal-registry version;
- exact canonical signal set;
- a component snapshot exists for the same ticker/date.

The UI shows the calculation timestamp and freshness label, then refreshes live
evidence. Macro-only and legacy/unverifiable rows are never accepted as complete.
If fresh optional evidence fails, the compatible complete snapshot remains
authoritative and the provisional result cannot overwrite it.

## Source freshness policy

| Source | TTL | Bound | Notes |
|---|---:|---:|---|
| Live quote | 5 minutes | 100 | Existing policy |
| Daily price history | 2 hours | 150 | Normalized ticker and day-level dates |
| Macro series (FRED/EIA) | 6 hours | 60/15 | Underlying dispatch caches; day-level dates |
| Federal contracts | 24 hours | 128 | Normalized company name |
| Insider transactions | 6 hours | 128 | Normalized ticker/arguments |
| Short interest | 24 hours | 128 | Normalized ticker/arguments |
| 13F fund filings | 24 hours | 32 | Once per normalized CIK/fund, reused by tickers |

Price and optional-source network failures are returned with explicit error
metadata outside the cached function, so failures do not poison the source cache.
Valid empty provider responses remain cacheable.

## Loading and observability

Ticker Deep Dive reports staged progress for cached/stored score lookup, macro
signals, price history, optional evidence, and explanation preparation. Structured
timing logs contain ticker, stage, cache status, duration, success, and UTC
timestamp, but no user/session data. Full page and rerun timings are also logged.

## Warm-up path

Run manually or from a scheduler; it is never imported by web-process startup:

```bash
python scripts/warm_full_scores.py
```

The job covers AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, SPY, QQQ, CCJ, and
LEU. It batch-downloads prices, scores tickers sequentially with a configurable
pause, logs every duration/failure, and persists only compatible complete
snapshots. When invoked inside a web process it also primes that worker's bounded
cache; as a separate scheduled process its durable benefit is snapshot-first
first paint.

## Correctness risks and safeguards

- Scoring weights and thresholds are unchanged; `MODEL_VERSION` was not bumped.
- Explicit empty signals now retain their documented semantics instead of being
  silently treated as automatic selection.
- Cached result dictionaries are treated as immutable. A future caller that
  mutates them in place could affect another page in the same worker.
- The snapshot schema stores one ticker/day row. Multiple explicit signal
  configurations on the same day still compete for that row; exact signal-set
  compatibility prevents a wrong display, but the schema should eventually key
  snapshots by configuration fingerprint.
- Provider latency remains outside application control. Cold target gates are not
  claimed as met from this sample.

## Tests

Before changes, the full suite produced **591 passed, 28 failed, 2 skipped**.
Existing failures included stale page-registration fixtures, HTTP mocks that no
longer intercept the resilience wrapper, package-version-sensitive Streamlit
fixtures, and several model/universe expectation drifts.

New targeted tests cover canonical cache hits, ticker/signal/model/optional
misses, `None` versus empty signals, targeted invalidation, session rerun reuse,
complete-versus-macro separation, provisional non-caching, and honest optional
failure handling.

After changes, the full suite produced **599 passed, 28 failed, 2 skipped** in
64.46 seconds. The eight added tests all pass, and the existing failure count did
not increase. The same pre-existing failure categories remain; no new failure is
attributable to this pass.

## Files changed

- `utils/performance.py` — privacy-safe timing and staged progress hooks.
- `utils/score_cache.py` — canonical bounded cache, session reuse, targeted
  invalidation, and compatible snapshot lookup.
- `utils/ticker_score.py` — stage instrumentation and complete/provisional result
  metadata, with scoring mathematics unchanged.
- `utils/fetchers.py` — normalized bounded source caches whose failures are not
  cached.
- `pages/3_Ticker_Deep_Dive.py` — snapshot-first rendering, staged loading,
  targeted refresh, and rerun preservation.
- `pages/28_Export.py`, `utils/alerts.py`, and `cron/send_score_moved.py` — shared
  full-result reuse.
- `utils/score_warmup.py` and `scripts/warm_full_scores.py` — explicit warm-up
  path for the high-value universe.
- `tests/test_score_cache_unit.py` and `tests/test_ticker_deep_dive_sections.py`
  — cache correctness, failure honesty, and snapshot-write coverage.

## Recommended next step

Move macro retrieval from dozens of on-demand dispatches to a periodically
refreshed, shared signal snapshot keyed by series and as-of date. That directly
targets the measured 8.08s cold bottleneck while preserving the current scoring
formula. Then run a controlled production trace across several hours before
setting or advertising the 8-second uncached target as achieved.
