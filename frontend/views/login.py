import streamlit as st
import httpx

from utils.styles import display_logo


def login_view(backend_url: str):
    display_logo()
    st.title("Smart Bank Extractor")
    st.write("Welcome to the system. Please login or register.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", type="primary"):
            try:
                res = httpx.post(f"{backend_url}/auth/login", json={"username": username, "password": password})
                if res.status_code == 200:
                    st.session_state.user = res.json()
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Cannot connect to backend: {e}")

    with tab_register:
        reg_username = st.text_input("New Username", key="reg_user")
        reg_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Sign Up", type="primary"):
            try:
                res = httpx.post(f"{backend_url}/auth/register", json={"username": reg_username, "password": reg_password})
                if res.status_code == 200:
                    st.success("Registered! Go to the Login tab.")
                else:
                    st.error(res.json().get("detail", "Registration error"))
            except Exception as e:
                st.error(f"Cannot connect to backend: {e}")
