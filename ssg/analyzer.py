from pathlib import Path
from .scanner import Scanner
from .metrics import languages_from_ext, loc_summary
from typing import Dict, Any


class AnalysisError(Exception):
    pass


class Analyzer:
    """High-level orchestrator for lightweight codebase analysis."""

    def __init__(self, root: Path = Path('.')):
        self.root = Path(root)
        if not self.root.exists():
            raise AnalysisError(f"Root path does not exist: {root}")

    def run(self) -> Dict[str, Any]:
        scanner = Scanner(self.root)
        scan = scanner.scan()

        files_by_ext = scan.get('files_by_ext', {})
        loc_by_ext = scan.get('loc_by_ext', {})

        languages = languages_from_ext(files_by_ext)
        loc = loc_summary(loc_by_ext)

        operational = {
            'has_dockerfile': (self.root / 'Dockerfile').exists(),
            'has_pyproject': (self.root / 'pyproject.toml').exists(),
            'has_requirements': (self.root / 'requirements.txt').exists(),
            'has_tests': any((self.root / 'tests').glob('**/*.py')) if (self.root / 'tests').exists() else False,
            'has_ci_workflow': any(self.root.glob('.github/workflows/*')) if (self.root / '.github/workflows').exists() else False,
        }

        total_files = sum(files_by_ext.values())

        report = {
            'root': str(self.root),
            'total_files': total_files,
            'languages': dict(sorted(languages.items(), key=lambda kv: -kv[1])),
            'loc': dict(sorted(loc.items(), key=lambda kv: -kv[1])),
            'operational': operational,
            'warnings': [f"{p}:{ln}: {txt}" for (p, ln, txt) in scan.get('findings', [])],
        }

        return report
