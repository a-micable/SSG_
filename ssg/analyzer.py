from pathlib import Path
from typing import Any

from .metrics import (
    languages_from_ext,
    languages_from_lang,
    loc_summary,
    loc_summary_from_lang,
)
from .scanner import Scanner


class AnalysisError(Exception):
    pass


class Analyzer:
    """High-level orchestrator for lightweight codebase analysis."""

    def __init__(self, root: Path = Path(".")):
        self.root = Path(root)
        if not self.root.exists():
            raise AnalysisError(f"Root path does not exist: {root}")

    def run(self) -> dict[str, Any]:
        scanner = Scanner(self.root)
        scan = scanner.scan()

        files_by_ext = scan.get("files_by_ext", {})
        loc_by_ext = scan.get("loc_by_ext", {})

        # prefer content-detected language summaries when available
        files_by_lang = scan.get("files_by_lang")
        loc_by_lang = scan.get("loc_by_lang")

        if files_by_lang and loc_by_lang:
            languages = languages_from_lang(files_by_lang)
            loc = loc_summary_from_lang(loc_by_lang)
        else:
            languages = languages_from_ext(files_by_ext)
            loc = loc_summary(loc_by_ext)

        # compute totals excluding boilerplate
        boilerplate = scan.get("boilerplate_files", [])
        total_files = sum(files_by_ext.values())
        non_boilerplate_files = total_files - len(boilerplate)
        total_loc = sum(loc.values())
        non_boilerplate_loc = total_loc
        # best-effort: if loc_by_lang present, sum those; otherwise rely on loc
        if loc_by_lang:
            non_boilerplate_loc = sum(loc_by_lang.values())

        operational = {
            "has_dockerfile": (self.root / "Dockerfile").exists(),
            "has_pyproject": (self.root / "pyproject.toml").exists(),
            "has_requirements": (self.root / "requirements.txt").exists(),
            "has_tests": any((self.root / "tests").glob("**/*.py"))
            if (self.root / "tests").exists()
            else False,
            "has_ci_workflow": any(self.root.glob(".github/workflows/*"))
            if (self.root / ".github/workflows").exists()
            else False,
        }

        total_files = sum(files_by_ext.values())

        report = {
            "root": str(self.root),
            "total_files": total_files,
            "boilerplate_count": len(boilerplate),
            "non_boilerplate_files": non_boilerplate_files,
            "non_boilerplate_loc": non_boilerplate_loc,
            "languages": dict(sorted(languages.items(), key=lambda kv: -kv[1])),
            "loc": dict(sorted(loc.items(), key=lambda kv: -kv[1])),
            "operational": operational,
            "warnings": [f"{p}:{ln}: {txt}" for (p, ln, txt) in scan.get("findings", [])],
        }

        return report
