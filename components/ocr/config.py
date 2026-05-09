import os
from dotenv import load_dotenv

from logger import get_logger

logger = get_logger(__name__, "ocr.log")

# Keys required for the Veryfi API
_REQUIRED_KEYS = ("client_id", "client_secret", "username", "api_key")
_ENV_VAR_MAP = {
    "client_id": "VERYFI_CLIENT_ID",
    "client_secret": "VERYFI_CLIENT_SECRET",
    "username": "VERYFI_USERNAME",
    "api_key": "VERYFI_API_KEY",
}


def load_configuration() -> dict:
    """
    Loads environment variables from the project root .env file and returns
    the Veryfi API configuration dictionary.

    Raises:
        ValueError: If any required credential is missing.
    """
    # Resolve project root (two levels up from components/ocr/)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(root_dir, ".env")

    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        logger.debug("Loaded .env from: '%s'", env_path)
    else:
        logger.warning(
            ".env file not found at '%s'. Falling back to system environment variables.",
            env_path,
        )
        load_dotenv()  # Fallback: read from shell environment

    config = {key: os.getenv(env_var) for key, env_var in _ENV_VAR_MAP.items()}

    missing_keys = [key for key, val in config.items() if not val]
    if missing_keys:
        logger.error(
            "Missing required Veryfi credentials: %s. "
            "Ensure they are defined in the .env file.",
            ", ".join(missing_keys),
        )
        raise ValueError(
            f"Missing Veryfi credentials in the .env file: {', '.join(missing_keys)}"
        )

    # Log presence (never log values of secrets)
    logger.info(
        "Veryfi configuration loaded successfully. Keys present: %s",
        ", ".join(config.keys()),
    )
    return config
