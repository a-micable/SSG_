from pathlib import Path
from typing import Dict, List, Tuple
import re


class Scanner:
    """Lightweight repository scanner that collects file counts, LOC, and suspicious patterns."""

    SUSPICIOUS_PATTERNS = [
        r"\beval\(",
        r"\bexec\(",
        r"password",
        r"secret",
        r"aws_access_key",
        r"aws_secret",
        r"TODO",
        r"FIXME",
    ]

    def __init__(self, root: Path):
        self.root = Path(root)

    def scan(self) -> Dict:
        files_by_ext = {}
        loc_by_ext = {}
        findings: List[Tuple[str, int, str]] = []

        for path in self.root.rglob('*'):
            if path.is_file():
                try:
                    ext = path.suffix.lower() or 'noext'
                    files_by_ext[ext] = files_by_ext.get(ext, 0) + 1

                    # attempt to read text files for LOC and patterns
                    text = path.read_text(encoding='utf-8', errors='ignore')
                    lines = text.splitlines()
                    loc_by_ext[ext] = loc_by_ext.get(ext, 0) + len(lines)

                    # scan for suspicious patterns
                    for i, line in enumerate(lines, start=1):
                        for pat in self.SUSPICIOUS_PATTERNS:
                            if re.search(pat, line, re.IGNORECASE):
                                findings.append((str(path.relative_to(self.root)), i, line.strip()))
                                break

                except Exception:
                    # binary or unreadable file: count it but skip content
                    ext = path.suffix.lower() or 'noext'
                    files_by_ext[ext] = files_by_ext.get(ext, 0) + 0

        return {
            'files_by_ext': files_by_ext,
            'loc_by_ext': loc_by_ext,
            'findings': findings,
        }
