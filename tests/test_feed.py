"""RSS feed timezone formatting."""

from datetime import datetime, timezone, timedelta

from ssg.config import SiteConfig
from ssg.feed import FeedGenerator
from pathlib import Path


def _generator(tmp_path: Path) -> FeedGenerator:
    content = tmp_path / "content"
    templates = tmp_path / "templates"
    content.mkdir()
    templates.mkdir()
    config = SiteConfig(
        site_name="Feed Site",
        base_url="https://example.test",
        content_dir=content,
        template_dir=templates,
        output_dir=tmp_path / "dist",
    )
    return FeedGenerator(config)


def test_rfc822_date_ends_in_gmt(tmp_path):
    gen = _generator(tmp_path)
    formatted = gen._format_rfc822_date(datetime(2024, 3, 15, 12, 0, 0))
    assert formatted.endswith("GMT")
    assert formatted == "Fri, 15 Mar 2024 12:00:00 GMT"


def test_rfc822_converts_offset_to_utc(tmp_path):
    gen = _generator(tmp_path)
    eastern = datetime(2024, 3, 15, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    formatted = gen._format_rfc822_date(eastern)
    assert formatted.endswith("GMT")
    assert "12:00:00 GMT" in formatted
