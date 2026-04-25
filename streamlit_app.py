# streamlit_app.py — Root entry point for Streamlit Community Cloud deployment.
#
# Streamlit Cloud looks for this file by default.
# It adds the portfolio_tracker directory to sys.path and then runs the app.

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.join(_ROOT, "portfolio_tracker")

if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

# Execute the portfolio tracker app in this context.
# st.set_page_config() inside app.py will be the first Streamlit call, as required.
exec(  # noqa: S102
    compile(
        open(os.path.join(_APP_DIR, "app.py")).read(),
        os.path.join(_APP_DIR, "app.py"),
        "exec",
    ),
    {"__file__": os.path.join(_APP_DIR, "app.py"), "__name__": "__main__"},
)
