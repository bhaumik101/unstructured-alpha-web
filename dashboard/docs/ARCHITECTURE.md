# Architecture

_Unstructured Alpha — a macro-signal intelligence product. Last updated 2026-07-17._

## Overview

Unstructured Alpha scores ~47 macro/alternative-data signals (FRED, EIA, SEC EDGAR,
FINRA, CBOE, and others) and blends them with price momentum to produce a
per-ticker "Confluence Score" across ~280 tickers. It is a multi-page Streamlit
application backed by Postgres, with a separate FastAPI service for
crawler-facing SEO pages, and a set of cron jobs for digests, alerts, and
universe maintenance.

## Request flow (runtime)

```
Browser
  └─> Render web service "unstructured-alpha"  (Standard: 2GB / 1 CPU, always-on)
        └─> app.py  (st.navigation router; every page sets its own page_config)
              └─> utils/header.render_header()   (topnav + regime bar, EVERY page)
                    ├─ observability: utils/observability.configure_logging() +
                    │                 per-session correlation id
                    ├─ auth:          utils/auth.py (DB login + 5/15min lockout)
                    │                 utils/billing.effective_is_pro / is_admin
                    ├─ rate limiting: utils/ratelimit.guard(...) on protected actions
                    ├─ cache:         st.cache_data (TTL'd) + st.cache_resource
                    ├─ database:      utils/db.py — ONE pooled SQLAlchemy engine
                    │                 (pool_size=5, max_overflow=10, pre_ping,
                    │                  recycle=300) → Neon Postgres
                    ├─ providers:     utils/fetchers.py → utils/resilience.py
                    │                 (circuit breaker + pooled retrying session)
                    ├─ scoring:       utils/signals_cache.get_all_signal_scores()
                    │                 (parallel cold-warm), utils/ticker_score,
                    │                 utils/analysis
                    └─ charts:        Plotly + TradingView (client-side)

SEO service "unstructured-alpha-seo"  (FastAPI, seo.unstructuredalpha.com)
  └─> seo/main.py — server-rendered ticker/signal pages, sitemap, robots
        ├─ health: /healthz, /readyz, /version
        └─ shares the same utils/ package + DATABASE_URL

Cron services (separate Render containers) — see DEPLOYMENT.md for the full list.
```

## Components

| Layer | Module(s) | Responsibility |
|---|---|---|
| Router | `app.py` | `st.navigation` registers all pages; must be first Streamlit call |
| Chrome | `utils/header.py`, `utils/theme.py` | Topnav, regime bar, page-view tracking, correlation id |
| Auth | `utils/auth.py`, `utils/auth_ui.py`, `utils/billing.py` | DB login, lockout, Pro/Admin detection |
| Data access | `utils/db.py` | Single pooled SQLAlchemy engine → Neon Postgres |
| Providers | `utils/fetchers.py` | All external data (yfinance, FRED, EIA, SEC, FINRA, …) |
| Resilience | `utils/resilience.py` | Per-provider circuit breakers + shared retrying HTTP session |
| Rate limiting | `utils/ratelimit.py` | Redis-backed atomic fixed-window limiter + in-proc fallback |
| Observability | `utils/observability.py` | JSON logging + correlation ids + `log_event` |
| Scoring | `utils/signals_cache.py`, `utils/ticker_score.py`, `utils/analysis.py` | Signal + ticker scoring, shared cache |
| Metrics SSOT | `utils/product_metrics.py` | `ACTIVE_SIGNAL_COUNT` (47), `SUPPORTED_TICKER_COUNT` (280) |
| SEO | `seo/main.py` | Crawlable server-rendered pages + health endpoints |

## Single sources of truth (do not hardcode)

- **Signal / ticker counts:** `utils/product_metrics.py` — `ACTIVE_SIGNAL_COUNT`
  (= `len(SIGNALS)` = 47), `SUPPORTED_TICKER_COUNT` (= `len(TICKERS)` = 280).
  Never hardcode "43"/"46"/"193" — import from here.
- **Admin allowlist:** `utils/billing.ADMIN_EMAILS`.
- **Pro/Admin status:** `utils/billing.effective_is_pro(user)` / `is_admin(user)`.
  The session `user` dict only holds `{"id","email"}` — it does NOT contain a
  tier or admin flag, so never check `user.get("subscription_tier")`.

## Two scores, deliberately distinct

- **Confluence Score** (Ticker Deep Dive, `compute_full_ticker_score`): 80% macro
  / 20% momentum + optional 12% differentiator signals.
- **Macro + Momentum Rank** (Stock Screener): `macro*0.70 + momentum*0.30`.

These are intentionally different metrics with different labels — not a bug.

## Repositories

- `bhaumik101/unstructured-alpha-web` — **source of truth**; the web service
  deploys from here.
- `bhaumik101/unstructured-alpha-dashboard` — kept in lockstep via a **dual-push
  git remote** (a single `git push` mirrors to both). Historically the Blueprint
  and crons deployed from `-dashboard`; the mirror keeps them from diverging.

The Streamlit app + SEO service live under `dashboard/` (the repo `rootDir`).
The Next.js marketing site lives under `dashboard/unstructured-alpha-web/`
(deployed separately on Vercel).

## Related docs

- [RELIABILITY.md](RELIABILITY.md) — resilience, rate limiting, health, observability
- [PERFORMANCE.md](PERFORMANCE.md) — memory, cold-start, load tests, tuning knobs
- [DEPLOYMENT.md](DEPLOYMENT.md) — Render infra, Blueprint, build pipeline, envs
- [RUNBOOK.md](RUNBOOK.md) — operational procedures & incident response
- [../RATE_LIMITS.md](../RATE_LIMITS.md) — rate-limit policies
