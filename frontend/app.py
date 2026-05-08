import sys
import os
from pathlib import Path

# Add frontend/ dir to sys.path so views/ and utils/ are importable
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(page_title="Smart Bank Extractor", layout="wide")

from utils.styles import inject_css
from views.login import login_view
from views.dashboard import dashboard_view
from views.project import project_view

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

inject_css()

# ─── Session State Defaults ──────────────────────────────────────────────────
for _key, _default in [
    ("user", None),
    ("current_project", None),
    ("pdf_bytes", None),
    ("pdf_page", 0),
    ("extracted_data", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ─── Router ──────────────────────────────────────────────────────────────────
if not st.session_state.user:
    login_view(BACKEND_URL)
elif not st.session_state.current_project:
    dashboard_view(BACKEND_URL)
else:
    project_view(BACKEND_URL)
