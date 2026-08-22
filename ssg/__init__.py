"""
SSG - A production-grade static site generator.

This package provides a complete static site generation system with:
- Markdown content processing with frontmatter support
- Jinja2 templating with layout inheritance
- Asset processing with fingerprinting
- Incremental builds with dependency tracking
- RSS feed and sitemap generation
- Development server with live reload
"""

__version__ = "1.0.0"
__author__ = "SSG Contributors"


class SSGError(Exception):
    """Base exception for all SSG-related errors."""

    pass


class ConfigurationError(SSGError):
    """Raised when configuration is invalid or missing required fields."""

    pass


class ParsingError(SSGError):
    """Raised when content parsing fails."""

    pass


class RenderingError(SSGError):
    """Raised when template rendering fails."""

    pass


class BuildError(SSGError):
    """Raised when the build process encounters an error."""

    pass
