import streamlit as st
import httpx

from utils.styles import display_logo


def dashboard_view(backend_url: str):
    display_logo(sidebar=True)
    st.sidebar.title(f"Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.current_project = None
        st.rerun()

    st.title("Projects Dashboard")
    st.info("""
    **How to use:**
    1. Create a project in the **Create New Project** tab.
    2. Open it, upload your PDF, and click **Run (OCR + Extractor)**.
    3. Review extracted data and download JSON.
    """)

    tab_projects, tab_create = st.tabs(["My Projects", "Create New Project"])

    with tab_create:
        st.subheader("Create a New Project")
        with st.form("create_project_form", clear_on_submit=True):
            proj_name = st.text_input("Project Name")
            if st.form_submit_button("Create Project", type="primary") and proj_name:
                try:
                    res = httpx.post(
                        f"{backend_url}/projects",
                        params={"user_id": st.session_state.user["user_id"]},
                        json={"name": proj_name},
                    )
                    if res.status_code == 200:
                        st.success("Project created! Switch to 'My Projects'.")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Cannot connect to backend: {e}")

    with tab_projects:
        try:
            res = httpx.get(
                f"{backend_url}/projects",
                params={"user_id": st.session_state.user["user_id"]},
            )
            projects = res.json() if res.status_code == 200 else []
        except Exception as e:
            st.error(f"Cannot load projects: {e}")
            return

        if not projects:
            st.info("No projects yet. Create one in the next tab!")
            return

        for p in projects:
            p_id = p["id"]
            is_editing = st.session_state.get(f"editing_{p_id}", False)

            if is_editing:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    new_name = st.text_input("Name", value=p["name"], key=f"inp_{p_id}", label_visibility="collapsed")
                with col2:
                    if st.button("Save", key=f"save_{p_id}", type="primary"):
                        try:
                            httpx.put(f"{backend_url}/projects/{p_id}", json={"name": new_name})
                            st.session_state[f"editing_{p_id}"] = False
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Could not save: {e}")
                with col3:
                    if st.button("Cancel", key=f"cancel_{p_id}"):
                        st.session_state[f"editing_{p_id}"] = False
                        st.rerun()
            else:
                col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
                with col1:
                    st.subheader(p["name"])
                with col2:
                    if st.button("Open", key=f"open_{p_id}"):
                        _open_project(p_id, backend_url)
                with col3:
                    if st.button("Edit", key=f"edit_{p_id}"):
                        st.session_state[f"editing_{p_id}"] = True
                        st.rerun()
                with col4:
                    if st.button("Delete", key=f"del_{p_id}"):
                        try:
                            httpx.delete(f"{backend_url}/projects/{p_id}")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Could not delete: {e}")


def _open_project(project_id: int, backend_url: str):
    st.session_state.current_project = project_id
    st.session_state.pdf_page = 0

    try:
        p_res = httpx.get(f"{backend_url}/projects/{project_id}")
        st.session_state.extracted_data = p_res.json().get("extracted_data") if p_res.status_code == 200 else None
    except Exception as e:
        st.warning(f"Could not load project data: {e}")
        st.session_state.extracted_data = None

    try:
        pdf_res = httpx.get(f"{backend_url}/projects/{project_id}/pdf", timeout=30.0)
        st.session_state.pdf_bytes = pdf_res.content if pdf_res.status_code == 200 else None
    except Exception as e:
        st.warning(f"Could not load PDF: {e}")
        st.session_state.pdf_bytes = None

    st.rerun()
