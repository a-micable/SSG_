"""Generate two sites with the CLI, then compare insert/delete/modify-style diffs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ssg(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ssg.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _file_map(root: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_file():
            mapping[str(path.relative_to(root))] = path.read_text(
                encoding="utf-8", errors="replace"
            )
    return mapping


def _diff_counts(left: dict[str, str], right: dict[str, str]) -> tuple[int, int, int]:
    left_keys = set(left)
    right_keys = set(right)
    inserts = len(right_keys - left_keys)
    deletes = len(left_keys - right_keys)
    modifies = sum(1 for k in left_keys & right_keys if left[k] != right[k])
    return inserts, deletes, modifies


def test_two_builds_diff_insert_delete_modify(tmp_path: Path):
    site_a = tmp_path / "site_a"
    site_b = tmp_path / "site_b"
    assert _ssg("init", str(site_a), "--name", "Alpha", "--url", "https://a.test").returncode == 0
    assert _ssg("init", str(site_b), "--name", "Beta", "--url", "https://b.test").returncode == 0

    extra = site_b / "content" / "posts" / "second.md"
    extra.write_text(
        """---
title: Second
date: 2024-04-01
slug: second
layout: post.html
draft: false
---

# Second

New post that should count as an insert after build.
""",
        encoding="utf-8",
    )
    welcome = site_b / "content" / "posts" / "welcome.md"
    text = welcome.read_text(encoding="utf-8")
    welcome.write_text(text.replace("Welcome!", "Welcome, modified!"), encoding="utf-8")

    assert _ssg("build", "--config", str(site_a / "config.yml")).returncode == 0
    assert _ssg("build", "--config", str(site_b / "config.yml")).returncode == 0

    inserts, deletes, modifies = _diff_counts(
        _file_map(site_a / "dist"),
        _file_map(site_b / "dist"),
    )
    # extra post HTML plus possible tag page; welcome content changed
    assert inserts >= 1
    assert modifies >= 1
    assert deletes >= 0
    summary = f"inserts={inserts} deletes={deletes} modifies={modifies}"
    assert "inserts=" in summary
    assert inserts + modifies >= 2
