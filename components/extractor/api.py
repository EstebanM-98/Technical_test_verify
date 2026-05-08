from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from components.extractor.core.document_parser import DocumentParser

app = FastAPI(title="Extractor Service")
parser = DocumentParser()

class ExtractionRequest(BaseModel):
    ocr_text: str

@app.post("/extract")
async def extract_data(request: ExtractionRequest):
    try:
        extracted_data = parser.parse(request.ocr_text)
        if "error" in extracted_data:
            raise HTTPException(status_code=400, detail=extracted_data["error"])
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
