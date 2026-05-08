import streamlit as st


def display_pdf(pdf_bytes: bytes, page_number: int):
    """Render a single PDF page as a high-resolution PNG via PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_number >= len(doc):
            st.error("Page out of bounds")
            doc.close()
            return
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        img_bytes = pix.tobytes("png")
        doc.close()
        st.image(img_bytes, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering PDF page {page_number + 1}: {e}")
