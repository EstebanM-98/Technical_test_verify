import os

from logger import get_logger

logger = get_logger(__name__, "ocr.log")


def get_output_dir() -> str:
    """
    Returns the absolute path to the 'components/ocr/output' directory,
    creating it if it does not already exist.
    """
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.debug("Created OCR output directory: '%s'", output_dir)
    return output_dir


def check_if_processed(document_path: str) -> str | bool:
    """
    Checks if a document has already been processed by looking for its output
    .txt file in the components/ocr/output/ directory.

    Returns:
        The path to the existing output file if found, otherwise False.
    """
    base_name = os.path.splitext(os.path.basename(document_path))[0]
    output_dir = get_output_dir()
    doc_output_dir = os.path.join(output_dir, base_name)
    expected_file = os.path.join(doc_output_dir, f"{base_name}.txt")

    if os.path.exists(expected_file):
        logger.info("Cache hit for '%s': output already exists at '%s'.", base_name, expected_file)
        return expected_file

    logger.debug("No cached output found for '%s'.", base_name)
    return False


def save_ocr_result(content: str, document_path: str) -> str:
    """
    Saves the OCR text result into:
        components/ocr/output/<doc_name>/<doc_name>.txt

    Returns:
        The absolute path to the saved file.
    """
    base_name = os.path.splitext(os.path.basename(document_path))[0]
    output_dir = get_output_dir()
    doc_output_dir = os.path.join(output_dir, base_name)

    if not os.path.exists(doc_output_dir):
        os.makedirs(doc_output_dir)
        logger.debug("Created document output directory: '%s'", doc_output_dir)

    output_file = os.path.join(doc_output_dir, f"{base_name}.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(
        "OCR result saved: '%s' (%d characters written).", output_file, len(content)
    )
    return output_file
