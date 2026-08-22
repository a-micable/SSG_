"""Tests for in-process error tracking and counters."""

from ssg.error_tracking import ERROR_TRACKING_BACKEND, ErrorTracker
from ssg.runtime_metrics import METRICS_BACKEND, increment, reset, snapshot


def test_error_tracker_records_events():
    t = ErrorTracker()
    t.capture("bad_config", "nope", {"file": "config.yml"})
    data = t.as_json()
    assert data["backend"] == ERROR_TRACKING_BACKEND
    assert data["count"] == 1
    assert data["events"][0]["code"] == "bad_config"


def test_runtime_metrics_increment():
    reset()
    increment("cli.build", 2)
    snap = snapshot()
    assert snap["cli.build"] == 2
    assert METRICS_BACKEND == "ssg-counters"
