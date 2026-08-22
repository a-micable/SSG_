"""Tests for ssg init file scaffolding."""

from pathlib import Path

from ssg.site_scaffold import write_new_site


def test_write_new_site_creates_config_and_welcome(tmp_path: Path):
    notes: list[str] = []
    write_new_site(tmp_path, "Scaffold Site", "https://example.test", echo=notes.append)
    assert (tmp_path / "config.yml").is_file()
    assert "Scaffold Site" in (tmp_path / "config.yml").read_text(encoding="utf-8")
    assert (tmp_path / "content" / "posts" / "welcome.md").is_file()
    assert (tmp_path / "templates" / "base.html").is_file()
    assert (tmp_path / "assets" / "css" / "style.css").is_file()
    assert any("config.yml" in n for n in notes)
