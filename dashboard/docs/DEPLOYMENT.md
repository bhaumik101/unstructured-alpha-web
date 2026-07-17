# Deployment

_How Unstructured Alpha builds, deploys, and is configured on Render.
Last updated 2026-07-17._

## Platform

Everything runs on **Render**, defined as Infrastructure-as-Code in
`dashboard/render.yaml` (a Blueprint). `rootDir: dashboard`.

- **Web service** `unstructured-alpha` (`srv-d8s4bq4vikkc7397q2qg`) —
  Streamlit app. Plan **Standard (2 GB / 1 CPU)**, always-on.
  Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  --server.headless true`. Health: `/_stcore/health` (liveness).
- **SEO service** `unstructured-alpha-seo` — FastAPI (`seo/main.py`).
  Health: `/healthz`.
- **Managed Redis** `unstructured-alpha-redis` (Render Key Value) —
  `REDIS_URL=redis://red-…:6379` (internal private hostname, no credentials).
- **Cron services** (separate containers; do not affect web RAM):
  keep-warm, digest, trial-reminder, webhooks, watchlist-alerts,
  resolve-predictions, grow-universe, score-moved, velocity-alerts,
  weekly-brief, brief-subscribers, onboarding-day3, onboarding-day7,
  reengagement, signal-flip-alerts. **Suspended** (X API 402): tweet-best-ideas,
  tweet-flips.

## Git & repositories

- Source of truth: `bhaumik101/unstructured-alpha-web` (web service deploys from
  `main`).
- The local `origin` has **dual push URLs** — a single `git push` mirrors to both
  `-web` and `-dashboard`, so they never diverge (the Blueprint/crons historically
  read `-dashboard`).

## How a deploy happens

1. `git push origin main` → mirrors to both repos.
2. Render **auto-deploys** the web service on push **— but only when files inside
   `rootDir` (`dashboard/`) change.** An empty commit or a change outside
   `dashboard/` will NOT trigger an auto-deploy.
3. Blueprint changes (`render.yaml`) sync on push and apply config/plan/env
   changes (this is what governs the instance `plan:`).
4. Zero-downtime deploy; ~1.5–2 min build.

### Trigger a deploy manually
Render dashboard → the service → **Manual Deploy** → **Deploy latest commit**
(use this when you pushed a commit that didn't touch `dashboard/`, or to redeploy
after a build-pipeline block clears).

## Instance type / plan (IMPORTANT)

The service is **Blueprint-managed**, so the instance type is governed by
`plan:` in `render.yaml` — **a change made only in the Render dashboard gets
reverted to the file's value on the next sync.** To change the app's compute,
edit `plan:` (valid slugs: `starter`, `standard`, `pro`, `pro plus`, `pro max`,
`pro ultra`) and deploy.

Web-service compute reference (per-service, prorated by the second):

| Plan | RAM | CPU | Price |
|---|---|---|---|
| starter | 512 MB | 0.5 | $7/mo |
| **standard (current)** | **2 GB** | **1** | **$25/mo** |
| pro | 4 GB | 2 | $85/mo |
| pro plus | 8 GB | 4 | $175/mo |
| pro max | 16 GB | 4 | $225/mo |
| pro ultra | 32 GB | 8 | $450/mo |

A 64 GB / 16 CPU **web runtime** is Custom (contact sales) only. Note: the
Postgres DB and the **build pipeline** are separate compute with their own tiers
(don't confuse a DB/pipeline upgrade with the app runtime).

## Build pipeline (separate from runtime)

Builds run on the workspace's **build pipeline** compute, metered in
**pipeline minutes**, gated by a **monthly spend limit** (Render dashboard →
Settings → Build Pipeline). If minutes/limit are exhausted, deploys fail with
_"Build blocked — your workspace has run out of pipeline minutes"_ (not a code
error). Fix: raise the spend limit (a valid card must be on file).

Tiers: **Starter** (2 CPU / 8 GB, $5/1000 min, includes 1,000 free min/mo) vs
**Performance** (16 CPU / 64 GB, $25/1000 min, no free minutes). A plain
`pip install` build does **not** benefit from Performance — Starter is the
cost-effective default; use Performance only for genuinely heavy builds.

## Environment variables

See [`../.env.example`](../.env.example) for the full annotated list. In prod,
secrets are entered in the Render dashboard (marked `sync: false` in
`render.yaml`); non-secrets (e.g. `REDIS_URL`, `MALLOC_ARENA_MAX`) are in the
Blueprint. Performance knobs (`SIGNAL_SCORE_WORKERS`, `RECOMMENDER_WORKERS`,
`MALLOC_ARENA_MAX`, `LOG_LEVEL`) are optional — safe defaults live in code.

## Rollback

Render dashboard → the service → **Deploys** → pick a prior green deploy →
**Rollback**. Or `git revert` + push. The last known-good app deploys are tagged
in the deploy history with commit SHAs.
