# utils/auth_ui.py
# Unstructured Alpha — Login/Signup/Email-Verification Gate
#
# require_login() is called once, at the very top of app.py, before the
# page router runs. If nobody is logged in this session, it renders the
# login/signup form (or, mid-verification, the code-entry form) and calls
# st.stop() so nothing else in the app executes -- this is what makes
# every page require a verified account, not just the Alerts page where
# per-user data actually lives.
#
# st.session_state["user"] is the source of truth for "who's logged in"
# WITHIN the current browser tab session -- but that alone resets on
# every browser restart, which is the exact "log in over and over" problem
# the "remember me" cookie below fixes. Streamlit itself still has no
# built-in cookie API (st.login()/st.user are OIDC-only, delegating to an
# external identity provider like Google -- a different mechanism
# entirely from this app's own email+password accounts, not a drop-in fit
# here), so this uses the third-party streamlit-cookies-manager-v2
# component instead. st.session_state["pending_verification_email"]
# tracks an account that exists but hasn't entered its emailed code yet --
# set right after signup, or when login() reports EmailNotVerifiedError.
#
# Cookie component lifecycle, the part that's easy to get wrong: the
# CookieManager's underlying browser component needs one render round-trip
# before cookies.ready() is True. require_login() checks ready() BEFORE
# checking for a remember-me cookie and calls st.stop() if not ready yet --
# skipping that check would mean treating "cookie data hasn't arrived yet"
# the same as "no cookie exists," which would show the login form for a
# split second to someone who's actually already remembered, on every
# single fresh page load.

import streamlit as st
from streamlit_cookies_manager import CookieManager

from utils.auth import (
    signup, login, verify_email, resend_verification_code, AuthError, EmailNotVerifiedError,
    issue_remember_token, verify_remember_token, revoke_remember_token,
)
from utils.email import EmailSendError

_REMEMBER_COOKIE_NAME = "ua_remember_token"


def _render_verification_form(cookies: CookieManager) -> None:
    email = st.session_state["pending_verification_email"]

    # A message queued by the signup handler before routing here (e.g. "the
    # account was created but the email failed to send") -- queued instead
    # of shown directly via st.error() there, because that call immediately
    # follows an st.rerun(): Streamlit reruns restart script execution from
    # scratch, so anything rendered in the OLD run (including an error
    # message) is gone before the user ever sees it. This was caught live,
    # not assumed -- a real first version of this silently swallowed the
    # "email failed to send" warning behind the rerun.
    pending_message = st.session_state.pop("pending_verification_message", None)
    if pending_message:
        st.warning(pending_message)

    st.info(f"We emailed a 6-digit code to **{email}**. Enter it below to finish setting up your account.")

    with st.form("verify_form"):
        code = st.text_input("Verification code", max_chars=6, key="verify_code")
        submitted = st.form_submit_button("Verify", type="primary", use_container_width=True)
    if submitted:
        if not code:
            st.error("Enter the 6-digit code from your email.")
        else:
            try:
                user = verify_email(email, code)
                st.session_state["user"] = user
                # Auto-remember right after verification, no checkbox shown
                # here -- the device that just typed in the emailed code is,
                # by construction, the account owner's own device, so
                # defaulting to "remember this device" is the helpful
                # choice rather than logging them out again moments later.
                token = issue_remember_token(user["id"])
                cookies[_REMEMBER_COOKIE_NAME] = token
                cookies.save()
                st.session_state["_remember_token"] = token
                st.session_state.pop("pending_verification_email", None)
                st.rerun()
            except AuthError as e:
                st.error(str(e))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resend code", use_container_width=True):
            try:
                resend_verification_code(email)
                st.success("A new code is on its way.")
            except (AuthError, EmailSendError) as e:
                st.error(str(e))
    with col2:
        if st.button("Use a different email", use_container_width=True):
            st.session_state.pop("pending_verification_email", None)
            st.rerun()


def require_login() -> dict:
    """
    Returns the logged-in user dict ({"id", "email"}) if already
    authenticated this session. Otherwise renders the login/signup gate
    (or the email-verification step, if mid-signup) and calls st.stop() --
    this function never returns None; it either returns a real, verified
    user or halts the script.

    Checks, in order: (1) already logged in this tab session -- the fast
    path, no cookie component touched at all; (2) a valid "remember me"
    cookie from a past session -- auto-logs in with no form shown; (3)
    falls through to the actual login/signup form.
    """
    if "user" in st.session_state:
        return st.session_state["user"]

    cookies = CookieManager()
    if not cookies.ready():
        st.stop()

    remember_token = cookies.get(_REMEMBER_COOKIE_NAME)
    if remember_token:
        remembered_user = verify_remember_token(remember_token)
        if remembered_user:
            st.session_state["user"] = remembered_user
            st.session_state["_remember_token"] = remember_token
            return remembered_user
        # Stale, expired, or already-revoked -- clear it so this same dead
        # cookie isn't re-checked (and re-found invalid) on every page load.
        del cookies[_REMEMBER_COOKIE_NAME]
        cookies.save()

    st.markdown("""
    <div style="text-align:center; margin-top:40px; margin-bottom:20px;">
        <div style="font-size:2.2rem;font-weight:700;color:#1C2B4A;font-family:Georgia,serif;">
            UNSTRUCTURED <span style="color:#B8860B;">ALPHA</span>
        </div>
        <div style="font-size:0.9rem;color:#8B7355;font-style:italic;font-family:Georgia,serif;">
            Alternative Data Intelligence — what's coming, not what happened
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        if "pending_verification_email" in st.session_state:
            _render_verification_form(cookies)
            st.stop()

        tab_login, tab_signup = st.tabs(["Log In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                remember_me = st.checkbox(
                    "Remember me on this device", value=True, key="login_remember_me",
                )
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Enter both your email and password.")
                else:
                    try:
                        user = login(email, password)
                        st.session_state["user"] = user
                        if remember_me:
                            token = issue_remember_token(user["id"])
                            cookies[_REMEMBER_COOKIE_NAME] = token
                            cookies.save()
                            st.session_state["_remember_token"] = token
                        st.rerun()
                    except EmailNotVerifiedError:
                        st.session_state["pending_verification_email"] = email.strip().lower()
                        st.rerun()
                    except AuthError as e:
                        st.error(str(e))

        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password (min 8 characters)", type="password", key="signup_password")
                password2 = st.text_input("Confirm password", type="password", key="signup_password2")
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Enter both an email and a password.")
                elif password != password2:
                    st.error("Passwords don't match.")
                else:
                    try:
                        signup(email, password)
                        st.session_state["pending_verification_email"] = email.strip().lower()
                        st.rerun()
                    except EmailSendError as e:
                        # Account was created (signup() only raises this AFTER
                        # the insert succeeds), but the user can't verify yet --
                        # route them to the same screen so "Resend code" can
                        # retry once email sending is actually working. The
                        # warning is QUEUED (read by _render_verification_form
                        # on the next run), not shown directly here -- this
                        # st.rerun() would wipe out an st.error() called
                        # immediately before it, since a rerun restarts script
                        # execution from scratch.
                        st.session_state["pending_verification_email"] = email.strip().lower()
                        st.session_state["pending_verification_message"] = (
                            f"Account created, but the verification email couldn't be sent: {e}"
                        )
                        st.rerun()
                    except AuthError as e:
                        st.error(str(e))

        st.caption(
            "\"Remember me\" keeps you logged in on this device for 30 days. "
            "Uncheck it on a shared or public computer."
        )

    st.stop()


def logout() -> None:
    """
    Clear the current session's login, and revoke + clear any "remember
    me" cookie too -- so logging out actually ends the persistent session,
    not just the in-tab one. The DB-side revoke always runs regardless of
    cookie-component readiness (it's a plain DB call with no browser
    round-trip dependency); the browser-side cookie deletion is
    best-effort if the component isn't ready, since the token is already
    dead server-side either way. Caller is responsible for st.rerun().
    """
    token = st.session_state.pop("_remember_token", None)
    if token:
        revoke_remember_token(token)
        cookies = CookieManager()
        if cookies.ready():
            del cookies[_REMEMBER_COOKIE_NAME]
            cookies.save()
    st.session_state.pop("user", None)
