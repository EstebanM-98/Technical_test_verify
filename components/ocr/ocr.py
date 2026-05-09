from veryfi import Client

from logger import get_logger

logger = get_logger(__name__, "ocr.log")


class VeryfiOCR:
    def __init__(self, config: dict):
        """
        Initializes the Veryfi client using the provided configuration dictionary.
        """
        logger.info("Initializing Veryfi client for username='%s'.", config.get("username"))
        self.client = Client(
            config["client_id"],
            config["client_secret"],
            config["username"],
            config["api_key"],
        )
        logger.debug("Veryfi client initialized successfully.")

    def process_document(self, file_path: str) -> dict:
        """
        Sends a document to the Veryfi API and returns the full JSON response.
        """
        logger.info("Sending document to Veryfi API: '%s'", file_path)
        try:
            response = self.client.process_document(file_path)
            logger.debug("Veryfi API response received. Keys: %s", list(response.keys()))
            return response
        except Exception as e:
            logger.error("Error communicating with Veryfi API for '%s': %s", file_path, e)
            raise RuntimeError(f"Error communicating with Veryfi API: {e}") from e

    def extract_ocr_text(self, file_path: str) -> str:
        """
        Processes a document and extracts only the 'ocr_text' field.
        """
        logger.debug("Extracting 'ocr_text' field from document: '%s'", file_path)
        response = self.process_document(file_path)
        ocr_text = response.get("ocr_text", "")
        logger.info(
            "ocr_text extracted from '%s': %d characters.", file_path, len(ocr_text)
        )
        return ocr_text
