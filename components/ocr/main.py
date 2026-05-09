import argparse
import os

from components.ocr.config import load_configuration
from components.ocr.file_utils import check_if_processed, save_ocr_result
from components.ocr.ocr import VeryfiOCR
from logger import get_logger

logger = get_logger(__name__, "ocr.log")


def process_single_file(file_path: str, ocr_service: VeryfiOCR) -> str | None:
    """
    Processes a single PDF file through the OCR pipeline.
    Returns the output file path on success, or None on failure.
    Skips processing if the file was already processed (cache hit).
    """
    if not os.path.exists(file_path):
        logger.error("Document not found: '%s'", file_path)
        return None

    logger.info("Processing document: '%s'", file_path)

    # Cache check — avoid redundant API calls
    existing_output = check_if_processed(file_path)
    if existing_output:
        logger.info("Cache hit — document already processed. Output at: '%s'", existing_output)
        return existing_output

    try:
        logger.debug("Sending document to Veryfi API: '%s'", file_path)
        ocr_text = ocr_service.extract_ocr_text(file_path)

        if ocr_text:
            output_path = save_ocr_result(ocr_text, file_path)
            logger.info(
                "OCR completed — %d characters extracted and saved to: '%s'",
                len(ocr_text), output_path,
            )
            return output_path
        else:
            logger.warning("No OCR text found in the Veryfi response for: '%s'", file_path)
            return None

    except Exception:
        logger.exception("Unexpected error while processing document: '%s'", file_path)
        return None


def main():
    parser = argparse.ArgumentParser(description="Process a document using Veryfi OCR")
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the document to process (e.g., documents/file.pdf)",
    )
    args = parser.parse_args()

    # 1. Load Configuration
    logger.info("Loading Veryfi configuration...")
    try:
        config = load_configuration()
    except ValueError:
        logger.exception("Configuration error. Cannot start OCR service.")
        return

    # 2. Initialize OCR Service
    logger.info("Initializing VeryfiOCR client...")
    try:
        ocr_service = VeryfiOCR(config)
    except Exception:
        logger.exception("Failed to initialize OCR service.")
        return

    # 3. Handle Execution
    if args.file:
        process_single_file(args.file, ocr_service)
    else:
        logger.warning("No file provided. Usage: python -m components.ocr.main <path_to_document>")


if __name__ == "__main__":
    main()
