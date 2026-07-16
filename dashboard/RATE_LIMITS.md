# Rate Limits

Distributed rate limiting for Unstructured Alpha. Implemented in
`utils/ratelimit.py`.

## Backend

- **Primary:** Redis (Render Key Value `unstructured-alpha-redis`, Free tier,
  same Oregon private network). Connection via the `REDIS_URL` env var
  (`redis://red-d9cipkeq1p3s73ben9cg:6379` — a private-network hostname, no
  credentials). Set in `render.yaml` and applied via Blueprint sync.
- **Algorithm:** atomic fixed-window counter — a Lua script does
  `INCR` then `EXPIRE` (only on the first hit of a window) then `TTL`, so
  concurrent requests across processes/instances cannot race past the limit.
- **Key namespace:** `rl:<action>:<actor>`, each with a short TTL (= the window),
  so the 25 MB instance never fills.
- **Fallback:** if `REDIS_URL` is unset or Redis is unreachable, a per-process
  in-memory limiter takes over (weaker — not shared across instances/restarts).
  The active backend is shown on the Admin dashboard (🟢 Redis / 🟡 fallback).
- **Fail-open:** a Redis error during a check *allows* the request rather than
  locking users out on a transient blip. Availability > perfect enforcement.

## Actor identity

- **Logged-in users:** `u<user_id>`.
- **Anonymous:** the Streamlit session id (`s<session_id>`), else `anon`.
- **IP-based limits:** best-effort client IP from Render's `X-Forwarded-For`
  (leading value). XFF can be spoofed, so IP limits are a *supplement*, never
  the sole control.

## Policies (`utils/ratelimit.POLICIES`) — (limit, window)

| Action | Limit | Window | Actor | Wired? | Notes |
|---|---|---|---|---|---|
| `ticker_analysis` | 30 | 5 min | user/session | ✅ Ticker Deep Dive | Counts only *new* tickers (not reruns); over-limit → calm "slow down" message + `st.stop()`. |
| `ai_research` | 10 | 1 hour | user/session | ✅ AI Assistant | Gates only the Claude API path (Anthropic $). Rule-based answers stay free. Over-limit → polite message, no API call. |
| `login_ip` | 25 | 15 min | IP | ✅ auth_ui login | Supplements the DB per-account lockout (5 fails / 15 min). |
| `export` | 10 | 10 min | user/session | ✅ Export page | Gates actual PDF generation (not the cached re-display of a ready report). |
| `screener_scan` | 60 | 5 min | user/session | ⏳ optional | Screener scan is already cache-backed (re-runs hit cache), so abuse risk is low; wire only if a specific abuse pattern appears (would need per-scan dedup like the Deep Dive). |
| `signup_ip` | 10 | 1 hour | IP | ✅ auth_ui signup | First condition in the submit chain, so even invalid submissions consume a token (spam protection). |
| `anon_page` | 120 | 1 min | IP/session | ⏳ pending | General anonymous page loads. |

## Response behavior

- Over-limit surfaces a **calm, useful message** with an approximate wait time
  (from the counter TTL). It never exposes the internal quota architecture.
- No feature hard-crashes on the limiter — every call site wraps the check so a
  limiter error can't break a working page.

## How to adjust

Edit the `(limit, window)` tuples in `POLICIES`. Changes take effect on the next
deploy. To add a new limit: add an entry to `POLICIES`, then call
`ratelimit.guard("<action>")` (or `limit_action(actor, "<action>")`) at the
protected code path and handle the `(allowed, retry_after)` result.

## Redis keys / expiration

- Keys: `rl:<action>:<actor>` (e.g. `rl:ai_research:u42`).
- Each key's TTL equals its policy window, so keys self-expire — no manual
  cleanup and no unbounded growth.

## Tests

`tests/test_ratelimit.py` — within-limit, over-limit + retry-after, window
reset, key independence, policy application, unknown-action no-op, backend
reporting (exercises the in-process fallback path deterministically).
