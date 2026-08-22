"""Tests for structured logging configuration."""

import json
import logging
from datetime import datetime

from ssg.logging_config import (
    LOG_LEVEL_ENV,
    LOGGING_FRAMEWORK,
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


def test_builder_logs_parse_content_not_print(sample_config, capsys):
    configure_logging()
    from ssg.builder import SiteBuilder

    SiteBuilder(sample_config).parse_content()
    captured = capsys.readouterr()
    assert "parse_content" in captured.err
    assert '"logger": "ssg.builder"' in captured.err
    assert "Parsing content from" not in captured.out


def test_assets_process_directory_logs(sample_config, temp_dir, capsys):
    configure_logging()
    from ssg.assets import AssetProcessor

    asset_dir = temp_dir / "assets"
    asset_dir.mkdir(exist_ok=True)
    (asset_dir / "style.css").write_text("body{}", encoding="utf-8")
    AssetProcessor(sample_config).process_directory(asset_dir)
    captured = capsys.readouterr()
    assert "process_directory" in captured.err
    assert '"logger": "ssg.assets"' in captured.err
    assert "Processed" not in captured.out


def test_feed_generate_logs(tmp_path, capsys):
    configure_logging()
    from ssg.config import SiteConfig
    from ssg.feed import FeedGenerator
    from ssg.parser import ParsedContent

    content = tmp_path / "content"
    templates = tmp_path / "templates"
    out = tmp_path / "dist"
    content.mkdir()
    templates.mkdir()
    out.mkdir()
    config = SiteConfig(
        site_name="Log Site",
        base_url="https://example.test",
        content_dir=content,
        template_dir=templates,
        output_dir=out,
    )
    item = ParsedContent(
        source_path=content / "a.md",
        title="A",
        content="<p>a</p>",
        raw_content="a",
        date=datetime(2024, 1, 1),
        slug="a",
    )
    FeedGenerator(config).generate([item])
    captured = capsys.readouterr()
    assert "feed_generated" in captured.err
    assert '"logger": "ssg.feed"' in captured.err
    assert "Generated RSS feed" not in captured.out
