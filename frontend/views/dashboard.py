import streamlit as st
import httpx

from utils.styles import display_logo
from logger import get_logger

logger = get_logger(__name__, "frontend.log")


def dashboard_view(backend_url: str):
    display_logo(sidebar=True)
    username = st.session_state.user["username"]
    user_id = st.session_state.user["user_id"]

    st.sidebar.title(f"Welcome, {username}")
    if st.sidebar.button("Log Out"):
        logger.info("User '%s' logged out.", username)
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
                logger.info("User '%s' creating project name='%s'.", username, proj_name)
                try:
                    res = httpx.post(
                        f"{backend_url}/projects",
                        params={"user_id": user_id},
                        json={"name": proj_name},
                    )
                    if res.status_code == 200:
                        logger.info("Project '%s' created for user '%s'.", proj_name, username)
                        st.success("Project created! Switch to 'My Projects'.")
                    else:
                        logger.warning(
                            "Failed to create project '%s' for user '%s': HTTP %s — %s",
                            proj_name, username, res.status_code, res.text,
                        )
                        st.error(f"Error: {res.text}")
                except Exception:
                    logger.exception(
                        "Connection error while creating project for user '%s'.", username
                    )
                    st.error("Cannot connect to backend.")

    with tab_projects:
        logger.debug("Loading projects for user '%s' (id=%s).", username, user_id)
        try:
            res = httpx.get(
                f"{backend_url}/projects",
                params={"user_id": user_id},
            )
            projects = res.json() if res.status_code == 200 else []
            logger.info("Loaded %d project(s) for user '%s'.", len(projects), username)
        except Exception:
            logger.exception("Failed to load projects for user '%s'.", username)
            st.error("Cannot load projects.")
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
                    new_name = st.text_input(
                        "Name", value=p["name"], key=f"inp_{p_id}", label_visibility="collapsed"
                    )
                with col2:
                    if st.button("Save", key=f"save_{p_id}", type="primary"):
                        logger.info(
                            "User '%s' renaming project_id=%s to '%s'.", username, p_id, new_name
                        )
                        try:
                            httpx.put(f"{backend_url}/projects/{p_id}", json={"name": new_name})
                            logger.info("Project_id=%s renamed to '%s'.", p_id, new_name)
                            st.session_state[f"editing_{p_id}"] = False
                            st.rerun()
                        except Exception:
                            logger.exception("Failed to rename project_id=%s.", p_id)
                            st.warning("Could not save changes.")
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
                        logger.info("User '%s' opening project_id=%s.", username, p_id)
                        _open_project(p_id, backend_url)
                with col3:
                    if st.button("Edit", key=f"edit_{p_id}"):
                        st.session_state[f"editing_{p_id}"] = True
                        st.rerun()
                with col4:
                    if st.button("Delete", key=f"del_{p_id}"):
                        logger.warning(
                            "User '%s' deleting project_id=%s (name='%s').",
                            username, p_id, p["name"],
                        )
                        try:
                            httpx.delete(f"{backend_url}/projects/{p_id}")
                            logger.info("Project_id=%s deleted.", p_id)
                            st.rerun()
                        except Exception:
                            logger.exception("Failed to delete project_id=%s.", p_id)
                            st.warning("Could not delete project.")


def _open_project(project_id: int, backend_url: str):
    """Loads project data and PDF bytes into session state and redirects to project view."""
    st.session_state.current_project = project_id
    st.session_state.pdf_page = 0

    logger.debug("Loading project data for project_id=%s.", project_id)
    try:
        p_res = httpx.get(f"{backend_url}/projects/{project_id}")
        st.session_state.extracted_data = (
            p_res.json().get("extracted_data") if p_res.status_code == 200 else None
        )
        logger.debug(
            "Project data loaded for project_id=%s: has_extracted_data=%s.",
            project_id, st.session_state.extracted_data is not None,
        )
    except Exception:
        logger.exception("Could not load project data for project_id=%s.", project_id)
        st.warning("Could not load project data.")
        st.session_state.extracted_data = None

    logger.debug("Loading PDF bytes for project_id=%s.", project_id)
    try:
        pdf_res = httpx.get(f"{backend_url}/projects/{project_id}/pdf", timeout=30.0)
        st.session_state.pdf_bytes = pdf_res.content if pdf_res.status_code == 200 else None
        logger.debug(
            "PDF loaded for project_id=%s: %d bytes.",
            project_id, len(st.session_state.pdf_bytes) if st.session_state.pdf_bytes else 0,
        )
    except Exception:
        logger.exception("Could not load PDF for project_id=%s.", project_id)
        st.warning("Could not load PDF.")
        st.session_state.pdf_bytes = None

    st.rerun()
