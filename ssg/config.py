"""
Configuration management for the SSG.
Loads and validates site configuration from YAML files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .validation import ValidationError, schema_validation_config


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required fields."""

    pass


@dataclass
class SiteConfig:
    """
    Complete site configuration.

    Attributes:
        site_name: Name of the site
        base_url: Base URL for the site (e.g., https://example.com)
        content_dir: Directory containing content files
        template_dir: Directory containing Jinja2 templates
        output_dir: Directory where built site is generated
        posts_per_page: Number of posts per paginated page
        date_format: Python strftime format for dates
        timezone: Timezone for date handling
        asset_dirs: Directories to copy as static assets
        build_drafts: Whether to build draft content
        feed_enabled: Whether to generate RSS feed
        sitemap_enabled: Whether to generate XML sitemap
        author: Default author name
        description: Site description
        language: Site language code
    """

    site_name: str
    base_url: str
    content_dir: Path
    template_dir: Path
    output_dir: Path
    posts_per_page: int = 10
    date_format: str = "%Y-%m-%d"
    timezone: str = "UTC"
    asset_dirs: list[str] = field(default_factory=lambda: ["assets", "static"])
    build_drafts: bool = False
    feed_enabled: bool = True
    sitemap_enabled: bool = True
    author: str | None = None
    description: str | None = None
    language: str = "en"

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.content_dir, str):
            self.content_dir = Path(self.content_dir)
        if isinstance(self.template_dir, str):
            self.template_dir = Path(self.template_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

    def validate(self) -> None:
        """
        Validate configuration settings.

        Raises:
            ConfigError: If any required fields are missing or invalid
        """
        errors = []

        if not self.site_name:
            errors.append("site_name is required")

        if not self.base_url:
            errors.append("base_url is required")
        elif not self.base_url.startswith(("http://", "https://")):
            errors.append("base_url must start with http:// or https://")

        if self.posts_per_page < 1:
            errors.append("posts_per_page must be at least 1")

        if not self.content_dir.exists():
            errors.append(f"content_dir does not exist: {self.content_dir}")

        if not self.template_dir.exists():
            errors.append(f"template_dir does not exist: {self.template_dir}")

        if errors:
            raise ConfigError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )


class ConfigLoader:
    """Loads configuration from YAML files."""

    REQUIRED_FIELDS = ["site_name", "base_url"]

    @classmethod
    def load(cls, config_path: Path) -> SiteConfig:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Returns:
            Loaded and validated SiteConfig

        Raises:
            ConfigError: If configuration file is invalid or missing required fields
        """
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse configuration YAML: {e}")

        if not isinstance(raw_config, dict):
            raise ConfigError("Configuration must be a YAML dictionary")

        try:
            schema_validation_config(raw_config)
        except ValidationError as e:
            raise ConfigError(f"Missing required fields: {e}") from e

        env_output = os.getenv("SSG_OUTPUT_DIR")
        if env_output:
            raw_config["output_dir"] = env_output

        # Set defaults for paths relative to config file
        config_dir = config_path.parent
        if "content_dir" not in raw_config:
            raw_config["content_dir"] = config_dir / "content"
        if "template_dir" not in raw_config:
            raw_config["template_dir"] = config_dir / "templates"
        if "output_dir" not in raw_config:
            raw_config["output_dir"] = config_dir / "dist"

        # Convert relative paths to absolute
        for path_field in ["content_dir", "template_dir", "output_dir"]:
            if path_field in raw_config:
                path_value = Path(raw_config[path_field])
                if not path_value.is_absolute():
                    raw_config[path_field] = config_dir / path_value

        try:
            config = SiteConfig(**raw_config)
            config.validate()
            return config
        except TypeError as e:
            raise ConfigError(f"Invalid configuration fields: {e}")

    @classmethod
    def create_default(cls, site_dir: Path, site_name: str, base_url: str) -> SiteConfig:
        """
        Create a default configuration for a new site.

        Args:
            site_dir: Root directory of the site
            site_name: Name of the site
            base_url: Base URL for the site

        Returns:
            Default SiteConfig
        """
        return SiteConfig(
            site_name=site_name,
            base_url=base_url,
            content_dir=site_dir / "content",
            template_dir=site_dir / "templates",
            output_dir=site_dir / "dist",
        )
