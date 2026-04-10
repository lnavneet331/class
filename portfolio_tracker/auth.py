"""Authentication helpers for the Portfolio Tracker app."""

import hmac
import streamlit as st


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_ADMIN  = "admin"
ROLE_VIEWER = "viewer"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_users() -> dict | None:
    """
    Returns {username: {"password": ..., "role": ..., "display_name": ...}},
    or None if credentials are not configured in secrets.toml.

    Passwords are stored in plaintext in secrets.toml and compared using
    hmac.compare_digest (constant-time) at login time — they are never
    persisted or hashed to disk.

    secrets.toml format:

        [users.admin]
        password     = "your_admin_password"
        role         = "admin"
        display_name = "Portfolio Manager"

        [users.father]
        password     = "fathers_password"
        role         = "viewer"
        display_name = "Dad's Portfolio"
    """
    try:
        raw = st.secrets["users"]
        users = {}
        for uname, udata in raw.items():
            users[uname] = {
                "password":     udata["password"],
                "role":         udata.get("role", ROLE_VIEWER),
                "display_name": udata.get("display_name", uname.title()),
            }
        return users if users else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_role() -> str | None:
    return st.session_state.get("role")


def get_display_name() -> str:
    return st.session_state.get("display_name", "")


def login(username: str, password: str) -> bool:
    """Validate credentials and populate session state. Returns True on success."""
    users = _get_users()
    if users is None:
        return False
    uname = username.strip().lower()
    if uname in users and hmac.compare_digest(password, users[uname]["password"]):
        st.session_state["authenticated"] = True
        st.session_state["username"]      = uname
        st.session_state["role"]          = users[uname]["role"]
        st.session_state["display_name"]  = users[uname]["display_name"]
        return True
    return False


def logout():
    for key in ["authenticated", "username", "role", "display_name"]:
        st.session_state.pop(key, None)


def render_login_page():
    """Renders the login form (or a setup warning). Returns nothing."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 📈 Portfolio Tracker")
        st.markdown("---")

        if _get_users() is None:
            st.warning(
                "⚠️ **Credentials not configured.**\n\n"
                "Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`, "
                "set your passwords, and restart the app.\n\n"
                "See `README.md` for full setup instructions."
            )
            st.stop()

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or father")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.success(f"Welcome, {get_display_name()}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
