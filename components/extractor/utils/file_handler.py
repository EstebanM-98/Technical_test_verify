import json

from logger import get_logger

logger = get_logger(__name__, "extractor.log")


def read_text(file_path: str) -> str:
    """Reads and returns the full content of a UTF-8 text file."""
    logger.debug("Reading text file: '%s'", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.debug("File read: '%s' (%d characters).", file_path, len(content))
    return content


def write_json(data: dict, file_path: str) -> None:
    """Serializes a dictionary to a pretty-printed JSON file."""
    logger.debug("Writing JSON output to: '%s'", file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info("JSON output written: '%s'.", file_path)
