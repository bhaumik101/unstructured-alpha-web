# pages/37_Legal.py
# Unstructured Alpha — Privacy Policy & Terms of Service
#
# Combined legal page. Keeps everything in one place rather than two separate
# pages that are harder to navigate. Covers:
#   - Privacy Policy (GDPR / CCPA compliant boilerplate for a SaaS)
#   - Terms of Service (no investment advice disclaimer, subscription terms)
#   - Refund Policy (Stripe 30-day policy)
#
# Keep this page in plain, readable English. Legalese reduces trust.

import streamlit as st

st.set_page_config(
    page_title="Privacy & Terms — Unstructured Alpha",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.header import render_header, render_sidebar_base, render_page_header
from utils.theme import inject_premium_css

render_header("Legal")
render_sidebar_base()
inject_premium_css()

render_page_header(
    "Privacy & Terms",
    "What we collect, how we use it, and the rules of the road.",
    icon="⚖️",
)

_tab_priv, _tab_tos, _tab_refund = st.tabs(
    ["Privacy Policy", "Terms of Service", "Refund Policy"]
)

# ── Privacy Policy ────────────────────────────────────────────────────────────
with _tab_priv:
    st.markdown("""
<div style="font-family:Inter,sans-serif;color:#C5CCDE;line-height:1.75;max-width:800px;">

<p style="font-size:0.78rem;color:#8892AA;">Last updated: July 5, 2026 &nbsp;·&nbsp; Unstructured Alpha</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">What we collect</h3>
<p>
When you create an account, we store your <strong>email address</strong> and a
<strong>salted hash of your password</strong> — we never store your password in plain text.
If you subscribe to Pro, Stripe processes your payment; we receive only a customer ID and
subscription status — not your card number, bank details, or billing address.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">What we don't collect</h3>
<p>
We do not use tracking cookies, ad pixels, or behavioral analytics. We do not sell or share
your data with third parties for marketing. We do not collect your real name, phone number,
or mailing address.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Cookies</h3>
<p>
We set one first-party cookie (<code>ua_remember</code>) only when you check "Remember me"
at login. This cookie stores a secure token — not your password — and expires after 30 days.
It is used solely to restore your session without requiring a new login. You can delete it at
any time by logging out.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Third-party services</h3>
<p>
We use <strong>Resend</strong> to send transactional emails (verification codes, digests,
alerts). We use <strong>Stripe</strong> for payment processing. Both operate under their own
privacy policies. We use <strong>Render</strong> to host the application; application logs
may be retained by Render for up to 30 days.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Data retention</h3>
<p>
Account data is retained for as long as your account is active. You can request deletion at
any time by emailing <a href="mailto:privacy@unstructuredalpha.com" style="color:#00C8E0;">privacy@unstructuredalpha.com</a>.
We will delete your account, email address, and all associated watchlist/alert data within
7 business days of receiving a verified deletion request.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Your rights</h3>
<p>
Under GDPR and CCPA, you have the right to access, correct, export, or delete your personal
data. To exercise any of these rights, contact
<a href="mailto:privacy@unstructuredalpha.com" style="color:#00C8E0;">privacy@unstructuredalpha.com</a>.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Changes to this policy</h3>
<p>
If we make material changes, we'll send an email to your registered address at least 14 days
before the change takes effect. The "Last updated" date at the top of this page will always
reflect the current version.
</p>

</div>
""", unsafe_allow_html=True)

# ── Terms of Service ──────────────────────────────────────────────────────────
with _tab_tos:
    st.markdown("""
<div style="font-family:Inter,sans-serif;color:#C5CCDE;line-height:1.75;max-width:800px;">

<p style="font-size:0.78rem;color:#8892AA;">Last updated: July 5, 2026 &nbsp;·&nbsp; Unstructured Alpha</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">1. Not financial advice</h3>
<p>
<strong style="color:#FF4D6A;">Unstructured Alpha is a research and signal intelligence tool,
not a registered investment adviser.</strong> Nothing on this platform constitutes investment
advice, a recommendation to buy or sell any security, or a solicitation to invest.
Confluence Scores, signal analyses, and AI-generated summaries are educational tools.
You are solely responsible for your own investment decisions.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">2. Use of the service</h3>
<p>
By creating an account, you agree to use Unstructured Alpha for lawful purposes only.
You may not scrape, redistribute, or resell data from this platform. You may not attempt
to reverse-engineer, overload, or interfere with the service. One account per person;
sharing accounts is not permitted.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">3. Pro subscription</h3>
<p>
Pro subscriptions are billed monthly or annually via Stripe. Prices are shown on the
Upgrade page and are in USD. We reserve the right to change pricing with 30 days' notice
to current subscribers. Trials begin on the date you start checkout; you will not be
charged until the trial period ends. You can cancel at any time from your profile page
and access will continue until the end of the current billing period.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">4. Data accuracy</h3>
<p>
Signal data is sourced from FRED (Federal Reserve), SEC EDGAR, FINRA, EIA, and public
market data. We make no warranties about the accuracy, completeness, or timeliness of
this data. Some signals may lag official publication dates. Synthetic or insufficient-data
warnings are displayed when data quality is below our standard threshold.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">5. Limitation of liability</h3>
<p>
To the maximum extent permitted by law, Unstructured Alpha shall not be liable for any
investment losses, financial damages, or consequential damages arising from use of this
platform. Your sole remedy for dissatisfaction with the service is to cancel your
subscription and request a refund under our refund policy.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">6. Governing law</h3>
<p>
These terms are governed by the laws of the State of Delaware, United States, without
regard to conflict of law principles.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">7. Contact</h3>
<p>
Questions about these terms:
<a href="mailto:legal@unstructuredalpha.com" style="color:#00C8E0;">legal@unstructuredalpha.com</a>
</p>

</div>
""", unsafe_allow_html=True)

# ── Refund Policy ─────────────────────────────────────────────────────────────
with _tab_refund:
    st.markdown("""
<div style="font-family:Inter,sans-serif;color:#C5CCDE;line-height:1.75;max-width:800px;">

<p style="font-size:0.78rem;color:#8892AA;">Last updated: July 5, 2026 &nbsp;·&nbsp; Unstructured Alpha</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">30-day money-back guarantee</h3>
<p>
If you're not satisfied with Pro for any reason within the first 30 days, email
<a href="mailto:support@unstructuredalpha.com" style="color:#00C8E0;">support@unstructuredalpha.com</a>
with your account email and we will issue a full refund within 5 business days.
No questions asked.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">After 30 days</h3>
<p>
After the 30-day window, subscriptions are non-refundable for the current billing period.
You can cancel at any time and your Pro access will continue until the end of the period
you've already paid for. We do not issue partial-period refunds.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">Trials</h3>
<p>
Free trials are not charged if cancelled before the trial ends. If you are charged after
a trial due to a technical issue, contact us and we will refund the charge immediately.
</p>

<h3 style="color:#E8EEFF;font-size:1.0rem;margin-top:24px;">How to request a refund</h3>
<p>
Email <a href="mailto:support@unstructuredalpha.com" style="color:#00C8E0;">support@unstructuredalpha.com</a>
from the email address associated with your account. Include "Refund Request" in the subject
line. We typically respond within 1 business day.
</p>

</div>
""", unsafe_allow_html=True)
