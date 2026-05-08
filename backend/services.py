import os
import logging
import httpx

logger = logging.getLogger(__name__)


async def run_pipeline(filename: str, content: bytes) -> dict:
    """
    Orchestrates: OCR → Extractor → Validator.
    Returns the enriched extracted-data dict.
    Raises RuntimeError on any service failure.
    """
    ocr_url = os.getenv("OCR_URL")
    extractor_url = os.getenv("EXTRACTOR_URL")
    validator_url = os.getenv("VALIDATOR_URL")

    if not all([ocr_url, extractor_url, validator_url]):
        raise RuntimeError(
            "Required environment variables not set: OCR_URL, EXTRACTOR_URL, VALIDATOR_URL"
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. OCR
        logger.info("Calling OCR service...")
        ocr_res = await client.post(
            ocr_url, files={"file": (filename, content, "application/pdf")}
        )
        if ocr_res.status_code != 200:
            raise RuntimeError(f"OCR Service failed: {ocr_res.text}")
        ocr_text = ocr_res.json().get("ocr_text")

        # 2. Extractor
        logger.info("Calling Extractor service...")
        ext_res = await client.post(extractor_url, json={"ocr_text": ocr_text})
        if ext_res.status_code != 200:
            raise RuntimeError(f"Extractor Service failed: {ext_res.text}")
        extracted = ext_res.json()

        # 3. Validator
        logger.info("Calling Validator service...")
        val_res = await client.post(validator_url, json={"extracted_data": extracted})
        if val_res.status_code == 200:
            extracted["validation"] = val_res.json()
        else:
            logger.warning(f"Validator returned {val_res.status_code}: {val_res.text}")
            extracted["validation"] = {
                "is_valid": False,
                "message": f"Validator failed: {val_res.text}",
                "errors": [],
                "details": [],
            }

    return extracted
