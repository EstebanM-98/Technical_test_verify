import json
import streamlit as st
import httpx
import pandas as pd

from utils.styles import display_logo
from utils.pdf_renderer import display_pdf


def project_view(backend_url: str):
    display_logo(sidebar=True)
    if st.sidebar.button("Back to Dashboard"):
        st.session_state.current_project = None
        st.session_state.pdf_bytes = None
        st.session_state.extracted_data = None
        st.rerun()

    try:
        p_res = httpx.get(f"{backend_url}/projects/{st.session_state.current_project}")
        project = p_res.json()
    except Exception as e:
        st.error(f"Cannot load project: {e}")
        return

    st.title(f"Project: {project['name']}")

    if not st.session_state.extracted_data:
        _upload_view(project, backend_url)
    else:
        _result_view(project, backend_url)


# ─── Upload View ─────────────────────────────────────────────────────────────

def _upload_view(project: dict, backend_url: str):
    st.write("Upload your bank statement PDF to process it.")
    uploaded_file = st.file_uploader("Drag and drop PDF here", type="pdf")
    if uploaded_file:
        st.session_state.pdf_bytes = uploaded_file.getvalue()
        if st.button("Run (OCR + Extractor)", type="primary"):
            with st.spinner("Processing document…"):
                try:
                    res = httpx.post(
                        f"{backend_url}/projects/{project['id']}/process",
                        files={"file": (uploaded_file.name, st.session_state.pdf_bytes, "application/pdf")},
                        timeout=120.0,
                    )
                    if res.status_code == 200:
                        st.session_state.extracted_data = res.json()["data"]
                        st.session_state.pdf_page = 0
                        st.success("Processing successful!")
                        st.rerun()
                    else:
                        st.error(f"Processing error: {res.text}")
                except Exception as e:
                    st.error(f"Cannot reach backend: {e}")


# ─── Result View ─────────────────────────────────────────────────────────────

def _result_view(project: dict, backend_url: str):
    data = st.session_state.extracted_data

    st.header("Extracted Information")
    _show_validation(data)
    _show_header(data)

    st.download_button(
        "Download JSON",
        data=json.dumps(data, indent=4),
        file_name="extract.json",
        mime="application/json",
        type="primary",
    )

    st.markdown("---")
    st.subheader("Line Items (Synced by Page)")

    pages_data = data.get("pages", [])
    max_pages = len(pages_data)

    # Auto re-fetch PDF bytes if lost (e.g. after browser refresh within session)
    if not st.session_state.pdf_bytes:
        try:
            pdf_res = httpx.get(f"{backend_url}/projects/{project['id']}/pdf", timeout=30.0)
            if pdf_res.status_code == 200:
                st.session_state.pdf_bytes = pdf_res.content
            else:
                st.warning(f"Could not retrieve PDF from backend (HTTP {pdf_res.status_code})")
        except Exception as e:
            st.warning(f"Could not load PDF: {e}")

    col_pdf, col_data = st.columns([1, 1])

    if st.session_state.pdf_bytes:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("⬅ Previous", disabled=(st.session_state.pdf_page <= 0)):
                st.session_state.pdf_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f"<h4 style='text-align:center;margin:0'>Page {st.session_state.pdf_page + 1} of {max_pages}</h4>",
                unsafe_allow_html=True,
            )
        with p3:
            if st.button("Next ➡", disabled=(st.session_state.pdf_page >= max_pages - 1)):
                st.session_state.pdf_page += 1
                st.rerun()

        with col_pdf:
            display_pdf(st.session_state.pdf_bytes, st.session_state.pdf_page)
    else:
        col_pdf.warning("⚠️ PDF not available.")

    with col_data:
        current_idx = next(
            (i for i, p in enumerate(pages_data) if p["page_number"] == st.session_state.pdf_page + 1),
            None,
        )
        if current_idx is not None and pages_data[current_idx].get("line_items"):
            df = pd.DataFrame(pages_data[current_idx]["line_items"])

            if st.button("Add Row", key=f"add_row_{st.session_state.pdf_page}"):
                new_row = {col: "" for col in df.columns}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.extracted_data["pages"][current_idx]["line_items"] = df.to_dict("records")
                st.rerun()

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{st.session_state.pdf_page}",
            )
            st.session_state.extracted_data["pages"][current_idx]["line_items"] = (
                edited_df.fillna("").to_dict("records")
            )
        else:
            st.warning("No line items detected on this page.")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _show_validation(data: dict):
    if "validation" not in data:
        return
    val = data["validation"]
    v1, v2 = st.columns([3, 1])
    with v1:
        if val.get("is_valid"):
            st.success(f"**{val.get('message', 'Validated ✅')}**")
        else:
            st.error(f"**{val.get('message', 'Validation Failed')}**")
            with st.expander("Validation Errors"):
                for err in val.get("errors", []):
                    st.write(f"- {err}")
    with v2:
        log_lines = ["--- VALIDATION LOG ---"]
        for det in val.get("details", []):
            icon = "TRUE ✅" if det["status"] else "FALSE ❌"
            log_lines.append(f"[{icon}] {det['check']}: {det['message']}")
        st.download_button(
            "Download Validation Log",
            data="\n".join(log_lines),
            file_name="validation_log.txt",
            mime="text/plain",
        )


def _show_header(data: dict):
    h = data.get("header", {})
    st.subheader("Main Details")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendor", h.get("vendor_name", "N/A"))
    c2.metric("Invoice Number", h.get("invoice_number", "N/A"))
    c3.metric("Invoice Date", h.get("invoice_date", "N/A"))
    c4.metric("Due Date", h.get("due_date", "N/A"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Bill To", h.get("bill_to_name", "N/A"))
    c6.metric("Vendor Address", h.get("vendor_address", "N/A"))
    c7.metric("Currency", h.get("currency", "N/A"))
    c8.metric("Total Amount", h.get("total_amount", "N/A"))
