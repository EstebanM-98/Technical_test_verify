import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

from components.validator.core.rule_engine import ValidatorEngine
from logger import get_logger

logger = get_logger(__name__, "validator.log")

app = FastAPI(title="Validator Service")

logger.info("Initializing ValidatorEngine...")
engine = ValidatorEngine()
logger.info("ValidatorEngine ready.")


class ValidationRequest(BaseModel):
    extracted_data: Dict[str, Any]


@app.post("/validate")
def validate_document(req: ValidationRequest):
    fmt = req.extracted_data.get("format", "unknown")
    logger.info("Validation request received for format='%s'.", fmt)

    result = engine.validate(req.extracted_data)

    is_valid = result.get("is_valid", False)
    errors_count = len(result.get("errors", []))

    if is_valid:
        logger.info("Validation passed for format='%s'.", fmt)
    else:
        logger.warning(
            "Validation failed for format='%s': %d error(s). Errors: %s",
            fmt, errors_count, result.get("errors"),
        )

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
