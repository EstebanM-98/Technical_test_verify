import os
import time
import httpx

from logger import get_logger

logger = get_logger(__name__, "backend.log")


async def run_pipeline(filename: str, content: bytes) -> dict:
    """
    Orchestrates: OCR → Extractor → Validator.
    Returns the enriched extracted-data dict.
    Raises RuntimeError on any service failure.
    """
    ocr_url = os.getenv("OCR_URL")
    extractor_url = os.getenv("EXTRACTOR_URL")
    validator_url = os.getenv("VALIDATOR_URL")

    logger.debug(
        "Pipeline env URLs — OCR: %s | Extractor: %s | Validator: %s",
        ocr_url, extractor_url, validator_url,
    )

    if not all([ocr_url, extractor_url, validator_url]):
        logger.critical(
            "Missing required environment variables. "
            "OCR_URL=%s, EXTRACTOR_URL=%s, VALIDATOR_URL=%s",
            ocr_url, extractor_url, validator_url,
        )
        raise RuntimeError(
            "Required environment variables not set: OCR_URL, EXTRACTOR_URL, VALIDATOR_URL"
        )

    async with httpx.AsyncClient(timeout=120.0) as client:

        # 1. OCR ─────────────────────────────────────────────────────────────
        logger.info("Step 1/3 — Calling OCR service for file='%s' (%d bytes)", filename, len(content))
        t0 = time.perf_counter()
        ocr_res = await client.post(
            ocr_url, files={"file": (filename, content, "application/pdf")}
        )
        ocr_elapsed = time.perf_counter() - t0

        if ocr_res.status_code != 200:
            logger.error(
                "OCR service failed in %.2fs — HTTP %s: %s",
                ocr_elapsed, ocr_res.status_code, ocr_res.text,
            )
            raise RuntimeError(f"OCR Service failed: {ocr_res.text}")

        ocr_text = ocr_res.json().get("ocr_text", "")
        logger.info(
            "OCR completed in %.2fs — extracted %d characters.", ocr_elapsed, len(ocr_text)
        )

        # 2. Extractor ───────────────────────────────────────────────────────
        logger.info("Step 2/3 — Calling Extractor service.")
        t0 = time.perf_counter()
        ext_res = await client.post(extractor_url, json={"ocr_text": ocr_text})
        ext_elapsed = time.perf_counter() - t0

        if ext_res.status_code != 200:
            logger.error(
                "Extractor service failed in %.2fs — HTTP %s: %s",
                ext_elapsed, ext_res.status_code, ext_res.text,
            )
            raise RuntimeError(f"Extractor Service failed: {ext_res.text}")

        extracted = ext_res.json()
        logger.info(
            "Extractor completed in %.2fs — format='%s'.",
            ext_elapsed, extracted.get("format", "unknown"),
        )

        # 3. Validator ───────────────────────────────────────────────────────
        logger.info("Step 3/3 — Calling Validator service.")
        t0 = time.perf_counter()
        val_res = await client.post(validator_url, json={"extracted_data": extracted})
        val_elapsed = time.perf_counter() - t0

        if val_res.status_code == 200:
            val_result = val_res.json()
            extracted["validation"] = val_result
            logger.info(
                "Validator completed in %.2fs — is_valid=%s.",
                val_elapsed, val_result.get("is_valid"),
            )
        else:
            logger.warning(
                "Validator returned HTTP %s in %.2fs: %s",
                val_res.status_code, val_elapsed, val_res.text,
            )
            extracted["validation"] = {
                "is_valid": False,
                "message": f"Validator failed: {val_res.text}",
                "errors": [],
                "details": [],
            }

    logger.info("Pipeline finished successfully for file='%s'.", filename)
    return extracted
