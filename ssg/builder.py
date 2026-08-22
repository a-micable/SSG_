"""
Site builder that orchestrates parsing, rendering, and asset processing.
Handles incremental builds and dependency tracking.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Optional
import shutil
from .config import SiteConfig
from .parser import MarkdownParser, ParsedContent
from .renderer import Renderer
from .assets import AssetProcessor
from .feed import FeedGenerator
from .sitemap import SitemapGenerator


class BuildError(Exception):
    """Raised when build process fails."""

    pass


class DependencyGraph:
    """
    Tracks dependencies between content, templates, and outputs.

    BUG 2 LOCATION: Cache invalidation doesn't properly handle template changes.
    When a template changes, dependent pages aren't always rebuilt.
    """

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
        """
        Get all content that needs rebuilding when a template changes.

        BUG 2: This doesn't recursively check template includes properly.
        When base.html changes, only direct dependents rebuild, not transitive ones.

        Example:
            base.html (changed)
            └── post.html (includes base.html)
                └── article.md (uses post.html)

        Expected: article.md rebuilds
        Actual: article.md doesn't rebuild (BUG!)
        """
        affected = set(self.template_to_content.get(changed_template, set()))

        # BUG 2: Missing recursive check for template inheritance
        # Should also check templates that include the changed template
        # This causes stale output when base templates change

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
        print(f"Parsing content from {self.config.content_dir}...")
        self.parsed_content = self.parser.parse_directory(
            self.config.content_dir, include_drafts=self.config.build_drafts
        )
        print(f"  Found {len(self.parsed_content)} content files")

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

        # Render content
        html = self.renderer.render_content(content)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    def build_content_pages(self):
        """Build individual content pages."""
        print(f"Building {len(self.parsed_content)} pages...")

        for content in self.parsed_content:
            # Determine output path
            output_path = self.config.output_dir / content.slug / "index.html"
            self.build_single_page(content, output_path)

        print(f"  Built {len(self.parsed_content)} pages")

    def build_index_pages(self):
        """Build index and paginated list pages."""
        print("Building index pages...")

        if not self.parsed_content:
            print("  No content to index")
            return

        paginator = Paginator(self.parsed_content, self.config.posts_per_page)

        print(f"  Creating {paginator.total_pages} paginated pages")

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
        print("Building tag pages...")

        # Group content by tag
        tags: Dict[str, List[ParsedContent]] = defaultdict(list)
        for content in self.parsed_content:
            for tag in content.tags:
                tags[tag].append(content)

        print(f"  Found {len(tags)} tags")

        # Build page for each tag
        for tag, items in tags.items():
            output_path = self.config.output_dir / "tags" / tag / "index.html"

            context = {"tag": tag}
            html = self.renderer.render_list("tag.html", items, context)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

    def build_assets(self):
        """Process and copy assets."""
        print("Processing assets...")
        self.asset_processor.process()

    def build_feed(self):
        """Generate RSS feed."""
        if not self.config.feed_enabled:
            print("Feed generation disabled")
            return

        print("Generating RSS feed...")
        self.feed_generator.generate(self.parsed_content)

    def build_sitemap(self):
        """Generate XML sitemap."""
        if not self.config.sitemap_enabled:
            print("Sitemap generation disabled")
            return

        print("Generating sitemap...")
        self.sitemap_generator.generate(self.parsed_content)

    def build(self, clean: bool = True):
        """
        Execute full site build.

        Args:
            clean: Whether to clean output directory first
        """
        print("=" * 70)
        print("Starting site build")
        print("=" * 70)

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

        print("=" * 70)
        print(f"Build complete! Output: {self.config.output_dir}")
        print("=" * 70)

    def rebuild_changed(self, changed_files: List[Path]):
        """
        Rebuild only files affected by changes.

        BUG 2 IMPACT: Template changes may not trigger all necessary rebuilds.

        Args:
            changed_files: List of changed file paths
        """
        content_to_rebuild = set()

        for changed_file in changed_files:
            # Check if it's a content file
            if changed_file.suffix in [".md", ".markdown"]:
                content_to_rebuild.add(changed_file)

            # Check if it's a template (BUG 2: Incomplete dependency tracking)
            elif changed_file.suffix in [".html", ".jinja2", ".j2"]:
                affected = self.dependency_graph.get_affected_content(changed_file)
                content_to_rebuild.update(affected)

        if content_to_rebuild:
            print(f"Rebuilding {len(content_to_rebuild)} affected files...")
            # Rebuild affected content
            for content_path in content_to_rebuild:
                try:
                    content = self.parser.parse_file(content_path)
                    output_path = self.config.output_dir / content.slug / "index.html"
                    self.build_single_page(content, output_path)
                except Exception as e:
                    print(f"  Error rebuilding {content_path}: {e}")
