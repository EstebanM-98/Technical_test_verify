import streamlit as st
st.set_page_config(page_title="Smart Bank Extractor", layout="wide")
import httpx
import json
import os
import pandas as pd
import base64

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# --- Custom CSS for Modern Glassmorphism Design ---
st.markdown("""
<style>
    .stApp {
        background-color: transparent !important;
    }
    /* Enhance All Buttons */
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
    /* Glassmorphism containers */
    .css-1d391kg {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        padding: 2rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    /* Table & Editor styling override */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if "user" not in st.session_state:
    st.session_state.user = None
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "pdf_page" not in st.session_state:
    st.session_state.pdf_page = 0
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# --- Helpers ---
def display_logo(sidebar=False):
    logo_path = "frontend/static/logo.png"
    if os.path.exists(logo_path):
        if sidebar:
            st.sidebar.image(logo_path, use_container_width=True)
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_container_width=True)

def display_pdf(pdf_bytes, page_number):
    """
    Render a single PDF page as a high-resolution PNG image.
    No iframes, no browser security blocks, no Chrome restrictions.
    """
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_number >= len(doc):
            st.error("Page out of bounds")
            doc.close()
            return

        page = doc.load_page(page_number)
        # 2.5x gives ~180 DPI — sharp and readable without being oversized
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        img_bytes = pix.tobytes("png")
        doc.close()

        st.image(img_bytes, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering PDF: {e}")

# --- Views ---
def login_view():
    display_logo()
    st.title("Smart Bank Extractor")
    st.write("Welcome to the system. Please login or register.")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", type="primary"):
            try:
                res = httpx.post(f"{BACKEND_URL}/auth/login", json={"username": username, "password": password})
                if res.status_code == 200:
                    st.session_state.user = res.json()
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
    with tab2:
        reg_username = st.text_input("New Username", key="reg_user")
        reg_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Sign Up", type="primary"):
            try:
                res = httpx.post(f"{BACKEND_URL}/auth/register", json={"username": reg_username, "password": reg_password})
                if res.status_code == 200:
                    st.success("User registered successfully. Go to Login tab.")
                else:
                    st.error(res.json().get("detail", "Registration Error"))
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")

def dashboard_view():
    display_logo(sidebar=True)
    st.sidebar.title(f"Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.current_project = None
        st.rerun()
        
    st.title("Projects Dashboard")
    
    st.info("""
    **How to use this application:**
    1. **Create a Project** by typing a name and clicking "Create".
    2. **Open the Project** from your list below.
    3. **Upload your PDF bank statement** or invoice.
    4. Click **Run (OCR + Extractor)** and wait for the AI to process it.
    5. **Review** the extracted data, navigate pages, and **Download JSON**.
    """)
    
    tab_projects, tab_create = st.tabs(["My Projects", "Create New Project"])
    
    with tab_create:
        st.subheader("Create a New Project")
        with st.form("create_project_form", clear_on_submit=True):
            proj_name = st.text_input("Project Name")
            submitted = st.form_submit_button("Create Project", type="primary")
            if submitted and proj_name:
                res = httpx.post(f"{BACKEND_URL}/projects", params={"user_id": st.session_state.user['user_id']}, json={"name": proj_name})
                if res.status_code == 200:
                    st.success("Project created! Go to the 'My Projects' tab.")
                    
    with tab_projects:
        res = httpx.get(f"{BACKEND_URL}/projects", params={"user_id": st.session_state.user['user_id']})
        if res.status_code == 200:
            projects = res.json()
            if not projects:
                st.info("No projects found. Create one in the next tab!")
            for p in projects:
                p_id = p['id']
                is_editing = st.session_state.get(f"editing_{p_id}", False)
                
                if is_editing:
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        new_name = st.text_input("Edit Name", value=p["name"], key=f"inp_{p_id}", label_visibility="collapsed")
                    with col2:
                        if st.button("Save", key=f"save_{p_id}", type="primary"):
                            try:
                                httpx.put(f"{BACKEND_URL}/projects/{p_id}", json={"name": new_name})
                                st.session_state[f"editing_{p_id}"] = False
                                st.rerun()
                            except:
                                pass
                    with col3:
                        if st.button("Cancel", key=f"cancel_{p_id}"):
                            st.session_state[f"editing_{p_id}"] = False
                            st.rerun()
                else:
                    col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
                    with col1:
                        st.subheader(p["name"])
                    with col2:
                        if st.button("Open", key=f"btn_{p_id}"):
                            st.session_state.current_project = p_id
                            try:
                                p_res = httpx.get(f"{BACKEND_URL}/projects/{p_id}")
                                if p_res.status_code == 200:
                                    st.session_state.extracted_data = p_res.json().get("extracted_data")
                            except:
                                st.session_state.extracted_data = None
                            
                            try:
                                pdf_res = httpx.get(f"{BACKEND_URL}/projects/{p_id}/pdf")
                                if pdf_res.status_code == 200:
                                    st.session_state.pdf_bytes = pdf_res.content
                                else:
                                    st.session_state.pdf_bytes = None
                            except Exception:
                                st.session_state.pdf_bytes = None
                                
                            st.session_state.pdf_page = 0
                            st.rerun()
                    with col3:
                        if st.button("Edit", key=f"edit_{p_id}"):
                            st.session_state[f"editing_{p_id}"] = True
                            st.rerun()
                    with col4:
                        if st.button("Delete", key=f"del_{p_id}"):
                            try:
                                httpx.delete(f"{BACKEND_URL}/projects/{p_id}")
                                st.rerun()
                            except:
                                pass

def project_view():
    display_logo(sidebar=True)
    if st.sidebar.button("Back to Dashboard"):
        st.session_state.current_project = None
        st.session_state.pdf_bytes = None
        st.session_state.extracted_data = None
        st.rerun()
        
    p_res = httpx.get(f"{BACKEND_URL}/projects/{st.session_state.current_project}")
    project = p_res.json()
    
    st.title(f"Project: {project['name']}")
    
    if not st.session_state.extracted_data:
        st.write("Upload your bank statement PDF to process it.")
        uploaded_file = st.file_uploader("Drag and drop PDF here", type="pdf")
        if uploaded_file is not None:
            st.session_state.pdf_bytes = uploaded_file.getvalue()
            
            if st.button("Run (OCR + Extractor)", type="primary"):
                with st.spinner("Processing document... (This may take several seconds)"):
                    files = {"file": (uploaded_file.name, st.session_state.pdf_bytes, "application/pdf")}
                    res = httpx.post(f"{BACKEND_URL}/projects/{project['id']}/process", files=files, timeout=120.0)
                    if res.status_code == 200:
                        st.session_state.extracted_data = res.json()["data"]
                        st.session_state.pdf_page = 0
                        st.success("Processing successful!")
                        st.rerun()
                    else:
                        st.error(f"Error processing: {res.text}")
    else:
        # RESULT VIEW
        data = st.session_state.extracted_data
        st.header("Extracted Information")
        
        # Display Validation Status
        if "validation" in data:
            val_data = data["validation"]
            
            v_col1, v_col2 = st.columns([3, 1])
            with v_col1:
                if val_data.get("is_valid"):
                    st.success(f"**{val_data.get('message', 'Validated ✅')}**")
                else:
                    st.error(f"**{val_data.get('message', 'Validation Failed')}**")
                    with st.expander("View Validation Errors"):
                        for err in val_data.get("errors", []):
                            st.write(f"- {err}")
            with v_col2:
                # Generate a nicely formatted log string
                log_lines = ["--- VALIDATION LOG ---"]
                for det in val_data.get("details", []):
                    status_icon = "TRUE ✅" if det["status"] else "FALSE ❌"
                    log_lines.append(f"[{status_icon}] {det['check']}: {det['message']}")
                log_text = "\n".join(log_lines)
                st.download_button("Download Validation Log", data=log_text, file_name="validation_log.txt", mime="text/plain", type="secondary")
        
        # Display Header Information
        st.subheader("Main Details")
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)
        h_col1.metric("Vendor", data["header"].get("vendor_name", "N/A"))
        h_col2.metric("Invoice Number", data["header"].get("invoice_number", "N/A"))
        h_col3.metric("Invoice Date", data["header"].get("invoice_date", "N/A"))
        h_col4.metric("Due Date", data["header"].get("due_date", "N/A"))
        
        h2_col1, h2_col2, h2_col3, h2_col4 = st.columns(4)
        h2_col1.metric("Bill To Name", data["header"].get("bill_to_name", "N/A"))
        h2_col2.metric("Vendor Address", data["header"].get("vendor_address", "N/A"))
        h2_col3.metric("Currency", data["header"].get("currency", "N/A"))
        h2_col4.metric("Total Amount", data["header"].get("total_amount", "N/A"))
        
        st.download_button("Download JSON", data=json.dumps(data, indent=4), file_name="extract.json", mime="application/json", type="primary")
        
        st.markdown("---")
        
        # Split View for Movements and PDF Preview
        st.subheader("Line Items (Synced by Page)")
        
        col_pdf, col_data = st.columns([1, 1])
        
        # Determine current page line items
        pages_data = data.get("pages", [])
        max_pages = len(pages_data)
        
        # --- Re-fetch PDF if bytes were lost (e.g. after a page rerun) ---
        if not st.session_state.pdf_bytes:
            try:
                pdf_res = httpx.get(f"{BACKEND_URL}/projects/{project['id']}/pdf", timeout=30.0)
                if pdf_res.status_code == 200:
                    st.session_state.pdf_bytes = pdf_res.content
            except Exception:
                pass

        if st.session_state.pdf_bytes:
            # Paginator controls
            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if st.button("⬅ Previous Page", disabled=(st.session_state.pdf_page <= 0)):
                    st.session_state.pdf_page -= 1
                    st.rerun()
            with p_col2:
                st.markdown(f"<h4 style='text-align:center; margin:0;'>Page {st.session_state.pdf_page + 1} of {max_pages}</h4>", unsafe_allow_html=True)
            with p_col3:
                if st.button("Next Page ➡", disabled=(st.session_state.pdf_page >= max_pages - 1)):
                    st.session_state.pdf_page += 1
                    st.rerun()

            with col_pdf:
                display_pdf(st.session_state.pdf_bytes, st.session_state.pdf_page)
        else:
            col_pdf.warning("⚠️ PDF preview not available. The file may not have been uploaded yet.")
            
        with col_data:
            current_page_idx = None
            for idx, p in enumerate(pages_data):
                if p["page_number"] == st.session_state.pdf_page + 1:
                    current_page_idx = idx
                    break
                    
            if current_page_idx is not None and pages_data[current_page_idx].get("line_items"):
                df = pd.DataFrame(pages_data[current_page_idx]["line_items"])
                
                # Manual Add Row Button
                if st.button("Add Row", key=f"add_row_{st.session_state.pdf_page}", type="secondary"):
                    new_row = {col: "" for col in df.columns}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.extracted_data["pages"][current_page_idx]["line_items"] = df.to_dict("records")
                    st.rerun()
                    
                # Interactive Data Editor
                edited_df = st.data_editor(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    num_rows="fixed", # Disables automatic row adding on scroll
                    key=f"editor_{st.session_state.pdf_page}" # vital so each page has its own editor state
                )
                
                # Sync back to session state so "Download JSON" gets the user's edits
                st.session_state.extracted_data["pages"][current_page_idx]["line_items"] = edited_df.fillna("").to_dict("records")
            else:
                st.warning("No line items detected on this page.")

# --- Router ---
if not st.session_state.user:
    login_view()
elif not st.session_state.current_project:
    dashboard_view()
else:
    project_view()
