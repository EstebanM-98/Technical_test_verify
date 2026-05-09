import streamlit as st

from logger import get_logger

logger = get_logger(__name__, "frontend.log")


def display_pdf(pdf_bytes: bytes, page_number: int):
    """Render a single PDF page as a high-resolution PNG via PyMuPDF."""
    logger.debug("Rendering PDF page %d (%d bytes).", page_number + 1, len(pdf_bytes))
    try:
        import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if page_number >= total_pages:
            logger.warning(
                "Requested page %d is out of bounds (document has %d page(s)).",
                page_number + 1, total_pages,
            )
            st.error("Page out of bounds")
            doc.close()
            return

        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        img_bytes = pix.tobytes("png")
        doc.close()

        logger.debug(
            "Page %d rendered: %d bytes PNG.", page_number + 1, len(img_bytes)
        )
        st.image(img_bytes, use_container_width=True)

    except Exception:
        logger.exception("Error rendering PDF page %d.", page_number + 1)
        st.error(f"Error rendering PDF page {page_number + 1}.")
