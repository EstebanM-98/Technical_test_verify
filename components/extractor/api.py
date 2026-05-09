import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from components.extractor.core.document_parser import DocumentParser
from logger import get_logger

logger = get_logger(__name__, "extractor.log")

app = FastAPI(title="Extractor Service")

logger.info("Initializing DocumentParser...")
parser = DocumentParser()
logger.info("DocumentParser ready.")


class ExtractionRequest(BaseModel):
    ocr_text: str


@app.post("/extract")
async def extract_data(request: ExtractionRequest):
    text_length = len(request.ocr_text)
    logger.info("Extraction request received: %d characters of OCR text.", text_length)

    try:
        extracted_data = parser.parse(request.ocr_text)

        if "error" in extracted_data:
            logger.warning("Extraction returned an error: %s", extracted_data["error"])
            raise HTTPException(status_code=400, detail=extracted_data["error"])

        format_name = extracted_data.get("format", "unknown")
        total_items = len(extracted_data.get("all_line_items", []))
        logger.info(
            "Extraction successful: format='%s', total_line_items=%d.",
            format_name, total_items,
        )
        return extracted_data

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during extraction.")
        raise HTTPException(status_code=500, detail="Internal extraction error.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
