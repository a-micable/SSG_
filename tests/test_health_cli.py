"""CLI health JSON and analyze command."""

import json
import subprocess
import sys
from pathlib import Path


def test_health_json():
    result = subprocess.run(
        [sys.executable, "-m", "ssg.cli", "health"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["classification"] == "cli-tool"
    assert payload["logging_framework"] == "ssg-structured"
    assert "metrics" in payload
    assert "error_tracking" in payload


def test_analyze_json(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ssg.cli",
            "analyze",
            "--path",
            str(Path(__file__).resolve().parents[1] / "ssg"),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout[result.stdout.find("{") :])
    assert payload["total_files"] >= 1
    assert "Python" in payload["languages"] or "python" in {k.lower() for k in payload["languages"]}
