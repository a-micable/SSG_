"""
Template rendering using Jinja2.
Handles layout inheritance, includes, and custom filters.
"""

from datetime import date as Date
from datetime import datetime, time
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .config import SiteConfig
from .parser import ParsedContent


class RenderError(Exception):
    """Raised when template rendering fails."""

    pass


class Renderer:
    """Jinja2-based template renderer with custom filters including strftime."""

    def __init__(self, config: SiteConfig):
        """
        Initialize the renderer.

        Args:
            config: Site configuration
        """
        self.config = config

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(config.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.env.filters["strftime"] = self._filter_strftime
        self.env.filters["dateformat"] = self._filter_dateformat
        self.env.filters["excerpt"] = self._filter_excerpt
        self.env.filters["limit"] = self._filter_limit

        # Register global functions
        self.env.globals["now"] = datetime.now
        self.env.globals["url_for"] = self._url_for

    def _filter_strftime(self, date_value: Any, format_string: str) -> str:
        """Format datetime, date, or ISO string values with strftime."""
        if isinstance(date_value, datetime):
            return date_value.strftime(format_string)
        if isinstance(date_value, Date):
            return datetime.combine(date_value, time.min).strftime(format_string)
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value)
                return date_value.strftime(format_string)
            except (ValueError, AttributeError):
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(date_value, fmt).strftime(format_string)
                    except ValueError:
                        continue
                return date_value
        return str(date_value)

    def _filter_dateformat(self, date_value: Any, format_string: str | None = None) -> str:
        """
        Format a date using configured or custom format.

        Args:
            date_value: Date to format
            format_string: Optional custom format (uses config default if not provided)

        Returns:
            Formatted date string
        """
        if format_string is None:
            format_string = self.config.date_format

        return self._filter_strftime(date_value, format_string)

    def _filter_excerpt(self, text: str, length: int = 200) -> str:
        """
        Extract an excerpt from text.

        Args:
            text: Text to excerpt
            length: Maximum length

        Returns:
            Excerpted text
        """
        if len(text) <= length:
            return text

        excerpt = text[:length].rsplit(" ", 1)[0]
        return excerpt + "..."

    def _filter_limit(self, items: list[Any], count: int) -> list[Any]:
        """
        Limit a list to a specific number of items.

        Args:
            items: List to limit
            count: Maximum number of items

        Returns:
            Limited list
        """
        return items[:count]

    def _url_for(self, path: str) -> str:
        """
        Generate a full URL for a path.

        Args:
            path: Relative path

        Returns:
            Full URL
        """
        base = self.config.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Template context variables

        Returns:
            Rendered HTML

        Raises:
            RenderError: If template is not found or rendering fails
        """
        # Add site config to context
        context.setdefault(
            "site",
            {
                "name": self.config.site_name,
                "base_url": self.config.base_url,
                "description": self.config.description,
                "author": self.config.author,
                "language": self.config.language,
            },
        )

        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise RenderError(f"Template not found: {template_name}")
        except Exception as e:
            raise RenderError(f"Failed to render {template_name}: {e}")

    def render_content(
        self, content: ParsedContent, extra_context: dict[str, Any] | None = None
    ) -> str:
        """
        Render a ParsedContent object using its layout template.

        Args:
            content: Parsed content to render
            extra_context: Additional context variables

        Returns:
            Rendered HTML
        """
        context = {
            "content": content.content,
            "title": content.title,
            "date": content.date,
            "tags": content.tags,
            "url": content.url,
            **content.metadata,
        }

        if extra_context:
            context.update(extra_context)

        return self.render(content.layout, context)

    def render_list(
        self,
        template_name: str,
        items: list[ParsedContent],
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a list of content items.

        Args:
            template_name: Template to use
            items: List of content items
            extra_context: Additional context variables

        Returns:
            Rendered HTML
        """
        context = {
            "items": items,
            "posts": items,  # Alias for convenience
        }

        if extra_context:
            context.update(extra_context)

        return self.render(template_name, context)
