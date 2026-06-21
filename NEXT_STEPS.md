# Unstructured Alpha — Next Session Checklist

Local HEAD is `21eb065` ("Add email verification at signup (Resend) + fix a real persistence bug"), already confirmed pushed and matching `origin/main` on GitHub. These are the open items from where we left off.

## 1. Resolve the Streamlit Cloud "old sidebar" issue
You reported the deployed app still shows the wrong build even after new tabs and a refresh. My last test (fresh, cache-busted load) showed the correct new login screen, so the mismatch is likely browser-side caching on your end, but it's not confirmed. Next session, in order:
- [ ] Fully clear site data for `unstructured-alpha.streamlit.app` (not just hard refresh) — in Chrome: site settings → Clear data, or DevTools → Application → Clear storage.
- [ ] Try a true incognito window if you haven't already.
- [ ] In the Streamlit Cloud dashboard, open "Manage app" → confirm the deployed commit hash matches `21eb065` → if not, click "Reboot app" to force a clean redeploy.
- [ ] If it still looks wrong after all of that, send a fresh screenshot and we'll dig into the actual page source rather than guessing further.

## 2. Resend domain verification (real users currently can't receive codes)
Right now `RESEND_FROM_EMAIL` uses Resend's test sender (`onboarding@resend.dev`), which **only delivers to your own Resend account email** — anyone else who signs up will never get their verification code and will be stuck.
- [ ] In Resend dashboard, add and verify a domain you own (DNS records).
- [ ] Update `RESEND_FROM_EMAIL` to an address on that domain, e.g. `Unstructured Alpha <noreply@yourdomain.com>`.
- [ ] Update the value in **both** places: local `.streamlit/secrets.toml` and Streamlit Cloud → Settings → Secrets.

## 3. Confirm Streamlit Cloud secrets match local
Double-check the Cloud dashboard secrets block has the current values for `DATABASE_URL`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `FRED_API_KEY`, `EIA_API_KEY` — local file and Cloud are configured separately and can drift.

## 4. Git hygiene before next push
There's a stale `.git/index.lock` in the project that my sandbox couldn't clear (a recurring sandbox-only file-lock quirk, not a real git problem). Before your next commit:
- [ ] Run `git status` locally on your machine — if it complains about a lock, delete `.git/index.lock` by hand, then proceed normally.

## 5. Known gaps (stated in code comments, not urgent — flagged for awareness)
- [ ] No password-reset flow yet.
- [ ] No rate-limiting on login or verification-code attempts.
- [ ] No "remember me" — every new browser session requires logging in again (Streamlit has no built-in cookie API).

Pick any of these up whenever you're ready — none are blocking, but #1 and #2 are the two that affect whether a real outside user can actually use the app today.
