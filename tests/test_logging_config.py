"""Tests for structured logging configuration."""

import json
import logging
import os

from ssg.logging_config import (
    LOGGING_FRAMEWORK,
    LOG_LEVEL_ENV,
    StructuredFormatter,
    configure_logging,
    resolve_log_level,
)


def test_logging_framework_constant():
    assert LOGGING_FRAMEWORK == "ssg-structured"


def test_resolve_log_level_from_env(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV, "DEBUG")
    assert resolve_log_level() == logging.DEBUG
    monkeypatch.setenv(LOG_LEVEL_ENV, "ERROR")
    assert resolve_log_level() == logging.ERROR


def test_structured_formatter_json():
    record = logging.LogRecord(
        name="ssg",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    payload = json.loads(StructuredFormatter().format(record))
    assert payload["msg"] == "hello"
    assert payload["framework"] == LOGGING_FRAMEWORK
    assert payload["level"] == "INFO"


def test_configure_logging_uses_env(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV, "WARNING")
    logger = configure_logging()
    assert logger.level == logging.WARNING
    assert logger.handlers
