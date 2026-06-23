# utils/email.py
# Unstructured Alpha — Verification Email Sending (Resend)
#
# Endpoint/payload shape verified live against Resend's published API
# reference before writing this, 2026-06-21:
#   POST https://api.resend.com/emails
#   Authorization: Bearer {api_key}
#   {"from": "...", "to": [...], "subject": "...", "html": "..."}
#   -> {"id": "..."}
# Plain requests.post, not Resend's Python SDK -- consistent with every
# other third-party integration in this codebase (FRED, EIA, SEC, FINRA all
# use requests directly), and avoids adding a dependency just to wrap one
# REST call this small.
#
# Configuration -- environment variable checked FIRST, st.secrets as a
# fallback (same priority order as FRED_API_KEY/EIA_API_KEY in
# utils/fetchers.py and DATABASE_URL in utils/db.py). This matters beyond
# consistency: st.secrets only exists at all under Streamlit Cloud's
# secrets.toml mechanism, so a host without that (Render, Railway, a plain
# VPS) needs the env var path to work, not just a fallback that happens to
# never get reached:
#   RESEND_API_KEY   -- required to actually send mail.
#   RESEND_FROM_EMAIL -- optional; defaults to Resend's own test sender
#     ("onboarding@resend.dev"), which only works for sending TO the email
#     address on the Resend account itself, not arbitrary recipients --
#     real signups need a verified sending domain configured in Resend and
#     that address set here.

import os

import requests
import streamlit as st

_RESEND_API_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "Unstructured Alpha <onboarding@resend.dev>"


class EmailSendError(Exception):
    """Raised when the verification email genuinely fails to send (bad/missing
    API key, Resend API error) -- distinct from AuthError, since this is an
    infrastructure failure, not a user input mistake."""


def _get_resend_config() -> tuple[str, str]:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("RESEND_API_KEY", "")
        except Exception:
            api_key = ""

    from_email = os.environ.get("RESEND_FROM_EMAIL", "")
    if not from_email:
        try:
            from_email = st.secrets.get("RESEND_FROM_EMAIL", _DEFAULT_FROM)
        except Exception:
            from_email = _DEFAULT_FROM
    return api_key, from_email


def send_verification_email(to_email: str, code: str) -> None:
    """Send a 6-digit verification code to to_email. Raises EmailSendError
    if RESEND_API_KEY isn't configured or Resend's API rejects the request.

    TEMPORARY DIAGNOSTIC LOGGING (added 2026-06-22, remove once the "emails
    aren't arriving for arbitrary recipients" issue is confirmed fixed):
    the FIRST version of this logging never showed up in Render's logs at
    all, even though a fresh, fully-observed incognito test confirmed
    signup() really was completing successfully (the "We emailed a code"
    UI message only renders when no exception was raised) -- and the
    GitHub source for the exact deployed commit was checked directly and
    does contain these print() calls. That combination only makes sense
    as a well-known Python/Docker gotcha: stdout is FULLY buffered (not
    line-buffered) when it's not an interactive terminal, which is always
    true for a containerized process whose stdout is piped into a log
    collector -- so print() output can sit in an internal buffer
    indefinitely in a long-running server process that never naturally
    exits, instead of ever reaching the log stream. flush=True on every
    print() below forces each line out immediately rather than waiting
    on Python's buffer to fill.
    """
    api_key, from_email = _get_resend_config()
    print(f"[email] send_verification_email called: to={to_email!r} from={from_email!r} "
          f"api_key_present={bool(api_key)} api_key_prefix={api_key[:6] if api_key else None!r}",
          flush=True)
    if not api_key:
        print("[email] aborting: no RESEND_API_KEY configured", flush=True)
        raise EmailSendError(
            "No RESEND_API_KEY configured -- add one in Streamlit secrets to send real verification emails."
        )

    html = f"""
    <div style="font-family: Georgia, serif; max-width: 480px;">
        <h2 style="color:#1C2B4A;">Verify your Unstructured Alpha account</h2>
        <p>Enter this code to finish creating your account:</p>
        <div style="font-size:2rem; font-weight:700; letter-spacing:0.2em; color:#B8860B; margin: 16px 0;">
            {code}
        </div>
        <p style="color:#8B7355; font-size:0.85rem;">This code expires in 15 minutes. If you didn't request this, you can ignore this email.</p>
    </div>
    """

    try:
        resp = requests.post(
            _RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [to_email],
                "subject": "Your Unstructured Alpha verification code",
                "html": html,
            },
            timeout=15,
        )
        print(f"[email] Resend API responded: status={resp.status_code} body={resp.text[:500]!r}", flush=True)
        resp.raise_for_status()
        print(f"[email] send succeeded for to={to_email!r}", flush=True)
    except requests.RequestException as e:
        print(f"[email] send FAILED for to={to_email!r}: {type(e).__name__}: {e}", flush=True)
        raise EmailSendError(f"Failed to send verification email: {e}") from e


def send_digest_email(
    to_email: str,
    signal_flips: list[dict],
    score_movers: list[dict],
    overall_bias: str,
    bull_n: int,
    bear_n: int,
    neut_n: int,
) -> None:
    """
    Send the morning intelligence digest to a single opted-in user.
    Called by cron/send_digest.py for each opted-in user.

    signal_flips: list of {signal_id, from_status, to_status, to_score} dicts
    score_movers: list of {ticker, from_score, to_score, delta, case} dicts (top 5)
    overall_bias: "Bullish", "Bearish", or "Mixed"
    bull_n / bear_n / neut_n: current signal counts
    """
    api_key, from_email = _get_resend_config()
    print(f"[digest] send_digest_email: to={to_email!r} bias={overall_bias}", flush=True)
    if not api_key:
        raise EmailSendError("No RESEND_API_KEY configured.")

    # ── Signal flips HTML ──────────────────────────────────────────────────
    FLIP_COLOR = {"bullish": "#1B5E20", "bearish": "#7B1010", "neutral": "#8B7355",
                  "insufficient_data": "#9E9E8E"}
    FLIP_SYM   = {"bullish": "▲", "bearish": "▼", "neutral": "●", "insufficient_data": "○"}

    if signal_flips:
        flip_rows = ""
        for f in signal_flips[:6]:
            from_c = FLIP_COLOR.get(f["from_status"], "#9E9E9E")
            to_c   = FLIP_COLOR.get(f["to_status"],   "#9E9E9E")
            from_s = FLIP_SYM.get(f["from_status"], "●")
            to_s   = FLIP_SYM.get(f["to_status"],   "●")
            flip_rows += (
                f'<tr>'
                f'<td style="padding:6px 12px;font-size:0.85rem;color:#1A1612;">{f.get("signal_name", f["signal_id"])}</td>'
                f'<td style="padding:6px 12px;color:{from_c};">{from_s} {f["from_status"].title()}</td>'
                f'<td style="padding:6px 12px;font-size:1.1rem;color:#9E9E9E;">→</td>'
                f'<td style="padding:6px 12px;font-weight:700;color:{to_c};">{to_s} {f["to_status"].title()}</td>'
                f'</tr>'
            )
        flips_html = f"""
        <h3 style="color:#1C2B4A;border-bottom:2px solid #D4C9B0;padding-bottom:6px;">
            ⚡ {len(signal_flips)} Signal Flip{"s" if len(signal_flips) != 1 else ""} Since Yesterday
        </h3>
        <table style="border-collapse:collapse;width:100%;font-family:Georgia,serif;">
            {flip_rows}
        </table>
        """
    else:
        flips_html = """
        <h3 style="color:#1C2B4A;border-bottom:2px solid #D4C9B0;padding-bottom:6px;">Signal Flips</h3>
        <p style="color:#8B7355;font-size:0.85rem;">No status changes since yesterday — signals are steady.</p>
        """

    # ── Score movers HTML ──────────────────────────────────────────────────
    if score_movers:
        mover_rows = ""
        for m in score_movers[:5]:
            delta = m["delta"]
            delta_color = "#1B5E20" if delta > 0 else "#7B1010"
            delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
            mover_rows += (
                f'<tr>'
                f'<td style="padding:6px 12px;font-weight:700;font-size:0.9rem;color:#1C2B4A;">{m["ticker"]}</td>'
                f'<td style="padding:6px 12px;color:#8B7355;">{m["from_score"]:.0f} → {m["to_score"]:.0f}</td>'
                f'<td style="padding:6px 12px;font-weight:700;color:{delta_color};">{delta_str}</td>'
                f'<td style="padding:6px 12px;color:#6B6560;">{m.get("case","")}</td>'
                f'</tr>'
            )
        movers_html = f"""
        <h3 style="color:#1C2B4A;border-bottom:2px solid #D4C9B0;padding-bottom:6px;margin-top:24px;">
            📊 Biggest Score Movers (7 days)
        </h3>
        <table style="border-collapse:collapse;width:100%;font-family:Georgia,serif;">
            <tr style="font-size:0.72rem;color:#9E9E8E;letter-spacing:0.06em;text-transform:uppercase;">
                <th style="padding:4px 12px;text-align:left;">Ticker</th>
                <th style="padding:4px 12px;text-align:left;">Score</th>
                <th style="padding:4px 12px;text-align:left;">Delta</th>
                <th style="padding:4px 12px;text-align:left;">Case</th>
            </tr>
            {mover_rows}
        </table>
        """
    else:
        movers_html = """
        <h3 style="color:#1C2B4A;border-bottom:2px solid #D4C9B0;padding-bottom:6px;margin-top:24px;">
            Score Movers
        </h3>
        <p style="color:#8B7355;font-size:0.85rem;">
            No recorded score moves yet — score history builds organically as tickers get viewed.
        </p>
        """

    # ── Bias banner ────────────────────────────────────────────────────────
    bias_color = "#1B5E20" if overall_bias == "Bullish" else ("#7B1010" if overall_bias == "Bearish" else "#8B7355")
    from datetime import date
    today_str = date.today().strftime("%B %-d, %Y")

    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;color:#1A1612;">
        <div style="background:#1C2B4A;padding:18px 24px;border-radius:8px 8px 0 0;">
            <div style="font-size:0.70rem;color:#C9A84C;letter-spacing:0.12em;text-transform:uppercase;">
                Unstructured Alpha — Morning Brief
            </div>
            <div style="font-size:1.2rem;font-weight:700;color:#FAF7F0;margin-top:4px;">
                {today_str}
            </div>
        </div>

        <div style="background:#F0EBE1;padding:14px 24px;border-left:5px solid {bias_color};">
            <span style="font-size:0.72rem;color:#8B7355;text-transform:uppercase;letter-spacing:0.08em;">
                Signal Pulse
            </span>
            <br>
            <span style="font-size:1.3rem;font-weight:800;color:{bias_color};">{overall_bias}</span>
            <span style="font-size:0.85rem;color:#6B6560;margin-left:12px;">
                ▲ {bull_n} bullish &nbsp; ▼ {bear_n} bearish &nbsp; ● {neut_n} neutral
            </span>
        </div>

        <div style="background:#FFFFFF;padding:20px 24px;">
            {flips_html}
            {movers_html}

            <div style="margin-top:28px;text-align:center;">
                <a href="https://unstructuredalpha.com/Today%27s_Brief"
                   style="background:#1C2B4A;color:#FAF7F0;padding:10px 24px;border-radius:4px;
                          text-decoration:none;font-size:0.9rem;font-weight:700;">
                    Open Full Brief →
                </a>
            </div>
        </div>

        <div style="background:#F0EBE1;padding:10px 24px;border-radius:0 0 8px 8px;
                    font-size:0.72rem;color:#9E9E8E;text-align:center;">
            Unstructured Alpha · Not financial advice · All data from public sources<br>
            <a href="https://unstructuredalpha.com/Watchlist" style="color:#9E9E8E;">
                Manage digest preferences
            </a>
        </div>
    </div>
    """

    try:
        resp = requests.post(
            _RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [to_email],
                "subject": f"UA Morning Brief — {today_str}",
                "html": html,
            },
            timeout=20,
        )
        print(f"[digest] Resend responded: status={resp.status_code}", flush=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[digest] send FAILED to={to_email!r}: {e}", flush=True)
        raise EmailSendError(f"Failed to send digest to {to_email}: {e}") from e
