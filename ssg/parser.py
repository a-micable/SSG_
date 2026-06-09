"""
Content parsing for Markdown files with frontmatter.
Handles extraction of metadata and conversion to HTML.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import frontmatter
import markdown
from markdown.extensions import tables, fenced_code, codehilite


class ParseError(Exception):
    """Raised when content parsing fails."""
    pass


@dataclass
class ParsedContent:
    """
    Represents a parsed content file.
    
    Attributes:
        source_path: Original file path
        title: Content title from frontmatter
        content: Rendered HTML content
        raw_content: Original Markdown content
        date: Publication date (BUG 1: stored as string instead of datetime)
        slug: URL slug
        layout: Template layout to use
        tags: List of tags
        draft: Whether content is a draft
        metadata: All frontmatter metadata
    """
    source_path: Path
    title: str
    content: str
    raw_content: str
    date: str  # BUG 1: Should be datetime, but stored as string
    slug: str
    layout: str = "default.html"
    tags: List[str] = field(default_factory=list)
    draft: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def url(self) -> str:
        """Generate URL path for this content."""
        if self.slug:
            return f"/{self.slug}/"
        return f"/{self.source_path.stem}/"
    
    @property
    def is_draft(self) -> bool:
        """Check if content is a draft."""
        return self.draft


class MarkdownParser:
    """
    Parses Markdown files with YAML frontmatter.
    
    BUG 1 LOCATION: Date parsing stores dates as strings instead of datetime objects.
    This causes template rendering errors when using date filters like strftime.
    
    Example error:
        {{ post.date | strftime('%B %d') }}
        TypeError: descriptor 'strftime' for 'datetime.date' objects doesn't apply to 'str'
    """
    
    def __init__(self):
        """Initialize the Markdown parser with extensions."""
        self.md = markdown.Markdown(
            extensions=[
                'extra',
                'meta',
                'tables',
                'fenced_code',
                'codehilite',
                'toc',
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                }
            }
        )
    
    def parse_file(self, file_path: Path) -> ParsedContent:
        """
        Parse a Markdown file with frontmatter.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            ParsedContent object with metadata and rendered HTML
            
        Raises:
            ParseError: If file cannot be read or parsed
        """
        if not file_path.exists():
            raise ParseError(f"File not found: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
        except Exception as e:
            raise ParseError(f"Failed to read {file_path}: {e}")
        
        # Extract frontmatter
        metadata = dict(post.metadata)
        raw_content = post.content
        
        # Required fields
        title = metadata.get("title")
        if not title:
            raise ParseError(f"Missing required field 'title' in {file_path}")
        
        # BUG 1: Date is stored as string instead of datetime
        # This causes issues when templates try to format dates
        date = metadata.get("date", "")
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")  # Convert to string (BUG!)
        elif not date:
            # Use file modification time as fallback
            date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
        
        # Optional fields
        slug = metadata.get("slug", file_path.stem)
        layout = metadata.get("layout", "post.html")
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        draft = metadata.get("draft", False)
        
        # Render Markdown to HTML
        try:
            html_content = self.md.convert(raw_content)
            self.md.reset()  # Reset parser state for next file
        except Exception as e:
            raise ParseError(f"Failed to render Markdown in {file_path}: {e}")
        
        return ParsedContent(
            source_path=file_path,
            title=title,
            content=html_content,
            raw_content=raw_content,
            date=date,  # BUG 1: String instead of datetime
            slug=slug,
            layout=layout,
            tags=tags,
            draft=draft,
            metadata=metadata,
        )
    
    def parse_directory(
        self, 
        content_dir: Path, 
        include_drafts: bool = False
    ) -> List[ParsedContent]:
        """
        Parse all Markdown files in a directory.
        
        Args:
            content_dir: Directory containing Markdown files
            include_drafts: Whether to include draft content
            
        Returns:
            List of ParsedContent objects
        """
        if not content_dir.exists():
            raise ParseError(f"Content directory not found: {content_dir}")
        
        parsed_items = []
        
        # Find all Markdown files
        for pattern in ["**/*.md", "**/*.markdown"]:
            for file_path in content_dir.glob(pattern):
                if file_path.is_file():
                    try:
                        parsed = self.parse_file(file_path)
                        
                        # Skip drafts unless explicitly included
                        if parsed.is_draft and not include_drafts:
                            continue
                        
                        parsed_items.append(parsed)
                    except ParseError as e:
                        print(f"Warning: {e}")
                        continue
        
        # Sort by date (newest first)
        # BUG 1 IMPACT: String comparison instead of datetime comparison
        # Works for ISO format dates but fails for other formats
        parsed_items.sort(key=lambda x: x.date, reverse=True)
        
        return parsed_items


def extract_excerpt(content: str, length: int = 200) -> str:
    """
    Extract an excerpt from HTML content.
    
    Args:
        content: HTML content
        length: Maximum length of excerpt
        
    Returns:
        Plain text excerpt
    """
    # Strip HTML tags (simple approach)
    import re
    text = re.sub(r'<[^>]+>', '', content)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= length:
        return text
    
    # Truncate at word boundary
    excerpt = text[:length].rsplit(' ', 1)[0]
    return excerpt + "..."
