"""
Template rendering for SSG.

Handles Jinja2 template rendering with custom filters and context building.
Manages template inheritance and includes.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    select_autoescape,
)

from ssg import RenderingError
from ssg.config import SiteConfig
from ssg.parser import ParsedContent

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Renders content using Jinja2 templates.
    
    Provides template loading, custom filters, and context management
    for rendering content into final HTML pages.
    """

    def __init__(self, config: SiteConfig) -> None:
        """
        Initialize the renderer with configuration.
        
        Args:
            config: Site configuration
        """
        self.config = config

        if not config.template_dir.exists():
            raise RenderingError(f"Template directory not found: {config.template_dir}")

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(config.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

        logger.info(f"Initialized template renderer with templates from {config.template_dir}")

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["strftime"] = self._filter_strftime
        self.env.filters["date"] = self._filter_date
        self.env.filters["url"] = self._filter_url

    def _filter_strftime(self, value: Any, format_string: str = "%Y-%m-%d") -> str:
        """
        Format a datetime object using strftime.
        
        BUG 1 SYMPTOM: This will fail when value is a string (from parser bug)
        because strings don't have strftime method.
        
        Args:
            value: datetime object or string
            format_string: strftime format string
            
        Returns:
            Formatted date string
        """
        if isinstance(value, datetime):
            return value.strftime(format_string)
        elif isinstance(value, str):
            # BUG 1 SYMPTOM: When parser returns date as string, this will fail
            # if template tries to use strftime filter
            # This error manifests in templates, but root cause is in parser.py
            raise RenderingError(
                f"Cannot format date: expected datetime object, got string '{value}'. "
                "This usually indicates a parsing issue."
            )
        elif value is None:
            return ""
        else:
            raise RenderingError(f"Cannot format date: unsupported type {type(value)}")

    def _filter_date(self, value: Any, format_string: str = "%B %d, %Y") -> str:
        """
        Format a date with a more readable default format.
        
        Args:
            value: datetime object
            format_string: strftime format string
            
        Returns:
            Formatted date string
        """
        return self._filter_strftime(value, format_string)

    def _filter_url(self, path: str) -> str:
        """
        Convert a relative path to an absolute URL.
        
        Args:
            path: Relative path
            
        Returns:
            Absolute URL with base_url prepended
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
            
        return self.config.base_url + path

    def render_content(
        self,
        content: ParsedContent,
        site_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a content item using its specified template.
        
        Args:
            content: Parsed content to render
            site_context: Additional site-wide context (collections, etc.)
            
        Returns:
            Rendered HTML string
            
        Raises:
            RenderingError: If template not found or rendering fails
        """
        template_name = content.metadata.layout

        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise RenderingError(
                f"Template not found: {template_name} (required by {content.source_path})"
            )

        # Build template context
        context = self._build_context(content, site_context or {})

        try:
            html = template.render(**context)
            return html
        except Exception as e:
            raise RenderingError(
                f"Failed to render {content.source_path} with template {template_name}: {e}"
            )

    def render_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """
        Render a template with arbitrary context.
        
        Used for special pages like tag archives, pagination pages, etc.
        
        Args:
            template_name: Name of template file
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
            
        Raises:
            RenderingError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise RenderingError(f"Template not found: {template_name}")

        # Add site config to context
        full_context = {
            "site": {
                "name": self.config.site_name,
                "base_url": self.config.base_url,
                "author": self.config.author,
                "description": self.config.description,
                "language": self.config.language,
            },
            **context,
        }

        try:
            html = template.render(**full_context)
            return html
        except Exception as e:
            raise RenderingError(f"Failed to render template {template_name}: {e}")

    def _build_context(
        self, content: ParsedContent, site_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the template context for a content item.
        
        Args:
            content: Parsed content
            site_context: Additional site-wide context
            
        Returns:
            Complete template context dictionary
        """
        context = {
            "site": {
                "name": self.config.site_name,
                "base_url": self.config.base_url,
                "author": self.config.author,
                "description": self.config.description,
                "language": self.config.language,
            },
            "page": {
                "title": content.metadata.title,
                "date": content.metadata.date,
                "tags": content.metadata.tags,
                "author": content.metadata.author or self.config.author,
                "description": content.metadata.description,
                "url": content.url_path,
                **content.metadata.custom,
            },
            "content": content.html,
        }

        # Merge site-wide context (collections, archives, etc.)
        context.update(site_context)

        return context

    def get_template_dependencies(self, template_name: str) -> List[Path]:
        """
        Get all template files that a template depends on (via extends/include).
        
        This is used for incremental build dependency tracking (BUG 2 location).
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of Path objects for all dependent templates
        """
        dependencies = []
        visited = set()

        def collect_deps(tpl_name: str) -> None:
            if tpl_name in visited:
                return
            visited.add(tpl_name)

            try:
                # Get the template source
                source, filename, _ = self.env.loader.get_source(self.env, tpl_name)
                if filename:
                    dependencies.append(Path(filename))

                # Parse template to find extends/includes
                # This is a simplified implementation
                # BUG 2: Dependency tracking might miss some edge cases
                # causing templates not to rebuild when base templates change
                ast = self.env.parse(source)
                
                # Extract referenced templates (this is simplified)
                for node in ast.find_all(()):
                    node_type = type(node).__name__
                    if node_type in ["Extends", "Include"]:
                        if hasattr(node, "template"):
                            if hasattr(node.template, "value"):
                                ref_template = node.template.value
                                collect_deps(ref_template)

            except TemplateNotFound:
                logger.warning(f"Template not found during dependency scan: {tpl_name}")
            except Exception as e:
                logger.warning(f"Failed to scan template dependencies for {tpl_name}: {e}")

        collect_deps(template_name)
        return dependencies
