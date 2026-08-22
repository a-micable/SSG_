"""Named input and schema validation helpers used by the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .error_tracking import tracker


class ValidationError(Exception):
    """Raised when argv or config schema validation fails."""


def input_validation_argv(argv: Optional[Sequence[str]]) -> List[str]:
    """Reject missing or non-string argv fragments before Click dispatch."""
    if argv is None:
        raise ValidationError("argv is required")
    cleaned: List[str] = []
    for item in argv:
        if not isinstance(item, str) or not item.strip():
            tracker.capture("invalid_argv", "empty argv token", {"token": item})
            raise ValidationError("argv tokens must be non-empty strings")
        cleaned.append(item)
    if not cleaned:
        tracker.capture("invalid_argv", "empty argv", {})
        raise ValidationError("argv must contain at least one token")
    return cleaned


def input_validation_port(port: int) -> int:
    if not isinstance(port, int) or port < 1 or port > 65535:
        tracker.capture("invalid_port", "port out of range", {"port": port})
        raise ValidationError("port must be an integer between 1 and 65535")
    return port


def schema_validation_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate required keys of a loaded YAML config mapping."""
    if not isinstance(data, dict):
        raise ValidationError("config schema must be a mapping")
    missing = [k for k in ("site_name", "base_url") if k not in data or not data[k]]
    if missing:
        tracker.capture("invalid_schema", "missing required keys", {"keys": missing})
        raise ValidationError(f"missing required config keys: {', '.join(missing)}")
    base_url = str(data["base_url"])
    if not base_url.startswith(("http://", "https://")):
        tracker.capture("invalid_schema", "bad base_url", {"base_url": base_url})
        raise ValidationError("base_url must start with http:// or https://")
    return data


def schema_validation_path(path: Path, *, must_exist: bool = False) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    if must_exist and not path.exists():
        tracker.capture("invalid_path", "path does not exist", {"path": str(path)})
        raise ValidationError(f"path does not exist: {path}")
    return path
