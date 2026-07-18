# Product Roadmap — Recommender, Portfolio Suite & Pro Upgrades

_Grounded in the live app + the 2 GB / 1 CPU (Standard) runtime. Last updated 2026-07-17._

This roadmap is deliberately honest about **feasibility on the current box**. The
runtime is Standard (2 GB RAM / 1 CPU) — not a big multi-core machine. So the
guiding rule is: **precompute or cache heavy work, render progressively, and make
expensive passes opt-in.** Nothing here assumes background-worker infrastructure;
where a feature would need it, that's called out.

Priorities: **P0** = do next (high impact / low-moderate effort), **P1** = strong
value, **P2** = nice-to-have / larger bets.

---

## Current Pro surface (baseline)

| Page | What it does | Health |
|---|---|---|
| Stock Recommender (`40`) | Ranks 280 tickers by macro confluence; deep-scores top picks | ✅ just fixed (enrichment now opt-in; loads fast) |
| Portfolio Suite (`44`) | 5 tabs: Backtest, Stress, Signal Backtest, Macro Exposure, Basket | ⚠️ likely same auto-run-heavy-scan risk as Recommender had |
| Factor Exposure (`27`) | Per-ticker factor decomposition | reactivated earlier |
| Alternative Data (`41`) | Alt-data signal surface | — |
| Export (`28`) | PDF export of analyses | rate-limited |

**Retired but revivable** (in `pages/retired/`): Options Flow (unusual options
activity), Signal Backtester (custom signal combos), Portfolio Analyzer
(aggregate portfolio macro exposure), Portfolio Backtest.

---

## Theme 1 — Recommender upgrades

**P0 · Persist the last scan so it's instant on return.** Cache the completed
deep-score results (per filter set) in Redis with a short TTL, not just
`st.session_state`. A returning user (or a second user with the same filters) sees
enriched results immediately instead of re-running. _Effort: S. Impact: High.
Feasible on Standard (Redis already provisioned)._

**P0 · Keep the Recommender warm.** Add `/stock-recommender` to the keep-warm cron
so the macro-ranking cache stays hot and the page never cold-loads for the first
visitor. _Effort: XS. Impact: Med._

**P1 · Progressive enrichment with live streaming.** Instead of one blocking
deep-score, stream each candidate's card as its score completes (fragment /
incremental render), so the user watches results fill in. Pairs with a bounded
worker count already in place. _Effort: M. Impact: High (perceived speed)._

**P1 · "Why this pick" transparency.** Reuse the Explain-the-Move attribution
engine to show, per recommended ticker, the top signals driving its score — the
same reconciling decomposition used on Ticker Deep Dive. Strong differentiator.
_Effort: M. Impact: High._

**P2 · Saved screens + alerts.** Let a Pro user save a filter set ("short-term
energy shorts") and get notified (email cron already exists) when a new ticker
enters the top ranks. _Effort: M–L. Impact: High for retention._

---

## Theme 2 — Portfolio Suite upgrades

**P0 · Audit for the same freeze pattern.** The Backtest / Stress / Signal-Backtest
tabs likely run heavy computations on tab open. Apply the Recommender fix: render
the tab structure first, gate the heavy run behind an explicit button with
progress, cache results. `st.tabs` renders all tabs' code — defer hidden-tab work.
_Effort: M. Impact: High (stability + speed). **Recommended immediately after the
roadmap.**_

**P1 · Upload a real portfolio.** CSV/paste import of holdings (ticker + weight),
then aggregate macro exposure, factor tilt, and concentration risk — reviving the
retired Portfolio Analyzer with the current engine. Add resource guards (max
holdings, max rows). _Effort: M. Impact: High._

**P1 · Portfolio-level confluence + hedging ideas.** Roll the per-ticker
Confluence Score up to a portfolio-weighted score, and surface which macro signals
the portfolio is most exposed to, plus candidate hedges. _Effort: M. Impact:
High._

**P2 · Scenario / stress presets.** Named macro shocks ("rates +100bp",
"oil spike", "credit widening") with precomputed factor responses. Precompute
overnight so the interactive path is instant. _Effort: M–L. Impact: Med–High._

---

## Theme 3 — New Pro upgrades (net-new)

**P1 · Revive Options Flow (unusual options activity).** yfinance-backed; surfaces
contracts where volume ≫ open interest. Route through the resilience layer +
rate limits; cache per ticker. A classic Pro draw. _Effort: M. Impact: High._

**P1 · Signal Backtester (custom combos).** Let Pro users build a custom signal
blend and backtest it. Guard compute hard (bounded date range, precomputed signal
history). _Effort: M–L. Impact: High for power users._

**P2 · AI portfolio review.** Feed the portfolio's macro exposure into the existing
Claude path to generate a plain-English risk read — cached by a stable input hash +
model version so it only regenerates on material change (pattern already used for
ticker explanations). _Effort: M. Impact: High; watch API cost with per-user
limits._

**P2 · Daily Pro digest, personalized.** Extend the existing digest cron to send
each Pro user their watchlist's confluence changes + new top ideas. _Effort: M.
Impact: High for retention._

---

## Theme 4 — Cross-cutting (perf & reliability, right-sized to Standard)

These make every Pro feature above safe and fast on 2 GB / 1 CPU. Several are the
remaining "right-sized to Standard" phases.

**P0 · Kill unnecessary Streamlit reruns.** Wrap ticker/date/filter inputs in
`st.form` so typing doesn't trigger a full rerun + recompute. Biggest
felt-smoothness win across the app. _Effort: M. Impact: High._

**P0 · Resource guards / caps.** Max date range, max tickers per request, max
export rows, max chart points — so one request can't exhaust the 2 GB. _Effort: S–M.
Impact: High (stability)._

**P1 · Precompute heavy analytics on schedule.** Move rolling z-scores,
correlations, historical percentiles, and the default Recommender ranking into
overnight/interval crons writing snapshots — so interactive pages just read.
_Effort: M–L. Impact: High._

**P1 · Progressive rendering everywhere.** Structure first → key metric → charts →
heavy tables last; show last-updated timestamps; preserve completed sections when
one fails. _Effort: M. Impact: High (perceived speed)._

**P2 · Chart/table efficiency.** Downsample long series for screen rendering (keep
full-res for downloads); cap points sent to the browser. _Effort: M. Impact: Med._

**P2 · Resource observability.** Log RSS/CPU per heavy op + memory-pressure guard
(shed optional work at high memory). Builds on the structured logging already in
place. _Effort: M. Impact: Med._

---

## Theme 5 — Scale scored coverage (the big one)

**Goal:** move from 280 scored tickers to scored coverage of the large majority of
*investable* US stocks, precomputed off the interactive path and stored durably.
Search already spans ~12,641 symbols; scoring needs to catch up.

### The integrity trap — do NOT score all 12,641

A large share of that universe is **not meaningfully scoreable** by a
macro-correlation model: leveraged/inverse ETPs (RKLX, SOFA…), plain ETFs, SPACs,
sub-12-month listings, and illiquid microcaps. Running the model on them produces
noise formatted as a score — which is exactly the credibility failure this product
can least afford. The app already has the right instinct in `utils/coverage.py`
(honest coverage tiers, never "—/100 Unknown"); extend that, don't bypass it.

**Qualifying universe (target ~3,000–5,000):** US common stocks with ≥12 months of
price history and a minimum average dollar-volume floor; exclude leveraged/inverse
and derivative ETPs; keep only macro-relevant ETFs (the sector SPDRs already in the
280). Everything outside stays searchable and on-demand — just honestly labelled
as not-scored rather than given a fake number.

### Architecture

Runs as a **dedicated scoring worker** (separate Render service/cron with 2–4 GB),
never in the 2 GB web process:

1. **Signals loaded once per run.** The 47 macro series are ticker-independent —
   load them a single time and reuse across every ticker. This is the dominant win
   and is what makes the whole thing tractable.
2. **Batch price fetch** via `fetch_prices_batch` in chunks (~150 symbols/call)
   through the resilience layer, with jitter and a per-provider request budget.
3. **Score** reusing `compute_full_ticker_score`'s math (correlation-weighted
   macro + momentum), chunked so peak RSS stays bounded; `release_memory()` between
   chunks.
4. **Persist** to the existing `score_snapshots` (+ `score_components` for
   attribution). Idempotent per `(ticker, snapshot_date)`; a failed compute must
   never overwrite a good prior row.

### Cadence (tiered — don't score everything daily)

| Tier | Universe | Cadence |
|---|---|---|
| A | the 280 core + every watchlisted/searched ticker | daily |
| B | liquid large/mid caps (~1,500) | every 2–3 days |
| C | remaining qualifying names | weekly |
| — | anything else | on-demand when a user opens it (already works), then cached |

### Stored safely

- Neon Postgres (managed, backups/PITR) — **confirm the retention window** matches
  the value of this data before relying on it.
- Index `(ticker, snapshot_date)`; at ~5k tickers daily that's ~1.8M rows/year —
  comfortable, but revisit partitioning/retention as it grows.
- Always surface the as-of date; never present a stale snapshot as current.
- Track per-run: rows written, failures, duration, input/algorithm version.

_Effort: L. Impact: Very High — it turns "search any stock" into "analyse any
stock", which is the product promise._

---

## Suggested sequence

1. **Portfolio Suite freeze audit** (P0, Theme 2) — same class of bug we just fixed
   on the Recommender; highest reliability payoff.
2. **`st.form` rerun reduction + resource guards** (P0, Theme 4) — app-wide smoothness + safety.
3. **Recommender: Redis-persist last scan + keep-warm** (P0, Theme 1) — instant returns.
4. **Precompute heavy analytics on schedule** (P1, Theme 4) — unlocks fast interactive pages.
5. **Revive Options Flow + Portfolio upload** (P1, Themes 2/3) — visible new Pro value.
6. Then the P1/P2 differentiators (Why-this-pick, AI portfolio review, saved screens).

## Guardrails (apply to every item)

- Heavy work is **opt-in or precomputed**, never auto-run on cold page load.
- Every cache entry is **bounded** (TTL + size); never cache full Plotly objects or
  user-specific data globally.
- Every provider call stays behind the **resilience layer + rate limits**.
- **Preserve financial-data accuracy** — any scoring change is validated
  byte-identical against the current output before shipping.
- Revisit the runtime plan only if precompute + caching genuinely can't keep a
  feature within 2 GB — and cost it explicitly before upgrading.
