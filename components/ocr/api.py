import os
import tempfile

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from components.ocr.config import load_configuration
from components.ocr.ocr import VeryfiOCR
from logger import get_logger

logger = get_logger(__name__, "ocr.log")

app = FastAPI(title="OCR Service")

# ─── Service Initialization ───────────────────────────────────────────────────

logger.info("Initializing OCR service...")
try:
    config = load_configuration()
    ocr_service = VeryfiOCR(config)
    logger.info("OCR service initialized successfully.")
except Exception:
    ocr_service = None
    logger.exception("Failed to initialize OCR service. Endpoint will return HTTP 500.")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/process")
async def process_pdf(file: UploadFile = File(...)):
    logger.info("Received OCR request: filename='%s', content_type='%s'", file.filename, file.content_type)

    if not ocr_service:
        logger.error("OCR service is not initialized. Cannot process request.")
        raise HTTPException(status_code=500, detail="OCR service not initialized.")

    content = await file.read()
    logger.debug("File read into memory: %d bytes", len(content))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(content)
        temp_pdf_path = temp_pdf.name

    logger.debug("PDF written to temp file: %s", temp_pdf_path)

    try:
        ocr_text = ocr_service.extract_ocr_text(temp_pdf_path)
        if not ocr_text:
            logger.warning("No text extracted from file='%s'.", file.filename)
            raise HTTPException(status_code=400, detail="No text extracted.")

        logger.info(
            "OCR extraction successful for '%s': %d characters extracted.",
            file.filename, len(ocr_text),
        )
        return JSONResponse(content={"ocr_text": ocr_text})

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during OCR processing for file='%s'.", file.filename)
        raise HTTPException(status_code=500, detail="Internal OCR processing error.")
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            logger.debug("Temp file cleaned up: %s", temp_pdf_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
