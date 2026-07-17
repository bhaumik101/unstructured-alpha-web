# Performance

_Memory, cold-start, load behavior, and the knobs to tune them. Last updated 2026-07-17._

## Current instance

- Web service: **Render Standard — 2 GB RAM / 1 CPU**, always-on (no cold sleep).
  Set via `plan: standard` in `render.yaml` (Blueprint-managed — the dashboard
  toggle alone gets reverted on sync; the file governs the plan).
- Baseline memory ~100 MB; heavy scans previously spiked toward the old 512 MB
  ceiling. On 2 GB there is 4× headroom.

## Memory / OOM history (fixed)

The app was OOM-killing every few minutes on the old 512 MB Starter box. Root
cause: `compute_full_ticker_score` fetched a **15-year** daily price window per
ticker (× up to 40 in parallel) when only ~2yr (correlation) + 252d (momentum)
are ever used. Fixes (all output-preserving):

- Price window **15yr → 3yr** in `utils/ticker_score.py` — Confluence Scores
  verified byte-identical (momentum differs ~1e-6 from yfinance split-adjust
  range dependence, invisible).
- Batch price fetch: one `yf.download` for N tickers instead of N calls
  (`fetch_prices_batch`), verified byte-identical.
- `gc.collect()` + glibc `malloc_trim(0)` (`utils/memory.release_memory()`) after
  the Recommender enrich and Screener 280-ticker builds.
- `MALLOC_ARENA_MAX=2` — caps glibc arenas so threaded scans don't hoard freed
  heap per-arena.

Zero OOM since.

## Cold-start (the big win)

The app HTML shell is fast (~0.2s TTFB). The historic ~7–8s blank on first load
was the **first script run**: ~2.2s of imports (pandas dominates ~1.4s) plus
**~4.6s in `get_all_signal_scores`**, which scored all 47 signals **serially**
(each a network-bound fetch + score).

**Fix:** `utils/signals_cache.get_all_signal_scores` now fans the 47 signals out
across a `ThreadPoolExecutor` (`SIGNAL_SCORE_WORKERS`, default 8), propagating the
Streamlit `ScriptRunContext` into workers so the inner `@st.cache_data` on
`fetch_signal_series` still caches. Output is **byte-identical** to the sequential
version (verified: 0 mismatches over all 47). Cold signal-scoring **~4.6s → <1s**.

This only does real work on a cold cache; warm hits (6h TTL) return instantly.
The keep-warm cron pings the app every 10 min to keep the cache warm.

## Load / resilience test

`tests/load/` (Locust) hits the SEO service (real DB-backed dynamic pages).

```
pip install locust
python tests/load/run_ramp.py            # staged 1 → 5 → 10 → 25 → 50 users
# or:
locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 2m \
       --host https://seo.unstructuredalpha.com --csv results/ramp50
```

**Result (2026-07-17, pre-upgrade Starter box): 0% failures through 50 concurrent
users.** App shell + health ~110ms, sitemap ~150ms, `/readyz` ~740ms.

**Known finding:** SEO `/ticker/{sym}` and `/signal/{id}` render in ~4.7s even at
1 user — a per-request render cost (not load-related). Candidate next
optimization: cache or snapshot those pages. The Streamlit app renders over a
websocket, so HTTP load only exercises its shell + health (noted in the script).

## Tuning knobs (env vars — no code change needed)

| Var | Default | Effect | Raise when |
|---|---|---|---|
| `SIGNAL_SCORE_WORKERS` | 8 | Cold-start signal fan-out width (1..16) | More cores; want fastest cold load |
| `RECOMMENDER_WORKERS` | 5 | Recommender scan pool (1..16); each in-flight score holds a 3yr frame | Multi-core plan + RAM headroom |
| `MALLOC_ARENA_MAX` | 2 | glibc malloc arenas | Multi-core plan (Pro Plus+); pointless on 1 CPU |
| `LOG_LEVEL` | INFO | Log verbosity | DEBUG for triage |

Guidance for larger plans: on a genuine multi-core box, set `RECOMMENDER_WORKERS`
8–12, `SIGNAL_SCORE_WORKERS` 12–16, and `MALLOC_ARENA_MAX` ~8 (relieves cross-core
allocation contention). On 1 CPU, leave `MALLOC_ARENA_MAX=2` — more arenas only
grow RSS with no throughput benefit.

## Caching (existing, don't rip out)

- `get_all_signal_scores` — 6h TTL, one shared entry across all pages.
- Provider fetches (`fetch_fred`/`fetch_eia`/prices) — TTL'd per data cadence.
- Per-day Pro AI score explanation — cache key is the score-state, so it
  regenerates only when the score actually changes (~24× fewer Haiku calls).
