"""Authentication helpers for the Portfolio Tracker app."""

import hmac
import streamlit as st


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_ADMIN  = "admin"
ROLE_VIEWER = "viewer"

# ---------------------------------------------------------------------------
# Demo / fallback credentials
# These are shown on the login page when secrets.toml is not configured.
# Anyone can log in with these in demo mode.
# ---------------------------------------------------------------------------
_DEMO_USERS = {
    "admin": {
        "password":     "admin123",
        "role":         ROLE_ADMIN,
        "display_name": "Portfolio Manager (Demo)",
    },
    "father": {
        "password":     "father123",
        "role":         ROLE_VIEWER,
        "display_name": "Dad's Portfolio (Demo)",
    },
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_users() -> tuple[dict, bool]:
    """
    Returns (users_dict, is_demo).

    Reads from st.secrets["users"] when available; falls back to _DEMO_USERS.

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
        if users:
            return users, False
    except Exception:
        pass
    return _DEMO_USERS, True


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
    users, _ = _get_users()
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
    """Renders the login form with demo credentials banner when in demo mode."""
    _, is_demo = _get_users()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 📈 Portfolio Tracker")
        st.markdown("---")

        if is_demo:
            st.info(
                "**🎮 Demo Mode** — no secrets.toml detected.\n\n"
                "Use the credentials below to explore the app with sample data:\n\n"
                "| Username | Password | Role |\n"
                "|---|---|---|\n"
                "| `admin` | `admin123` | Full access + add transactions |\n"
                "| `father` | `father123` | Read-only dashboard |\n\n"
                "_To use your own data, configure `secrets.toml` — see README._"
            )

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or father")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.success(f"Welcome, {get_display_name()}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
