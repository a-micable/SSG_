from pathlib import Path
from ssg.analyzer import Analyzer


def test_analyzer_runs_on_repo_root():
    root = Path(".")
    analyzer = Analyzer(root=root)
    report = analyzer.run()

    assert "total_files" in report
    assert "languages" in report
    assert "loc" in report
    assert "operational" in report
    assert isinstance(report["warnings"], list)
