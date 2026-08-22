"""
Site builder that orchestrates parsing, rendering, and asset processing.
Handles incremental builds and dependency tracking.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Optional
import re
import shutil
from .config import SiteConfig
from .parser import MarkdownParser, ParsedContent
from .renderer import Renderer
from .assets import AssetProcessor
from .feed import FeedGenerator
from .sitemap import SitemapGenerator
from .logging_config import get_logger

log = get_logger("ssg.builder")


class BuildError(Exception):
    """Raised when build process fails."""

    pass


class DependencyGraph:
    """Tracks content-to-template edges including transitive includes."""

    def __init__(self):
        """Initialize the dependency graph."""
        self.content_to_templates: Dict[Path, Set[Path]] = defaultdict(set)
        self.template_to_content: Dict[Path, Set[Path]] = defaultdict(set)
        self.template_includes: Dict[Path, Set[Path]] = defaultdict(set)

    def add_content_dependency(self, content_path: Path, template_path: Path):
        """Record that content depends on a template."""
        self.content_to_templates[content_path].add(template_path)
        self.template_to_content[template_path].add(content_path)

    def add_template_include(self, parent_template: Path, included_template: Path):
        """Record that a template includes another template."""
        self.template_includes[parent_template].add(included_template)

    def get_affected_content(self, changed_template: Path) -> Set[Path]:
        """Return content that must rebuild when a template (or its includers) change."""
        affected: Set[Path] = set()
        stack = [changed_template]
        seen: Set[Path] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            affected.update(self.template_to_content.get(current, set()))
            for parent, included in self.template_includes.items():
                if current in included and parent not in seen:
                    stack.append(parent)
        return affected


class Paginator:
    """Paginates content lists with ceiling division (no empty extra pages)."""

    def __init__(self, items: List[any], per_page: int = 10):
        """
        Initialize paginator.

        Args:
            items: Items to paginate
            per_page: Items per page
        """
        self.items = items
        self.per_page = per_page

    @property
    def total_pages(self) -> int:
        """Return the number of pages, using ceiling division for exact multiples."""
        if not self.items:
            return 1
        return (len(self.items) + self.per_page - 1) // self.per_page

    def page(self, page_num: int) -> List[any]:
        """Get items for a specific page."""
        start = (page_num - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]

    def has_prev(self, page_num: int) -> bool:
        """Check if there's a previous page."""
        return page_num > 1

    def has_next(self, page_num: int) -> bool:
        """Check if there's a next page."""
        return page_num < self.total_pages


class SiteBuilder:
    """
    Main site builder that orchestrates the build process.
    """

    def __init__(self, config: SiteConfig):
        """
        Initialize the site builder.

        Args:
            config: Site configuration
        """
        self.config = config
        self.parser = MarkdownParser()
        self.renderer = Renderer(config)
        self.asset_processor = AssetProcessor(config)
        self.feed_generator = FeedGenerator(config)
        self.sitemap_generator = SitemapGenerator(config)
        self.dependency_graph = DependencyGraph()
        self.parsed_content: List[ParsedContent] = []

    def clean(self):
        """Clean the output directory."""
        if self.config.output_dir.exists():
            shutil.rmtree(self.config.output_dir)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_content(self):
        """Parse all content files."""
        log.info(
            "parse_content",
            extra={"ssg_extra": {"content_dir": str(self.config.content_dir)}},
        )
        self.parsed_content = self.parser.parse_directory(
            self.config.content_dir, include_drafts=self.config.build_drafts
        )
        log.info(
            "content_found",
            extra={"ssg_extra": {"count": len(self.parsed_content)}},
        )

    def build_single_page(self, content: ParsedContent, output_path: Path):
        """
        Build a single content page.

        Args:
            content: Content to build
            output_path: Output file path
        """
        # Track template dependency
        template_path = self.config.template_dir / content.layout
        self.dependency_graph.add_content_dependency(content.source_path, template_path)
        self._record_template_chain(template_path)

        # Render content
        html = self.renderer.render_content(content)
        html = self.asset_processor.rewrite_asset_urls(html, page_depth=1)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    def _record_template_chain(self, template_path: Path) -> None:
        """Record {% extends %} parents so base-template edits rebuild child pages."""
        current = template_path
        seen: Set[Path] = set()
        while current.exists() and current not in seen:
            seen.add(current)
            text = current.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"""\{%\s*extends\s+["']([^"']+)["']""", text)
            if not match:
                break
            parent = self.config.template_dir / match.group(1)
            self.dependency_graph.add_template_include(current, parent)
            current = parent

    def build_content_pages(self):
        """Build individual content pages."""
        log.info(
            "build_content_pages",
            extra={"ssg_extra": {"count": len(self.parsed_content)}},
        )

        for content in self.parsed_content:
            # Determine output path
            output_path = self.config.output_dir / content.slug / "index.html"
            self.build_single_page(content, output_path)

        log.info(
            "pages_built",
            extra={"ssg_extra": {"count": len(self.parsed_content)}},
        )

    def build_index_pages(self):
        """Build index and paginated list pages."""
        log.info("build_index_pages")

        if not self.parsed_content:
            log.info("no_index_content")
            return

        paginator = Paginator(self.parsed_content, self.config.posts_per_page)

        log.info(
            "paginated_pages",
            extra={"ssg_extra": {"pages": paginator.total_pages}},
        )

        for page_num in range(1, paginator.total_pages + 1):
            items = paginator.page(page_num)

            # Determine output path
            if page_num == 1:
                output_path = self.config.output_dir / "index.html"
            else:
                output_path = self.config.output_dir / "page" / str(page_num) / "index.html"

            # Render index page
            context = {
                "page_num": page_num,
                "total_pages": paginator.total_pages,
                "has_prev": paginator.has_prev(page_num),
                "has_next": paginator.has_next(page_num),
                "prev_url": f"/page/{page_num - 1}/" if page_num > 2 else "/",
                "next_url": f"/page/{page_num + 1}/" if paginator.has_next(page_num) else None,
            }

            html = self.renderer.render_list("index.html", items, context)

            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

    def build_tag_pages(self):
        """Build tag archive pages."""
        log.info("build_tag_pages")

        # Group content by tag
        tags: Dict[str, List[ParsedContent]] = defaultdict(list)
        for content in self.parsed_content:
            for tag in content.tags:
                tags[tag].append(content)

        log.info("tags_found", extra={"ssg_extra": {"count": len(tags)}})

        # Build page for each tag
        for tag, items in tags.items():
            output_path = self.config.output_dir / "tags" / tag / "index.html"

            context = {"tag": tag}
            html = self.renderer.render_list("tag.html", items, context)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

    def build_assets(self):
        """Process and copy assets."""
        log.info("processing_assets")
        self.asset_processor.process()

    def build_feed(self):
        """Generate RSS feed."""
        if not self.config.feed_enabled:
            log.info("feed_disabled")
            return

        log.info("generating_feed")
        self.feed_generator.generate(self.parsed_content)

    def build_sitemap(self):
        """Generate XML sitemap."""
        if not self.config.sitemap_enabled:
            log.info("sitemap_disabled")
            return

        log.info("generating_sitemap")
        self.sitemap_generator.generate(self.parsed_content)

    def build(self, clean: bool = True):
        """
        Execute full site build.

        Args:
            clean: Whether to clean output directory first
        """
        log.info("build_start")

        if clean:
            self.clean()

        # Parse all content
        self.parse_content()

        # Build pages
        self.build_content_pages()
        self.build_index_pages()
        self.build_tag_pages()

        # Process assets
        self.build_assets()

        # Generate feed and sitemap
        self.build_feed()
        self.build_sitemap()

        log.info(
            "build_complete",
            extra={"ssg_extra": {"output_dir": str(self.config.output_dir)}},
        )

    def rebuild_changed(self, changed_files: List[Path]):
        """Rebuild content files affected by content or template changes."""
        content_to_rebuild = set()

        for changed_file in changed_files:
            # Check if it's a content file
            if changed_file.suffix in [".md", ".markdown"]:
                content_to_rebuild.add(changed_file)

            elif changed_file.suffix in [".html", ".jinja2", ".j2"]:
                affected = self.dependency_graph.get_affected_content(changed_file)
                content_to_rebuild.update(affected)

        if content_to_rebuild:
            log.info(
                "rebuild_changed",
                extra={"ssg_extra": {"count": len(content_to_rebuild)}},
            )
            # Rebuild affected content
            for content_path in content_to_rebuild:
                try:
                    content = self.parser.parse_file(content_path)
                    output_path = self.config.output_dir / content.slug / "index.html"
                    self.build_single_page(content, output_path)
                except Exception as e:
                    log.error(
                        "rebuild_error",
                        extra={"ssg_extra": {"path": str(content_path), "error": str(e)}},
                    )
