"""Authentication helpers for the Portfolio Tracker app."""

import hmac
import streamlit as st


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_ADMIN  = "admin"
ROLE_VIEWER = "viewer"

# ---------------------------------------------------------------------------
# Default credentials (used when secrets.toml is not configured)
# ---------------------------------------------------------------------------
_DEFAULT_USERS = {
    "admin": {
        "password":     "admin",
        "role":         ROLE_ADMIN,
        "display_name": "Portfolio Manager",
    },
    "user": {
        "password":     "user",
        "role":         ROLE_VIEWER,
        "display_name": "Portfolio Viewer",
    },
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_users() -> dict:
    """
    Returns {username: {"password": ..., "role": ..., "display_name": ...}}.

    Reads from st.secrets["users"] when available; falls back to _DEFAULT_USERS.

    secrets.toml format:

        [users.admin]
        password     = "your_admin_password"
        role         = "admin"
        display_name = "Portfolio Manager"

        [users.user]
        password     = "your_user_password"
        role         = "viewer"
        display_name = "Portfolio Viewer"
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
        if users:
            return users
    except Exception:
        pass
    return _DEFAULT_USERS


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
    """Renders the login form."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 📈 Portfolio Tracker")
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or user")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.success(f"Welcome, {get_display_name()}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
