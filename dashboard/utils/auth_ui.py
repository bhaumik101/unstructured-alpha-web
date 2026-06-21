# utils/auth_ui.py
# Unstructured Alpha — Login/Signup Gate
#
# require_login() is called once, at the very top of app.py, before the
# page router runs. If nobody is logged in this session, it renders a
# login/signup form and calls st.stop() so nothing else in the app executes
# -- this is what makes every page require an account, not just the Alerts
# page where per-user data actually lives.
#
# st.session_state["user"] is the source of truth for "who's logged in" --
# Streamlit session_state lives only for the current browser session/tab,
# so logging in does NOT persist across a real browser restart (see
# utils/auth.py's module docstring for why a "remember me" cookie isn't
# built into this version).

import streamlit as st

from utils.auth import signup, login, AuthError


def require_login() -> dict:
    """
    Returns the logged-in user dict ({"id", "email"}) if already
    authenticated this session. Otherwise renders the login/signup gate
    and calls st.stop() -- this function never returns None; it either
    returns a real user or halts the script.
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
                        user = signup(email, password)
                        st.session_state["user"] = user
                        st.success("Account created — you're in.")
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
