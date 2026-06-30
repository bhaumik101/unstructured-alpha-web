# pages/29_Upgrade.py
# Unstructured Alpha — Upgrade / Pricing Page
#
# Handles three distinct states in a single page:
#
#   1. ?stripe_session_id=xxx  — returning from Stripe Checkout success.
#      Verifies the session via Stripe API, upgrades DB tier, shows
#      confirmation. If the query param is present, this is always the
#      first thing rendered (before any other UI) so the upgrade lands
#      the moment the user is redirected back from Stripe.
#
#   2. User is already Pro — show current plan status + "Manage Subscription"
#      button (launches Stripe Customer Portal).
#
#   3. User is Free (or anonymous) — show pricing cards with upgrade CTA.
#
# The Stripe Checkout redirect flow:
#   User clicks "Upgrade" → create_checkout_session() → redirect to stripe.com
#   Stripe hosted checkout → payment → redirect to:
#     /Upgrade?stripe_session_id={CHECKOUT_SESSION_ID}
#   This page's handle_checkout_success() verifies + upgrades user in DB.

import os

import streamlit as st

from utils.theme import BG_PAGE, BG_CARD, TEXT_PRIMARY, PURPLE, CYAN, GREEN, AMBER

st.set_page_config(
    page_title="Upgrade — Unstructured Alpha",
    page_icon="🔓",
    layout="centered",
)

from utils.header import render_header
from utils.auth_ui import get_cookies, try_restore_session
from utils.billing import (
    get_user_tier, create_checkout_session, handle_checkout_success,
    create_portal_session, get_stripe_ids, check_and_sync_subscription,
    PRO_FEATURES,
)

render_header()

# ── Base URL helper ───────────────────────────────────────────────────────────
def _base_url() -> str:
    """Best-effort detection of the app's public URL for Stripe redirect targets."""
    # Render sets RENDER_EXTERNAL_URL; fall back to localhost for local dev.
    return os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8501")


def _page_url(path: str = "/Upgrade") -> str:
    return f"{_base_url()}{path}"


# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
.pricing-card {{
    background: {BG_CARD};
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 28px 24px;
    height: 100%;
}}
.pricing-card.pro-card {{
    border-color: {PURPLE};
    box-shadow: 0 0 28px rgba(124,58,237,0.18);
}}
.plan-badge {{
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 12px;
}}
.free-badge  {{ background: rgba(255,255,255,0.06); color: #8892B0; }}
.pro-badge   {{ background: linear-gradient(90deg,{PURPLE},{CYAN}); color:#fff; }}
.plan-price  {{ font-size: 2.4rem; font-weight: 800; color: {TEXT_PRIMARY}; line-height: 1; }}
.plan-price span {{ font-size: 1rem; font-weight: 400; color: #8892B0; }}
.plan-name   {{ font-size: 1.1rem; font-weight: 700; color: {TEXT_PRIMARY}; margin-bottom: 4px; }}
.plan-desc   {{ font-size: 0.85rem; color: #8892B0; margin-bottom: 20px; }}
.feat-row    {{ display:flex; align-items:flex-start; gap:8px; margin-bottom:10px; font-size:0.875rem; color:#B8C0D4; }}
.feat-check  {{ color:{GREEN}; flex-shrink:0; margin-top:1px; }}
.feat-x      {{ color:#4A5063; flex-shrink:0; margin-top:1px; }}
.success-box {{
    background: rgba(0,213,102,0.08);
    border: 1px solid rgba(0,213,102,0.3);
    border-radius: 12px;
    padding: 24px 28px;
    text-align: center;
    margin-bottom: 28px;
}}
.pro-status-box {{
    background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(0,200,224,0.06));
    border: 1px solid {PURPLE};
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 28px;
}}
.trial-banner {{
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.8rem;
    color: {AMBER};
    text-align: center;
    margin-bottom: 20px;
}}
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
cookies = get_cookies()
user    = try_restore_session(cookies)

# ── State 1: Returning from Stripe Checkout ───────────────────────────────────
params = st.query_params
stripe_session_id = params.get("stripe_session_id", "")

if stripe_session_id:
    if not user:
        st.error("Session expired. Please log in again and visit this page.")
        st.stop()

    # Prevent double-processing the same session_id within one browser session
    already_processed = st.session_state.get(f"_stripe_done_{stripe_session_id}", False)
    if not already_processed:
        with st.spinner("Verifying your payment with Stripe…"):
            result = handle_checkout_success(stripe_session_id, user["id"])
        st.session_state[f"_stripe_done_{stripe_session_id}"] = True
        # Bust the tier cache so require_pro() sees the new value immediately
        st.session_state.pop(f"_tier_{user['id']}", None)
    else:
        result = {"ok": True, "tier": get_user_tier(user["id"]), "error": ""}

    if result["ok"]:
        st.markdown("""
        <div class="success-box">
            <div style="font-size:2.5rem;margin-bottom:8px;">🎉</div>
            <div style="font-size:1.35rem;font-weight:700;color:#00D566;margin-bottom:6px;">Welcome to Pro!</div>
            <div style="font-size:0.9rem;color:#8892B0;">Your subscription is active. All Pro features are now unlocked.</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("→ Ticker Deep Dive", use_container_width=True, type="primary"):
                st.switch_page("pages/3_Ticker_Deep_Dive.py")
        with col2:
            if st.button("→ Factor Exposure", use_container_width=True):
                st.switch_page("pages/27_Factor_Exposure.py")

        # Clear the query param so a refresh doesn't re-run handle_checkout_success
        st.query_params.clear()
    else:
        st.error(f"Payment verification failed: {result['error']}. Please contact support at bpgiri2005@gmail.com.")
        if st.button("Try again"):
            st.query_params.clear()
            st.rerun()
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;margin-bottom:32px;">
    <div style="font-size:1.9rem;font-weight:800;color:{TEXT_PRIMARY};margin-bottom:6px;">
        Simple, transparent pricing
    </div>
    <div style="font-size:0.95rem;color:#8892B0;">
        Start free. Upgrade when you need the full signal stack.
    </div>
</div>
""", unsafe_allow_html=True)

# ── State 2: Already Pro ──────────────────────────────────────────────────────
if user:
    cache_key = f"_tier_{user['id']}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = get_user_tier(user["id"])
    current_tier = st.session_state[cache_key]

    if current_tier == "pro":
        customer_id, sub_id = get_stripe_ids(user["id"])
        st.markdown(f"""
        <div class="pro-status-box">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="font-size:1.5rem;">🟣</span>
                <span style="font-size:1.1rem;font-weight:700;color:{TEXT_PRIMARY};">You're on Pro</span>
                <span style="font-size:0.7rem;font-weight:700;padding:3px 10px;border-radius:20px;
                       background:linear-gradient(90deg,{PURPLE},{CYAN});color:#fff;letter-spacing:0.1em;">ACTIVE</span>
            </div>
            <div style="font-size:0.875rem;color:#8892B0;">
                All Pro features are unlocked. Use the button below to manage your subscription,
                update your payment method, or cancel.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if customer_id and st.button("Manage Subscription ↗", use_container_width=True, type="primary"):
                try:
                    portal_url = create_portal_session(customer_id, return_url=_page_url("/Upgrade"))
                    st.markdown(f"""
                    <script>window.open("{portal_url}", "_blank");</script>
                    <div style="font-size:0.85rem;color:{CYAN};">
                        Opening Stripe portal... <a href="{portal_url}" target="_blank">Click here</a> if it didn't open.
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not open portal: {e}")
        with col2:
            if st.button("Re-sync subscription status", use_container_width=True):
                with st.spinner("Checking Stripe…"):
                    live_tier = check_and_sync_subscription(user["id"])
                    st.session_state[cache_key] = live_tier
                if live_tier == "pro":
                    st.success("Subscription confirmed active.")
                else:
                    st.warning("Subscription no longer active — downgraded to Free.")
                    st.rerun()
        st.stop()

# ── State 3: Free plan (or anonymous) — pricing cards ────────────────────────
st.markdown("""
<div class="trial-banner">
    ✨ Pro includes a <strong>7-day free trial</strong> — no charge until the trial ends, cancel anytime.
</div>
""", unsafe_allow_html=True)

free_features = [
    ("Signal Dashboard (38 signals)", True),
    ("Ticker Deep Dive (any ticker)", True),
    ("Market Heatmap & Sector Map", True),
    ("Congress Tracker", True),
    ("Today's Brief & Weekly Brief", True),
    ("Watchlist (up to 5 tickers)", True),
    ("Morning digest email", False),
    ("Factor Exposure (Fama-French)", False),
    ("PDF Research Reports", False),
    ("Signal Backtester", False),
    ("Portfolio Analyzer", False),
    ("Unlimited watchlist tickers", False),
]

pro_features_display = [
    "Everything in Free",
    "Factor Exposure — Fama-French regression",
    "PDF Research Reports (any ticker)",
    "Signal Backtester",
    "Portfolio Analyzer",
    "Options Flow Feed",
    "Unlimited watchlist tickers",
    "Morning digest email",
    "Priority support",
]

col_free, col_pro = st.columns(2, gap="large")

with col_free:
    st.markdown("""
    <div class="pricing-card">
        <div class="plan-badge free-badge">Free</div>
        <div class="plan-name">Free</div>
        <div class="plan-price">$0 <span>/ month</span></div>
        <div class="plan-desc">Full signal visibility. No credit card required.</div>
        <hr style="border-color:rgba(255,255,255,0.06);margin:16px 0;">
    """, unsafe_allow_html=True)

    for feat, included in free_features:
        icon = '<span class="feat-check">✓</span>' if included else '<span class="feat-x">✗</span>'
        color = "#B8C0D4" if included else "#4A5063"
        st.markdown(
            f'<div class="feat-row">{icon}<span style="color:{color};">{feat}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if not user:
        pass  # anonymous — no action needed for Free column
    elif current_tier == "free":  # type: ignore[possibly-undefined]
        st.markdown('<div style="margin-top:16px;text-align:center;font-size:0.85rem;color:#8892B0;">← Your current plan</div>', unsafe_allow_html=True)

with col_pro:
    st.markdown(f"""
    <div class="pricing-card pro-card">
        <div class="plan-badge pro-badge">Pro</div>
        <div class="plan-name">Pro</div>
        <div class="plan-price">$15 <span>/ month</span></div>
        <div class="plan-desc">Full alternative data stack. 7-day free trial.</div>
        <hr style="border-color:rgba(124,58,237,0.25);margin:16px 0;">
    """, unsafe_allow_html=True)

    for feat in pro_features_display:
        st.markdown(
            f'<div class="feat-row"><span class="feat-check">✓</span><span>{feat}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Upgrade button ────────────────────────────────────────────────────────────
if not user:
    st.markdown("""
    <div style="text-align:center;margin:8px 0 4px;font-size:0.9rem;color:#8892B0;">
        Sign in or create a free account first, then upgrade.
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        if st.button("Sign In / Create Account", use_container_width=True, type="primary"):
            st.switch_page("pages/home_page.py")
else:
    _, col, _ = st.columns([0.5, 1.2, 0.5])
    with col:
        checkout_disabled = False
        btn_label = "🔓 Start 7-Day Free Trial — then $15/mo"

        try:
            # Validate env vars before showing the button as active
            from utils.billing import get_stripe_price_id as _check_pid
            _check_pid()
        except RuntimeError:
            checkout_disabled = True
            btn_label = "⚠️ Stripe not configured yet"

        if st.button(btn_label, type="primary", use_container_width=True, disabled=checkout_disabled):
            try:
                success_url = _page_url(f"/Upgrade") + "?stripe_session_id={{CHECKOUT_SESSION_ID}}"
                cancel_url  = _page_url("/Upgrade") + "?stripe_cancel=1"
                checkout_url = create_checkout_session(
                    user_id=user["id"],
                    user_email=user["email"],
                    success_url=success_url,
                    cancel_url=cancel_url,
                )
                # Redirect to Stripe Checkout via meta-refresh (works without JS)
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={checkout_url}">',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'Redirecting to Stripe… <a href="{checkout_url}">Click here</a> if not redirected.',
                    unsafe_allow_html=True,
                )
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Could not create checkout session: {e}")

        st.markdown("""
        <div style="text-align:center;font-size:0.75rem;color:#4A5063;margin-top:10px;">
            Secured by Stripe · Cancel anytime · No hidden fees
        </div>
        """, unsafe_allow_html=True)

# ── Stripe cancel return ──────────────────────────────────────────────────────
if params.get("stripe_cancel"):
    st.info("No worries — you weren't charged. You can upgrade any time.")
    st.query_params.clear()

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.05rem;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:16px;'>Frequently asked questions</div>", unsafe_allow_html=True)

with st.expander("What happens after the 7-day free trial?"):
    st.markdown("You'll be charged $15/month starting on day 8. You can cancel any time before that from the 'Manage Subscription' portal — no charge if you cancel during the trial.")

with st.expander("Can I cancel anytime?"):
    st.markdown("Yes. Click 'Manage Subscription' above (when on Pro) to access the Stripe Customer Portal where you can cancel, update your card, or download invoices. Cancellations take effect at the end of your current billing period.")

with st.expander("What payment methods are accepted?"):
    st.markdown("All major credit and debit cards (Visa, Mastercard, Amex, Discover) via Stripe. No PayPal or crypto currently.")

with st.expander("Is this platform affiliated with any broker or investment firm?"):
    st.markdown("No. Unstructured Alpha is an independent research tool. Nothing here is investment advice. All signals are educational and informational only.")

with st.expander("What data sources power the signals?"):
    st.markdown("FRED (Federal Reserve), EIA (Energy Information Administration), SEC EDGAR (insider trades, 13F filings, congressional trades), FINRA (short interest), yfinance (price data), and Google Trends. All public sources.")
