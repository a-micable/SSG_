"""Tests for configuration loading and validation."""

from pathlib import Path
import pytest
import yaml
from ssg.config import SiteConfig, ConfigLoader, ConfigError


class TestSiteConfig:
    """Test cases for SiteConfig dataclass."""

    def test_site_config_valid(self):
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
        assert config.posts_per_page == 10  # Default value

    def test_validates_base_url(self, temp_dir):
        """Test that invalid base URLs are caught during validation."""
        # Create directories
        (temp_dir / "content").mkdir()
        (temp_dir / "templates").mkdir()

        config = SiteConfig(
            site_name="Test",
            base_url="invalid-url",  # Missing protocol
            content_dir=temp_dir / "content",
            template_dir=temp_dir / "templates",
            output_dir=temp_dir / "dist",
        )

        with pytest.raises(ConfigError, match="base_url must start with"):
            config.validate()

    def test_missing_site_name(self, temp_dir):
        """Test that missing site_name is caught."""
        (temp_dir / "content").mkdir()
        (temp_dir / "templates").mkdir()

        config = SiteConfig(
            site_name="",
            base_url="https://example.com",
            content_dir=temp_dir / "content",
            template_dir=temp_dir / "templates",
            output_dir=temp_dir / "dist",
        )

        with pytest.raises(ConfigError, match="site_name is required"):
            config.validate()


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_load_config_file(self, temp_dir):
        """Test loading configuration from YAML file."""
        # Create directories
        (temp_dir / "content").mkdir()
        (temp_dir / "templates").mkdir()

        # Create config file
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
site_name: Test Site
base_url: https://example.com
posts_per_page: 5
""")

        config = ConfigLoader.load(config_file)

        assert config.site_name == "Test Site"
        assert config.base_url == "https://example.com"
        assert config.posts_per_page == 5

    def test_load_missing_file(self, temp_dir):
        """Test that loading non-existent file raises error."""
        with pytest.raises(ConfigError, match="Configuration file not found"):
            ConfigLoader.load(temp_dir / "nonexistent.yml")

    def test_load_missing_required_fields(self, temp_dir):
        """Test that missing required fields raise error."""
        config_file = temp_dir / "config.yml"
        config_file.write_text("site_name: Test Site\n")  # Missing base_url

        with pytest.raises(ConfigError, match="Missing required fields"):
            ConfigLoader.load(config_file)

    def test_create_default(self, temp_dir):
        """Test creating default configuration."""
        config = ConfigLoader.create_default(temp_dir, "Test Site", "https://example.com")

        assert config.site_name == "Test Site"
        assert config.base_url == "https://example.com"
        assert config.content_dir == temp_dir / "content"
