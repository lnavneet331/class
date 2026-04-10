"""Authentication helpers for the Portfolio Tracker app."""

import hashlib
import streamlit as st


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_ADMIN  = "admin"
ROLE_VIEWER = "viewer"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_users() -> dict:
    """
    Returns {username: {"password_hash": ..., "role": ..., "display_name": ...}}.

    Credentials are read from st.secrets["users"] which should look like:

        [users.admin]
        password = "your_admin_password"
        role     = "admin"
        display_name = "Portfolio Manager"

        [users.father]
        password = "fathers_password"
        role     = "viewer"
        display_name = "Dad's Portfolio"
    """
    try:
        raw = st.secrets["users"]
        users = {}
        for uname, udata in raw.items():
            users[uname] = {
                "password_hash": _hash(udata["password"]),
                "role":          udata.get("role", ROLE_VIEWER),
                "display_name":  udata.get("display_name", uname.title()),
            }
        return users
    except Exception:
        # Fallback for local dev / demo when secrets.toml is absent.
        # CHANGE THESE DEFAULTS before deploying!
        return {
            "admin": {
                "password_hash": _hash("admin123"),
                "role":          ROLE_ADMIN,
                "display_name":  "Portfolio Manager",
            },
            "father": {
                "password_hash": _hash("father123"),
                "role":          ROLE_VIEWER,
                "display_name":  "Dad's Portfolio",
            },
        }


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
    """Validate credentials and store session info. Returns True on success."""
    users = _get_users()
    uname = username.strip().lower()
    if uname in users and users[uname]["password_hash"] == _hash(password):
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
    """Renders the login form and handles submission. Returns nothing."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/investment-portfolio.png", width=80)
        st.markdown("## 📈 Portfolio Tracker")
        st.markdown("---")
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
