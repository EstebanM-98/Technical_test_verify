"""
logger.py — Centralized logging configuration for all services.

Usage:
    from logger import get_logger
    logger = get_logger(__name__, "backend.log")

Log files are written to the `logs/` directory at the project root.
Each service writes to its own file to allow independent monitoring.

Levels:
    - Console (StreamHandler): INFO and above
    - File (RotatingFileHandler): DEBUG and above
      Max 5 MB per file, up to 5 rotated backups kept.

Format:
    2026-05-08 21:00:00,000 | INFO     | module_name | function | message
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ─── Constants ────────────────────────────────────────────────────────────────

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
_MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
_BACKUP_COUNT = 5               # Keep 5 rotated backups
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ─── Registry ─────────────────────────────────────────────────────────────────

# Cache already-configured loggers to avoid duplicate handlers on re-import
_configured_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str, log_file: str) -> logging.Logger:
    """
    Returns a named logger writing to both the console and a rotating log file.

    Args:
        name:     Logger name, typically __name__ of the calling module.
        log_file: File name (e.g. "backend.log") relative to the logs/ directory.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)

    # Guard against adding duplicate handlers if the root logger was already set
    if logger.handlers:
        _configured_loggers[name] = logger
        return logger

    logger.setLevel(logging.DEBUG)  # Capture everything; handlers filter by level

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # ── Console handler (INFO+) ──────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ── File handler (DEBUG+, rotating) ─────────────────────────────────────
    os.makedirs(_LOG_DIR, exist_ok=True)
    log_path = os.path.join(_LOG_DIR, log_file)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Prevent log records from propagating to the root logger
    logger.propagate = False

    _configured_loggers[name] = logger
    return logger
