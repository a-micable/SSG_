"""Structured logging for the SSG CLI and library."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOGGING_FRAMEWORK = "ssg-structured"
LOG_LEVEL_ENV = "SSG_LOG_LEVEL"
LOG_FORMAT_ENV = "SSG_LOG_FORMAT"

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class StructuredFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "framework": LOGGING_FRAMEWORK,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "ssg_extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


def resolve_log_level(override: Optional[str] = None) -> int:
    raw = (override or os.getenv(LOG_LEVEL_ENV) or "INFO").upper()
    return _LEVELS.get(raw, logging.INFO)


def configure_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure the `ssg` logger from getenv / argv overrides."""
    logger = logging.getLogger("ssg")
    logger.handlers.clear()
    logger.setLevel(resolve_log_level(level))
    handler = logging.StreamHandler(sys.stderr)
    fmt = (os.getenv(LOG_FORMAT_ENV) or "json").lower()
    if fmt == "text":
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str = "ssg") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logging.getLogger("ssg").handlers:
        configure_logging()
    return logger
