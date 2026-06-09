"""Tests for configuration loading and validation."""
from pathlib import Path
import pytest
import yaml
from ssg import ConfigurationError
from ssg.config import SiteConfig, load_config

def test_site_config_valid():
    config = SiteConfig(
        site_name="Test", base_url="https://example.com",
        content_dir=Path("content"), template_dir=Path("templates"),
        output_dir=Path("dist"))
    assert config.site_name == "Test"

def test_validates_base_url():
    with pytest.raises(ConfigurationError):
        SiteConfig(site_name="Test", base_url="example.com",
                   content_dir=Path("c"), template_dir=Path("t"), output_dir=Path("d"))
