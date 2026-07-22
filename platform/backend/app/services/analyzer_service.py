from pathlib import Path
from typing import Any, Dict
from ssg.analyzer import Analyzer


class AnalyzerService:
    """Thin service wrapper around the existing `ssg` Analyzer for platform use."""

    def __init__(self, root: Path = Path('.')):
        self.root = Path(root)

    def run(self) -> Dict[str, Any]:
        analyzer = Analyzer(self.root)
        return analyzer.run()
