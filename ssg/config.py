"""
Configuration management for SSG.

Handles loading, validation, and access to site configuration from YAML files.
Provides strongly-typed configuration models with validation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ssg import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class SiteConfig:
    """
    Strongly-typed site configuration.
    
    Attributes:
        site_name: Display name of the site
        base_url: Base URL for absolute links (no trailing slash)
        content_dir: Directory containing Markdown content
        template_dir: Directory containing Jinja2 templates
        output_dir: Directory where the built site will be generated
        posts_per_page: Number of posts per paginated page
        timezone: Timezone for date handling (default: UTC)
        author: Default author name
        description: Site description for feeds
        language: Language code (default: en)
    """

    site_name: str
    base_url: str
    content_dir: Path
    template_dir: Path
    output_dir: Path
    posts_per_page: int = 10
    timezone: str = "UTC"
    author: Optional[str] = None
    description: Optional[str] = None
    language: str = "en"
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Convert string paths to Path objects
        if isinstance(self.content_dir, str):
            self.content_dir = Path(self.content_dir)
        if isinstance(self.template_dir, str):
            self.template_dir = Path(self.template_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Normalize base_url (remove trailing slash)
        self.base_url = self.base_url.rstrip("/")

        # Validation
        if not self.site_name:
            raise ConfigurationError("site_name is required")
        
        if not self.base_url:
            raise ConfigurationError("base_url is required")
        
        if not self.base_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"base_url must start with http:// or https://, got: {self.base_url}"
            )

        if self.posts_per_page < 1:
            raise ConfigurationError(
                f"posts_per_page must be at least 1, got: {self.posts_per_page}"
            )


def load_config(config_path: Path) -> SiteConfig:
    """
    Load and validate site configuration from a YAML file.
    
    Args:
        config_path: Path to the config.yaml file
        
    Returns:
        Validated SiteConfig instance
        
    Raises:
        ConfigurationError: If config file is missing, invalid, or fails validation
    """
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to read configuration file: {e}")

    if not isinstance(data, dict):
        raise ConfigurationError("Configuration must be a YAML mapping")

    # Extract required fields
    required_fields = ["site_name", "base_url", "content_dir", "template_dir", "output_dir"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ConfigurationError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )

    # Resolve paths relative to config file location
    config_dir = config_path.parent
    
    # Extract and remove known fields, leaving the rest for additional_config
    known_fields = [
        "site_name",
        "base_url",
        "content_dir",
        "template_dir",
        "output_dir",
        "posts_per_page",
        "timezone",
        "author",
        "description",
        "language",
    ]
    
    config_args = {}
    additional = {}
    
    for key, value in data.items():
        if key in known_fields:
            # Resolve paths relative to config directory
            if key in ["content_dir", "template_dir", "output_dir"]:
                if not Path(value).is_absolute():
                    config_args[key] = config_dir / value
                else:
                    config_args[key] = Path(value)
            else:
                config_args[key] = value
        else:
            additional[key] = value
    
    config_args["additional_config"] = additional

    try:
        config = SiteConfig(**config_args)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration structure: {e}")


def create_default_config(output_path: Path, site_name: str = "My Site") -> None:
    """
    Create a default configuration file.
    
    Args:
        output_path: Where to write the config.yaml file
        site_name: Name of the site
    """
    default_config = {
        "site_name": site_name,
        "base_url": "https://example.com",
        "content_dir": "content",
        "template_dir": "templates",
        "output_dir": "dist",
        "posts_per_page": 10,
        "timezone": "UTC",
        "author": "Your Name",
        "description": "A site built with SSG",
        "language": "en",
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Created default configuration at {output_path}")
