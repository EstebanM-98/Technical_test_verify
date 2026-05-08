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
# We removed hacky inputs CSS because we now use native Streamlit Dark Theme via config.toml
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
            # Center the logo on the main page
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_container_width=True)

def display_pdf(pdf_bytes, page_number):
    """Render a SINGLE PAGE of the PDF as a high-resolution image to avoid browser iframe blocks and state resets"""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_number >= len(doc):
            st.error("Page out of bounds")
            return
            
        page = doc.load_page(page_number)
        # Render high-resolution image (3x zoom)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        img_bytes = pix.tobytes("png")
        
        # Displaying as an image perfectly preserves the layout, works in all browsers, 
        # and doesn't lose zoom/pan state when Streamlit reruns!
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
        
    st.title("Your Projects")
    
    # Instructions
    st.info("""
    **How to use this application:**
    1. **Create a Project** by typing a name and clicking "Create".
    2. **Open the Project** from your list below.
    3. **Upload your PDF bank statement** or invoice.
    4. Click **Run (OCR + Extractor)** and wait for the AI to process it.
    5. **Review** the extracted data, navigate pages, and **Download JSON**.
    """)
    
    # Create Project
    with st.expander("Create New Project"):
        proj_name = st.text_input("Project Name")
        if st.button("Create", type="primary"):
            res = httpx.post(f"{BACKEND_URL}/projects", params={"user_id": st.session_state.user['user_id']}, json={"name": proj_name})
            if res.status_code == 200:
                st.success("Project created")
                st.rerun()
                
    # List Projects
    res = httpx.get(f"{BACKEND_URL}/projects", params={"user_id": st.session_state.user['user_id']})
    if res.status_code == 200:
        projects = res.json()
        for p in projects:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(p["name"])
            with col2:
                if st.button("Open", key=f"btn_{p['id']}"):
                    st.session_state.current_project = p['id']
                    # Load project details
                    p_res = httpx.get(f"{BACKEND_URL}/projects/{p['id']}")
                    if p_res.status_code == 200:
                        st.session_state.extracted_data = p_res.json().get("extracted_data")
                    
                    # Fetch PDF if available
                    try:
                        pdf_res = httpx.get(f"{BACKEND_URL}/projects/{p['id']}/pdf")
                        if pdf_res.status_code == 200:
                            st.session_state.pdf_bytes = pdf_res.content
                        else:
                            st.session_state.pdf_bytes = None
                    except Exception:
                        st.session_state.pdf_bytes = None
                        
                    st.session_state.pdf_page = 0
                    st.rerun()

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
        
        # Display Header Information
        st.subheader("Main Details")
        h_col1, h_col2, h_col3 = st.columns(3)
        h_col1.metric("Vendor", data["header"].get("vendor_name", "N/A"))
        h_col2.metric("Invoice Number", data["header"].get("invoice_number", "N/A"))
        h_col3.metric("Invoice Date", data["header"].get("invoice_date", "N/A"))
        
        h2_col1, h2_col2, h2_col3 = st.columns(3)
        h2_col1.metric("Due Date", data["header"].get("due_date", "N/A"))
        h2_col2.metric("Bill To Name", data["header"].get("bill_to_name", "N/A"))
        h2_col3.metric("Vendor Address", data["header"].get("vendor_address", "N/A"))
        
        # We explicitly set type="primary" to make sure it picks up the bright gradient
        st.download_button("Download JSON", data=json.dumps(data, indent=4), file_name="extract.json", mime="application/json", type="primary")
        
        st.markdown("---")
        
        # Split View for Movements and PDF Preview
        st.subheader("Line Items (Synced by Page)")
        
        col_pdf, col_data = st.columns([1, 1])
        
        # Determine current page line items
        pages_data = data.get("pages", [])
        max_pages = len(pages_data)
        
        if st.session_state.pdf_bytes:
            # Paginator controls
            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                # Disable button if we are on the first page
                if st.button("Previous Page", disabled=(st.session_state.pdf_page <= 0)):
                    st.session_state.pdf_page -= 1
                    st.rerun()
            with p_col2:
                st.write(f"**Page {st.session_state.pdf_page + 1} of {max_pages}**")
            with p_col3:
                # Disable button if we are on the last page
                if st.button("Next Page", disabled=(st.session_state.pdf_page >= max_pages - 1)):
                    st.session_state.pdf_page += 1
                    st.rerun()

            with col_pdf:
                display_pdf(st.session_state.pdf_bytes, st.session_state.pdf_page)
        else:
            col_pdf.info("PDF preview not available.")
            
        with col_data:
            current_page_idx = None
            for idx, p in enumerate(pages_data):
                if p["page_number"] == st.session_state.pdf_page + 1:
                    current_page_idx = idx
                    break
                    
            if current_page_idx is not None and pages_data[current_page_idx].get("line_items"):
                df = pd.DataFrame(pages_data[current_page_idx]["line_items"])
                
                # Interactive Data Editor
                edited_df = st.data_editor(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    num_rows="dynamic", # Allow adding/deleting rows!
                    key=f"editor_{st.session_state.pdf_page}" # vital so each page has its own editor state
                )
                
                # Sync back to session state so "Download JSON" gets the user's edits!
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
