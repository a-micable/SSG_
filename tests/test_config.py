"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest
import yaml

from ssg import ConfigurationError
from ssg.config import SiteConfig, create_default_config, load_config


def test_site_config_valid():
    """Test creating a valid SiteConfig."""
    config = SiteConfig(
        site_name="Test Site",
        base_url="https://example.com",
        content_dir=Path("content"),
        template_dir=Path("templates"),
        output_dir=Path("dist"),
    )
    
    assert config.site_name == "Test Site"
    assert config.base_url == "https://example.com"
    assert config.posts_per_page == 10  # Default


def test_site_config_validates_base_url():
    """Test that base_url must start with http:// or https://."""
    with pytest.raises(ConfigurationError, match="must start with"):
        SiteConfig(
            site_name="Test",
            base_url="example.com",  # Missing protocol
            content_dir=Path("content"),
            template_dir=Path("templates"),
            output_dir=Path("dist"),
        )


def test_site_config_validates_posts_per_page():
    """Test that posts_per_page must be positive."""
    with pytest.raises(ConfigurationError, match="must be at least 1"):
        SiteConfig(
            site_name="Test",
            base_url="https://example.com",
            content_dir=Path("content"),
            template_dir=Path("templates"),
            output_dir=Path("dist"),
            posts_per_page=0,
        )


def test_site_config_normalizes_base_url():
    """Test that trailing slash is removed from base_url."""
    config = SiteConfig(
        site_name="Test",
        base_url="https://example.com/",  # With trailing slash
        content_dir=Path("content"),
        template_dir=Path("templates"),
        output_dir=Path("dist"),
    )
    
    assert config.base_url == "https://example.com"


def test_load_config_from_file(temp_dir: Path):
    """Test loading configuration from a YAML file."""
    config_path = temp_dir / "config.yaml"
    config_data = {
        "site_name": "My Blog",
        "base_url": "https://myblog.com",
        "content_dir": "content",
        "template_dir": "templates",
        "output_dir": "dist",
        "posts_per_page": 15,
        "author": "John Doe",
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    config = load_config(config_path)
    
    assert config.site_name == "My Blog"
    assert config.base_url == "https://myblog.com"
    assert config.posts_per_page == 15
    assert config.author == "John Doe"


def test_load_config_missing_file():
    """Test that loading non-existent config raises error."""
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(Path("nonexistent.yaml"))


def test_load_config_missing_required_fields(temp_dir: Path):
    """Test that missing required fields raises error."""
    config_path = temp_dir / "config.yaml"
    config_data = {
        "site_name": "My Blog",
        # Missing other required fields
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    with pytest.raises(ConfigurationError, match="Missing required"):
        load_config(config_path)


def test_load_config_resolves_relative_paths(temp_dir: Path):
    """Test that relative paths are resolved relative to config file."""
    config_path = temp_dir / "config.yaml"
    config_data = {
        "site_name": "Test",
        "base_url": "https://example.com",
        "content_dir": "content",
        "template_dir": "templates",
        "output_dir": "dist",
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    config = load_config(config_path)
    
    assert config.content_dir == temp_dir / "content"
    assert config.template_dir == temp_dir / "templates"
    assert config.output_dir == temp_dir / "dist"


def test_create_default_config(temp_dir: Path):
    """Test creating a default configuration file."""
    config_path = temp_dir / "config.yaml"
    create_default_config(config_path, "My New Site")
    
    assert config_path.exists()
    
    config = load_config(config_path)
    assert config.site_name == "My New Site"
    assert config.posts_per_page == 10


def test_config_additional_fields(temp_dir: Path):
    """Test that additional config fields are preserved."""
    config_path = temp_dir / "config.yaml"
    config_data = {
        "site_name": "Test",
        "base_url": "https://example.com",
        "content_dir": "content",
        "template_dir": "templates",
        "output_dir": "dist",
        "custom_field": "custom_value",
        "another_field": 123,
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    config = load_config(config_path)
    
    assert config.additional_config["custom_field"] == "custom_value"
    assert config.additional_config["another_field"] == 123
