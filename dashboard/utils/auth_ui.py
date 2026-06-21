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
# st.session_state["user"] is the source of truth for "who's logged in" --
# Streamlit session_state lives only for the current browser session/tab,
# so logging in does NOT persist across a real browser restart (see
# utils/auth.py's module docstring for why a "remember me" cookie isn't
# built into this version). st.session_state["pending_verification_email"]
# tracks an account that exists but hasn't entered its emailed code yet --
# set right after signup, or when login() reports EmailNotVerifiedError.

import streamlit as st

from utils.auth import signup, login, verify_email, resend_verification_code, AuthError, EmailNotVerifiedError
from utils.email import EmailSendError


def _render_verification_form() -> None:
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
    """
    if "user" in st.session_state:
        return st.session_state["user"]

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
            _render_verification_form()
            st.stop()

        tab_login, tab_signup = st.tabs(["Log In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Enter both your email and password.")
                else:
                    try:
                        user = login(email, password)
                        st.session_state["user"] = user
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
            "Note: you'll need to log in again each time you start a new browser session — "
            "there's no \"remember me\" yet."
        )

    st.stop()


def logout() -> None:
    """Clear the current session's login. Caller is responsible for st.rerun()."""
    st.session_state.pop("user", None)
