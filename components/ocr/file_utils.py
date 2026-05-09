import hashlib
import json
import os
from datetime import datetime, timezone

from logger import get_logger

logger = get_logger(__name__, "ocr.log")

# ─── Cache directory (persisted via Docker volume at /app/ocr_cache) ─────────
_CACHE_DIR = os.environ.get("OCR_CACHE_DIR", "/app/ocr_cache")


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


def compute_content_hash(content: bytes) -> str:
    """
    Computes the SHA-256 hash of raw PDF bytes.
    Used as the cache key — independent of filename.
    """
    return hashlib.sha256(content).hexdigest()


def check_cache_by_hash(file_hash: str) -> dict | None:
    """
    Looks up a previously processed document by its content hash.

    Returns:
        A dict with 'ocr_text' and metadata if found, otherwise None.
    """
    cache_file = os.path.join(_CACHE_DIR, f"{file_hash}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(
                "Cache HIT for hash '%s...' (original file: '%s', processed: %s).",
                file_hash[:12], data.get("original_filename"), data.get("processed_at"),
            )
            return data
        except Exception:
            logger.exception("Failed to read cache file '%s'. Treating as cache miss.", cache_file)
    logger.debug("Cache MISS for hash '%s...'.", file_hash[:12])
    return None


def save_cache_by_hash(ocr_text: str, file_hash: str, original_filename: str) -> str:
    """
    Persists the OCR result to the cache directory, keyed by content hash.

    Returns:
        The absolute path to the saved cache file.
    """
    os.makedirs(_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(_CACHE_DIR, f"{file_hash}.json")
    payload = {
        "file_hash": file_hash,
        "original_filename": original_filename,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "character_count": len(ocr_text),
        "ocr_text": ocr_text,
    }
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(
        "Cache saved: hash='%s...', file='%s', chars=%d.",
        file_hash[:12], original_filename, len(ocr_text),
    )
    return cache_file


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
