"""Light in-process counters for CLI operations."""

from __future__ import annotations

from collections import Counter
from typing import Dict

METRICS_BACKEND = "ssg-counters"

_counters: Counter[str] = Counter()


def increment(name: str, n: int = 1) -> int:
    _counters[name] += n
    return _counters[name]


def snapshot() -> Dict[str, int]:
    return dict(_counters)


def reset() -> None:
    _counters.clear()


def as_json() -> Dict[str, object]:
    return {"backend": METRICS_BACKEND, "counters": snapshot()}
