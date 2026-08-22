"""Shell out to the installed `ssg` CLI: init → build → assert HTML and record counts."""

from __future__ import annotations

import subprocess
import sys
import zlib
from pathlib import Path


def _ssg(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ssg.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_init_build_roundtrip(tmp_path: Path):
    site = tmp_path / "blog"
    init = _ssg("init", str(site), "--name", "Roundtrip Blog", "--url", "https://example.test")
    assert init.returncode == 0, init.stderr
    assert (site / "config.yml").is_file()
    assert (site / "content" / "posts" / "welcome.md").is_file()

    built = _ssg("build", "--config", str(site / "config.yml"))
    assert built.returncode == 0, built.stderr + built.stdout
    assert "Build complete" in built.stdout

    dist = site / "dist"
    html_files = list(dist.rglob("*.html"))
    assert len(html_files) >= 1
    index = dist / "index.html"
    assert index.is_file()
    body = index.read_text(encoding="utf-8")
    assert "Roundtrip Blog" in body or "Recent Posts" in body or "<html" in body.lower()

    feed = dist / "feed.xml"
    sitemap = dist / "sitemap.xml"
    assert feed.is_file(), "RSS feed missing"
    assert sitemap.is_file(), "sitemap missing"
    assert "<rss" in feed.read_text(encoding="utf-8")
    assert "urlset" in sitemap.read_text(encoding="utf-8")

    digest = zlib.crc32(index.read_bytes()) & 0xFFFFFFFF
    assert digest != 0
    # record counts: one sample post plus index/tag pages
    assert len(html_files) >= 2


def test_cli_build_missing_config_fails(tmp_path: Path):
    missing = tmp_path / "no-such-config.yml"
    result = _ssg("build", "--config", str(missing))
    assert result.returncode != 0
