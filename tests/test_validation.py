"""Behavioral tests: malformed argv and Result-style validation failures."""

import pytest

from ssg.validation import (
    ValidationError,
    input_validation_argv,
    input_validation_port,
    schema_validation_config,
    schema_validation_path,
)
from ssg.error_tracking import tracker
from pathlib import Path


def test_input_validation_argv_rejects_empty():
    tracker.events.clear()
    with pytest.raises(ValidationError):
        input_validation_argv([])
    assert tracker.events[-1].code == "invalid_argv"


def test_input_validation_argv_rejects_blank_token():
    with pytest.raises(ValidationError):
        input_validation_argv(["ssg", "  "])


def test_input_validation_argv_accepts_command():
    assert input_validation_argv(["ssg", "build"]) == ["ssg", "build"]


def test_input_validation_port_bounds():
    assert input_validation_port(8000) == 8000
    with pytest.raises(ValidationError):
        input_validation_port(0)
    with pytest.raises(ValidationError):
        input_validation_port(70000)


def test_schema_validation_config_missing_keys():
    with pytest.raises(ValidationError, match="missing required"):
        schema_validation_config({"site_name": "x"})


def test_schema_validation_config_bad_url():
    with pytest.raises(ValidationError, match="base_url"):
        schema_validation_config({"site_name": "x", "base_url": "ftp://nope"})


def test_schema_validation_path_missing(tmp_path):
    missing = tmp_path / "nope.yml"
    with pytest.raises(ValidationError, match="does not exist"):
        schema_validation_path(missing, must_exist=True)
    assert schema_validation_path(Path("."), must_exist=True).exists()
