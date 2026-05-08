from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
import uvicorn

from components.ocr.config import load_configuration
from components.ocr.ocr import VeryfiOCR
from components.ocr.file_utils import save_ocr_result

app = FastAPI(title="OCR Service")

try:
    config = load_configuration()
    ocr_service = VeryfiOCR(config)
except Exception as e:
    ocr_service = None
    print(f"Failed to initialize OCR service: {e}")

@app.post("/process")
async def process_pdf(file: UploadFile = File(...)):
    if not ocr_service:
        raise HTTPException(status_code=500, detail="OCR service not initialized.")
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        content = await file.read()
        temp_pdf.write(content)
        temp_pdf_path = temp_pdf.name
        
    try:
        ocr_text = ocr_service.extract_ocr_text(temp_pdf_path)
        if not ocr_text:
            raise HTTPException(status_code=400, detail="No text extracted.")
            
        return JSONResponse(content={"ocr_text": ocr_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
