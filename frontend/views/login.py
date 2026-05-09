import streamlit as st
import httpx

from utils.styles import display_logo
from logger import get_logger

logger = get_logger(__name__, "frontend.log")


def login_view(backend_url: str):
    display_logo()
    st.title("Smart Invoice Extractor")
    st.write("Welcome to the system. Please login or register.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", type="primary"):
            logger.info("Login attempt for username='%s'.", username)
            try:
                res = httpx.post(
                    f"{backend_url}/auth/login",
                    json={"username": username, "password": password},
                )
                if res.status_code == 200:
                    st.session_state.user = res.json()
                    logger.info("Login successful for username='%s'.", username)
                    st.rerun()
                else:
                    logger.warning(
                        "Login failed for username='%s': HTTP %s.",
                        username, res.status_code,
                    )
                    st.error("Invalid credentials")
            except Exception:
                logger.exception("Cannot connect to backend at '%s'.", backend_url)
                st.error(f"Cannot connect to backend: {backend_url}")

    with tab_register:
        reg_username = st.text_input("New Username", key="reg_user")
        reg_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Sign Up", type="primary"):
            logger.info("Registration attempt for username='%s'.", reg_username)
            try:
                res = httpx.post(
                    f"{backend_url}/auth/register",
                    json={"username": reg_username, "password": reg_password},
                )
                if res.status_code == 200:
                    logger.info("Registration successful for username='%s'.", reg_username)
                    st.success("Registered! Go to the Login tab.")
                else:
                    detail = res.json().get("detail", "Registration error")
                    logger.warning(
                        "Registration failed for username='%s': %s.", reg_username, detail
                    )
                    st.error(detail)
            except Exception:
                logger.exception(
                    "Cannot connect to backend at '%s' during registration.", backend_url
                )
                st.error(f"Cannot connect to backend: {backend_url}")
