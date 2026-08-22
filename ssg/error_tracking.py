"""In-process error tracking for CLI and library call sites."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

ERROR_TRACKING_BACKEND = "ssg-inprocess"


@dataclass
class TrackedError:
    code: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ErrorTracker:
    def __init__(self) -> None:
        self.backend = ERROR_TRACKING_BACKEND
        self.events: List[TrackedError] = []

    def capture(
        self,
        code: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TrackedError:
        event = TrackedError(code=code, message=message, context=context or {})
        self.events.append(event)
        return event

    def as_json(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "count": len(self.events),
            "events": [
                {
                    "code": e.code,
                    "message": e.message,
                    "context": e.context,
                    "ts": e.ts,
                }
                for e in self.events
            ],
        }


tracker = ErrorTracker()
