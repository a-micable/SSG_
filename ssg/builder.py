"""
Site builder orchestration for SSG.

Coordinates parsing, rendering, asset processing, and output generation.
Implements incremental builds with dependency tracking.
"""

import logging
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ssg import BuildError
from ssg.assets import AssetProcessor
from ssg.config import SiteConfig
from ssg.feed import FeedGenerator
from ssg.parser import ContentParser, ParsedContent, discover_content
from ssg.renderer import TemplateRenderer
from ssg.sitemap import SitemapGenerator

logger = logging.getLogger(__name__)


class DependencyGraph:
    """
    Tracks dependencies between content, templates, and assets.
    
    Used for incremental builds (BUG 2 location - cache invalidation).
    """

    def __init__(self) -> None:
        """Initialize empty dependency graph."""
        self.content_to_templates: Dict[Path, Set[Path]] = defaultdict(set)
        self.template_to_content: Dict[Path, Set[Path]] = defaultdict(set)
        self.template_to_templates: Dict[Path, Set[Path]] = defaultdict(set)

    def add_content_template_dependency(
        self, content_path: Path, template_path: Path
    ) -> None:
        """Record that content depends on a template."""
        self.content_to_templates[content_path].add(template_path)
        self.template_to_content[template_path].add(content_path)

    def add_template_dependency(self, template: Path, depends_on: Path) -> None:
        """Record that a template depends on another template (extends/include)."""
        self.template_to_templates[template].add(depends_on)

    def get_affected_content(self, changed_template: Path) -> Set[Path]:
        """
        Get all content files affected by a template change.
        
        BUG 2: This may not properly traverse template inheritance chains,
        causing some content to not rebuild when base templates change.
        """
        affected = set()
        
        # Direct dependencies
        affected.update(self.template_to_content.get(changed_template, set()))
        
        # BUG 2: Template inheritance traversal might be incomplete
        # If base.html changes, we need to find all templates that extend it
        # and then all content using those templates
        # Current implementation only checks direct dependencies
        
        return affected

    def clear(self) -> None:
        """Clear all dependency tracking."""
        self.content_to_templates.clear()
        self.template_to_content.clear()
        self.template_to_templates.clear()


class SiteBuilder:
    """
    Main site builder that orchestrates the build process.
    
    Coordinates:
    - Content discovery and parsing
    - Template rendering
    - Asset processing
    - Collection generation (tags, archives)
    - Pagination
    - Feed and sitemap generation
    - Incremental builds
    """

    def __init__(self, config: SiteConfig) -> None:
        """
        Initialize the site builder.
        
        Args:
            config: Site configuration
        """
        self.config = config
        self.parser = ContentParser()
        self.renderer = TemplateRenderer(config)
        self.asset_processor = AssetProcessor(config)
        self.feed_generator = FeedGenerator(config)
        self.sitemap_generator = SitemapGenerator(config)
        self.dependency_graph = DependencyGraph()
        
        self.all_content: List[ParsedContent] = []
        self.collections: Dict[str, Any] = {}

    def build(self, clean: bool = True, fingerprint_assets: bool = True) -> None:
        """
        Build the entire site.
        
        Args:
            clean: Whether to clean output directory before building
            fingerprint_assets: Whether to fingerprint assets for cache busting
            
        Raises:
            BuildError: If build fails
        """
        logger.info("Starting site build")
        start_time = datetime.now()

        # Clean output directory if requested
        if clean and self.config.output_dir.exists():
            logger.info(f"Cleaning output directory: {self.config.output_dir}")
            shutil.rmtree(self.config.output_dir)

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Parse all content
            self._parse_all_content()

            # Step 2: Build collections (tags, archives)
            self._build_collections()

            # Step 3: Render all content
            self._render_all_content()

            # Step 4: Generate paginated pages
            self._generate_pagination()

            # Step 5: Process assets
            asset_dir = self.config.content_dir.parent / "assets"
            self.asset_processor.process_assets(asset_dir, fingerprint=fingerprint_assets)

            # Step 6: Rewrite asset URLs in all HTML files
            if fingerprint_assets:
                self._rewrite_all_asset_urls()

            # Step 7: Generate RSS feed
            self._generate_feed()

            # Step 8: Generate sitemap
            self._generate_sitemap()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Build completed successfully in {elapsed:.2f}s")
            logger.info(f"  - {len(self.all_content)} pages")
            logger.info(f"  - Output: {self.config.output_dir}")

        except Exception as e:
            logger.error(f"Build failed: {e}")
            raise BuildError(f"Site build failed: {e}")

    def _parse_all_content(self) -> None:
        """Parse all content files."""
        logger.info("Parsing content files")
        
        content_files = discover_content(self.config.content_dir)
        self.all_content = []

        for content_file in content_files:
            try:
                parsed = self.parser.parse_file(content_file, self.config.content_dir)
                
                # Skip drafts in production builds
                if not parsed.metadata.draft:
                    self.all_content.append(parsed)
                    
                    # Track template dependency
                    template_path = self.config.template_dir / parsed.metadata.layout
                    self.dependency_graph.add_content_template_dependency(
                        content_file, template_path
                    )
            except Exception as e:
                logger.error(f"Failed to parse {content_file}: {e}")
                raise

        logger.info(f"Parsed {len(self.all_content)} content files")

    def _build_collections(self) -> None:
        """Build tag and date-based collections."""
        logger.info("Building collections")
        
        # Build tag collections
        tags: Dict[str, List[ParsedContent]] = defaultdict(list)
        for content in self.all_content:
            for tag in content.metadata.tags:
                tags[tag].append(content)

        # Build date archives (by year and month)
        archives: Dict[str, List[ParsedContent]] = defaultdict(list)
        for content in self.all_content:
            if content.metadata.date:
                # Parse date string to extract year
                # This works around BUG 1 by parsing the string
                try:
                    if isinstance(content.metadata.date, str):
                        date_str = content.metadata.date
                        # Simple year extraction
                        year = date_str.split("-")[0] if "-" in date_str else None
                        if year:
                            archives[year].append(content)
                except Exception as e:
                    logger.warning(f"Failed to extract year from date: {e}")

        # Sort collections by date (newest first)
        for tag_content in tags.values():
            tag_content.sort(key=lambda c: c.metadata.date or "", reverse=True)
        
        for archive_content in archives.values():
            archive_content.sort(key=lambda c: c.metadata.date or "", reverse=True)

        self.collections = {
            "tags": dict(tags),
            "archives": dict(archives),
            "all_posts": sorted(
                self.all_content, 
                key=lambda c: c.metadata.date or "", 
                reverse=True
            ),
        }

        logger.info(f"Built collections: {len(tags)} tags, {len(archives)} archives")

    def _render_all_content(self) -> None:
        """Render all content files to HTML."""
        logger.info("Rendering content")

        site_context = {
            "collections": self.collections,
        }

        for content in self.all_content:
            try:
                html = self.renderer.render_content(content, site_context)
                
                # Write to output
                output_path = self._get_output_path(content.url_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
                
                logger.debug(f"Rendered: {content.source_path} -> {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to render {content.source_path}: {e}")
                raise

    def _generate_pagination(self) -> None:
        """
        Generate paginated index pages.
        
        BUG 3: Off-by-one error when total_posts % posts_per_page == 0
        Creates an extra empty page.
        """
        logger.info("Generating pagination")

        all_posts = self.collections.get("all_posts", [])
        if not all_posts:
            return

        posts_per_page = self.config.posts_per_page
        total_posts = len(all_posts)
        
        # BUG 3: This calculation is incorrect
        # When total_posts is exactly divisible by posts_per_page,
        # this creates an extra page
        # Example: 20 posts, 10 per page -> should be 2 pages, but creates 3
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page
        
        # However, range will create one extra iteration in some cases
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * posts_per_page
            end_idx = start_idx + posts_per_page
            page_posts = all_posts[start_idx:end_idx]
            
            # BUG 3: Should check if page_posts is empty and skip
            # but this implementation doesn't, creating empty final pages
            
            context = {
                "posts": page_posts,
                "page_num": page_num,
                "total_pages": total_pages,
                "has_prev": page_num > 1,
                "has_next": page_num < total_pages,
                "prev_url": f"/page/{page_num - 1}/" if page_num > 2 else "/",
                "next_url": f"/page/{page_num + 1}/" if page_num < total_pages else None,
                "site": {
                    "name": self.config.site_name,
                    "base_url": self.config.base_url,
                },
            }

            # Render page
            try:
                html = self.renderer.render_template("index.html", context)
                
                # Determine output path
                if page_num == 1:
                    output_path = self.config.output_dir / "index.html"
                else:
                    output_path = self.config.output_dir / "page" / str(page_num) / "index.html"
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
                
                logger.debug(f"Generated pagination page {page_num}/{total_pages}")
                
            except Exception as e:
                logger.warning(f"Failed to generate pagination page {page_num}: {e}")

    def _rewrite_all_asset_urls(self) -> None:
        """Rewrite asset URLs in all generated HTML files."""
        logger.info("Rewriting asset URLs")

        for html_file in self.config.output_dir.rglob("*.html"):
            try:
                # Calculate page depth for relative path resolution
                page_depth = len(html_file.relative_to(self.config.output_dir).parents) - 1
                
                with open(html_file, "r", encoding="utf-8") as f:
                    html = f.read()
                
                # Rewrite URLs (BUG 5 may manifest here for nested pages)
                rewritten = self.asset_processor.rewrite_asset_urls(html, page_depth)
                
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(rewritten)
                    
            except Exception as e:
                logger.warning(f"Failed to rewrite asset URLs in {html_file}: {e}")

    def _generate_feed(self) -> None:
        """Generate RSS feed."""
        logger.info("Generating RSS feed")
        
        try:
            feed_xml = self.feed_generator.generate(self.collections.get("all_posts", []))
            feed_path = self.config.output_dir / "rss.xml"
            
            with open(feed_path, "w", encoding="utf-8") as f:
                f.write(feed_xml)
            
            logger.info(f"Generated RSS feed: {feed_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate RSS feed: {e}")

    def _generate_sitemap(self) -> None:
        """Generate XML sitemap."""
        logger.info("Generating sitemap")
        
        try:
            sitemap_xml = self.sitemap_generator.generate(self.all_content)
            sitemap_path = self.config.output_dir / "sitemap.xml"
            
            with open(sitemap_path, "w", encoding="utf-8") as f:
                f.write(sitemap_xml)
            
            logger.info(f"Generated sitemap: {sitemap_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate sitemap: {e}")

    def _get_output_path(self, url_path: str) -> Path:
        """
        Convert a URL path to an output file path.
        
        Args:
            url_path: URL path like "/blog/post/"
            
        Returns:
            Path to output file
        """
        # Remove leading/trailing slashes
        clean_path = url_path.strip("/")
        
        if not clean_path:
            return self.config.output_dir / "index.html"
        
        # URL paths map to index.html files in directories
        return self.config.output_dir / clean_path / "index.html"

    def incremental_build(self, changed_files: Set[Path]) -> None:
        """
        Perform incremental build for changed files.
        
        BUG 2: Dependency graph may not properly invalidate all affected content.
        
        Args:
            changed_files: Set of file paths that changed
        """
        logger.info(f"Incremental build for {len(changed_files)} changed files")
        
        content_to_rebuild = set()
        
        for changed_file in changed_files:
            # Check if it's a content file
            if changed_file.suffix == ".md" and changed_file.is_relative_to(self.config.content_dir):
                content_to_rebuild.add(changed_file)
            
            # Check if it's a template file
            elif changed_file.suffix == ".html" and changed_file.is_relative_to(self.config.template_dir):
                # BUG 2: Find all content affected by this template
                affected = self.dependency_graph.get_affected_content(changed_file)
                content_to_rebuild.update(affected)
        
        # Rebuild affected content
        for content_file in content_to_rebuild:
            try:
                parsed = self.parser.parse_file(content_file, self.config.content_dir)
                html = self.renderer.render_content(parsed, {"collections": self.collections})
                
                output_path = self._get_output_path(parsed.url_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
                
                logger.debug(f"Rebuilt: {content_file}")
                
            except Exception as e:
                logger.error(f"Failed to rebuild {content_file}: {e}")

        logger.info(f"Incremental build completed: {len(content_to_rebuild)} files rebuilt")
