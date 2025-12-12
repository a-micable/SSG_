"""
Content parsing for SSG.

Handles parsing of Markdown files with YAML frontmatter, converting content
to HTML, and extracting metadata.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter
from markdown_it import MarkdownIt

from ssg import ParsingError

logger = logging.getLogger(__name__)


@dataclass
class ContentMetadata:
    """
    Structured metadata extracted from content frontmatter.
    
    Attributes:
        title: Content title
        date: Publication date (BUG 1: intentionally stored as string for historical bug)
        tags: List of tags
        slug: URL slug for the content
        layout: Template file to use for rendering
        author: Content author
        description: Content description
        draft: Whether content is a draft
        custom: Any additional custom metadata
    """

    title: str
    date: Optional[str] = None  # BUG 1: Should be datetime but stored as string
    tags: List[str] = None
    slug: Optional[str] = None
    layout: str = "default.html"
    author: Optional[str] = None
    description: Optional[str] = None
    draft: bool = False
    custom: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        if self.tags is None:
            self.tags = []
        if self.custom is None:
            self.custom = {}


@dataclass
class ParsedContent:
    """
    Represents fully parsed content with metadata and rendered HTML.
    
    Attributes:
        source_path: Original file path
        metadata: Structured metadata from frontmatter
        html: Rendered HTML content
        raw_markdown: Original Markdown content
        url_path: Generated URL path for this content
    """

    source_path: Path
    metadata: ContentMetadata
    html: str
    raw_markdown: str
    url_path: str


class ContentParser:
    """
    Parses Markdown content files with frontmatter support.
    
    This parser handles:
    - YAML frontmatter extraction
    - Markdown to HTML conversion
    - Metadata validation and typing
    - URL path generation
    """

    def __init__(self) -> None:
        """Initialize the parser with Markdown renderer."""
        self.md = MarkdownIt()
        # Enable common Markdown extensions
        self.md.enable(["table", "strikethrough"])

    def parse_file(self, file_path: Path, content_dir: Path) -> ParsedContent:
        """
        Parse a Markdown file with frontmatter.
        
        Args:
            file_path: Path to the Markdown file
            content_dir: Root content directory (for relative path calculation)
            
        Returns:
            ParsedContent instance with metadata and rendered HTML
            
        Raises:
            ParsingError: If file cannot be read or parsed
        """
        if not file_path.exists():
            raise ParsingError(f"Content file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
        except Exception as e:
            raise ParsingError(f"Failed to parse frontmatter in {file_path}: {e}")

        # Extract and validate metadata
        metadata = self._extract_metadata(post.metadata, file_path)

        # Render Markdown to HTML
        try:
            html = self.md.render(post.content)
        except Exception as e:
            raise ParsingError(f"Failed to render Markdown in {file_path}: {e}")

        # Generate URL path
        url_path = self._generate_url_path(file_path, content_dir, metadata.slug)

        parsed = ParsedContent(
            source_path=file_path,
            metadata=metadata,
            html=html,
            raw_markdown=post.content,
            url_path=url_path,
        )

        logger.debug(f"Parsed content: {file_path} -> {url_path}")
        return parsed

    def _extract_metadata(self, fm_data: Dict[str, Any], file_path: Path) -> ContentMetadata:
        """
        Extract and validate metadata from frontmatter.
        
        Args:
            fm_data: Raw frontmatter dictionary
            file_path: Source file path (for error messages)
            
        Returns:
            ContentMetadata instance
        """
        # Required field: title
        title = fm_data.get("title")
        if not title:
            raise ParsingError(f"Missing required 'title' field in {file_path}")

        # Parse date field
        # BUG 1: This is where the date parsing bug exists
        # Date is kept as string instead of being converted to datetime
        # This will cause issues in templates when trying to use date filters
        date_value = fm_data.get("date")
        if date_value:
            # Historical bug: date is stored as string, not converted to datetime
            # This causes template errors when using strftime filter
            date = str(date_value)
        else:
            date = None

        # Extract tags
        tags = fm_data.get("tags", [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",")]
        elif not isinstance(tags, list):
            tags = []

        # Extract other fields
        slug = fm_data.get("slug")
        layout = fm_data.get("layout", "default.html")
        author = fm_data.get("author")
        description = fm_data.get("description")
        draft = fm_data.get("draft", False)

        # Collect any custom metadata
        known_fields = {
            "title",
            "date",
            "tags",
            "slug",
            "layout",
            "author",
            "description",
            "draft",
        }
        custom = {k: v for k, v in fm_data.items() if k not in known_fields}

        return ContentMetadata(
            title=title,
            date=date,
            tags=tags,
            slug=slug,
            layout=layout,
            author=author,
            description=description,
            draft=draft,
            custom=custom,
        )

    def _generate_url_path(
        self, file_path: Path, content_dir: Path, slug: Optional[str]
    ) -> str:
        """
        Generate the URL path for content.
        
        Args:
            file_path: Source file path
            content_dir: Root content directory
            slug: Optional custom slug from frontmatter
            
        Returns:
            URL path string (e.g., "/blog/my-post/")
        """
        if slug:
            # Use custom slug from frontmatter
            return f"/{slug.strip('/')}/"

        # Generate from file path
        relative_path = file_path.relative_to(content_dir)
        
        # Remove .md extension and convert to URL path
        path_parts = list(relative_path.parts[:-1])  # Exclude filename
        filename = relative_path.stem  # Filename without extension

        # Special case: index files map to directory
        if filename != "index":
            path_parts.append(filename)

        if not path_parts:
            return "/"

        return "/" + "/".join(path_parts) + "/"


def discover_content(content_dir: Path, exclude_drafts: bool = True) -> List[Path]:
    """
    Discover all Markdown content files in a directory tree.
    
    Args:
        content_dir: Root content directory to search
        exclude_drafts: Whether to exclude draft files
        
    Returns:
        List of Path objects for Markdown files
    """
    if not content_dir.exists():
        logger.warning(f"Content directory does not exist: {content_dir}")
        return []

    markdown_files = []
    
    for md_file in content_dir.rglob("*.md"):
        if md_file.is_file():
            # Skip files starting with underscore (private/partial files)
            if md_file.name.startswith("_"):
                continue
            markdown_files.append(md_file)

    logger.info(f"Discovered {len(markdown_files)} content files in {content_dir}")
    return sorted(markdown_files)
