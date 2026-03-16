"""Centralized logging configuration for the InfoHub application.

Call `setup_logging()` once at application startup (CLI main or API app creation).
All modules then use `logging.getLogger(__name__)` to get their logger.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = APP_ROOT / "logs"

_configured = False


def setup_logging(level: str | None = None) -> None:
    """Configure root logger with console + rotating file handlers.

    - Console: INFO level (or env override)
    - File: DEBUG level, rolling 10 MB x 5 backups
    """
    global _configured
    if _configured:
        return
    _configured = True

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    effective_level = getattr(logging, (level or os.environ.get("LOG_LEVEL", "DEBUG")).upper(), logging.DEBUG)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  [%(name)s:%(lineno)d]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — INFO+ by default
    console_handler = logging.StreamHandler()
    console_handler.setLevel(max(effective_level, logging.INFO))
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Rotating file handler — DEBUG, 10 MB x 5 backups
    file_handler = RotatingFileHandler(
        LOGS_DIR / "infohub.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Quiet noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)