# Runbook

_Operational procedures and incident response. Last updated 2026-07-17._

## Quick health check

```bash
# Web (liveness)
curl -s -o /dev/null -w "%{http_code}\n" https://app.unstructuredalpha.com/_stcore/health   # → 200

# SEO service
curl -s https://seo.unstructuredalpha.com/healthz    # {"status":"ok"}
curl -s https://seo.unstructuredalpha.com/readyz     # {"ready":true,"db":"up","redis":"up"}
curl -s https://seo.unstructuredalpha.com/version    # {service, commit, signals:47}
```

- `readyz` `db:"down"` → 503: Postgres/Neon problem (see below).
- `readyz` `redis:"down"`: degraded, NOT fatal — rate limiting fails open.
- Rate-limiter backend indicator: Admin page shows 🟢 Redis / 🟡 in-process.

## Incident: deploy failed

1. Render dashboard → service → **Events** for the human-readable reason.
2. **"Build blocked — out of pipeline minutes"** → NOT code. Raise the build
   pipeline spend limit (Settings → Build Pipeline). Then Manual Deploy → Deploy
   latest commit. (Consider switching the pipeline tier back to Starter to save
   cost — see DEPLOYMENT.md.)
3. **Sub-second (~1s) failure, no build logs** → a Blueprint/`render.yaml`
   validation or config problem. Check the last `render.yaml` change.
4. **Fails during build (~1m+)** → a real build error; read the build log.
5. A pushed commit didn't deploy at all → likely it didn't touch `dashboard/`
   (auto-deploy only fires on `rootDir` changes). Manual Deploy → Deploy latest
   commit.

## Incident: app is down / erroring

1. Check `/_stcore/health` — if 200, the server is up (issue is a page, not the
   process). If not 200, check Render → Logs and Events.
2. Logs are JSON; filter by `cid` to trace one session/request. Look for
   `[circuit]` (a provider breaker OPEN) or `rate_limit_block` events.
3. Recent deploy suspected → **Rollback** to the last green deploy.

## Incident: a data provider is down

- Expected & handled: the provider's circuit breaker opens after 4 consecutive
  failures and fast-fails for 60s; affected signals show gracefully (no page
  crash). Confirm via `[circuit] <provider> OPEN` log lines.
- No action usually needed. If a provider is down for a long time, the breaker
  keeps the app responsive; data refreshes when the provider recovers.

## Incident: OOM / high memory (should be rare on 2 GB)

- Check Render → Metrics (memory). Baseline ~100 MB; scans spike transiently.
- Immediate lever: lower `RECOMMENDER_WORKERS` / `SIGNAL_SCORE_WORKERS` env vars.
- Structural levers already in place: 3yr price window, batched fetches,
  `malloc_trim` after scans, `MALLOC_ARENA_MAX=2`.
- Escalation: bump `plan:` in `render.yaml` (e.g. `pro` = 4 GB) and deploy.

## Incident: Postgres / Neon problem

- `/readyz` returns `db:"down"`. Check Neon status + the `DATABASE_URL` secret.
- The engine is pre-ping + auto-recycling, so transient drops self-heal; a
  sustained outage needs Neon-side attention.

## Routine: tune performance

All via env vars (no code change) — see PERFORMANCE.md:
`SIGNAL_SCORE_WORKERS`, `RECOMMENDER_WORKERS`, `MALLOC_ARENA_MAX`, `LOG_LEVEL`.

## Routine: adjust a rate limit

Edit `POLICIES` in `utils/ratelimit.py` (`action: (limit, window_seconds)`),
commit, deploy. Document the change in `RATE_LIMITS.md`.

## Routine: verify after any deploy

```bash
# 1. endpoints green
curl -s https://seo.unstructuredalpha.com/readyz
curl -s https://seo.unstructuredalpha.com/version   # commit should match HEAD
# 2. app renders (load the Signal Dashboard; regime bar should reconcile to 47)
# 3. run the unit suites
python -m pytest tests/test_resilience.py tests/test_ratelimit.py tests/test_observability.py -q
```

Note: the full `pytest tests/` run has ~41 pre-existing cross-test-pollution
failures that pass in isolation — they are unrelated to app health. Trust the
three suites above plus the live endpoint/render checks.

## Suspended crons

`tweet-best-ideas` and `tweet-flips` are suspended (X API 402 / credits
depleted). Re-enable in Render only after the X API billing is resolved.

## Key facts

- Web service ID: `srv-d8s4bq4vikkc7397q2qg`
- Repos: `unstructured-alpha-web` (source of truth) + `-dashboard` (mirror);
  one `git push` updates both.
- Redis: `unstructured-alpha-redis` (Render Key Value).
- Admin allowlist: `utils/billing.ADMIN_EMAILS`.
