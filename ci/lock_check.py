#!/usr/bin/env python3
"""Compare package==version pins between committed and freshly compiled hashed locks."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

PIN = re.compile(r"^([A-Za-z0-9_.\[\]-]+)==([^ \\]+)")


def pins(path: Path) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN.match(line)
        if match:
            found.add((match.group(1).lower(), match.group(2)))
    return found


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    committed = root / "ci" / "requirements-ci.txt"
    with tempfile.TemporaryDirectory() as tmp:
        compiled = Path(tmp) / "requirements-ci.txt"
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "piptools",
                "compile",
                "--allow-unsafe",
                "--generate-hashes",
                "--output-file",
                str(compiled),
                str(root / "requirements.in"),
            ]
        )
        a = pins(committed)
        b = pins(compiled)
        if a != b:
            print("missing from committed:", sorted(b - a), file=sys.stderr)
            print("extra in committed:", sorted(a - b), file=sys.stderr)
            return 1
    print(f"lock-check: package pins match ({len(a)} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
