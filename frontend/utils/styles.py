import streamlit as st


def inject_css():
    st.markdown("""
<style>
    .stApp { background-color: transparent !important; }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 20px !important;
        transition: transform 0.2s !important;
    }
    .stButton>button p, .stDownloadButton>button p, .stDownloadButton>button span {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: scale(1.05) !important;
    }
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)


def display_logo(sidebar: bool = False):
    import os
    logo_path = "frontend/static/logo.png"
    if os.path.exists(logo_path):
        if sidebar:
            st.sidebar.image(logo_path, use_container_width=True)
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_container_width=True)
