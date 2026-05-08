from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from components.validator.core.rule_engine import ValidatorEngine

app = FastAPI(title="Validator Service")
engine = ValidatorEngine()

class ValidationRequest(BaseModel):
    extracted_data: Dict[str, Any]

@app.post("/validate")
def validate_document(req: ValidationRequest):
    result = engine.validate(req.extracted_data)
    return result
