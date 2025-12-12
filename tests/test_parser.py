"""Tests for content parsing."""

from pathlib import Path

import pytest

from ssg import ParsingError
from ssg.parser import ContentParser, discover_content


def test_parse_markdown_with_frontmatter(sample_markdown_file: Path, temp_dir: Path):
    """Test parsing a Markdown file with frontmatter."""
    parser = ContentParser()
    parsed = parser.parse_file(sample_markdown_file, temp_dir)
    
    assert parsed.metadata.title == "Test Post"
    assert parsed.metadata.date == "2024-03-15"  # BUG 1: stored as string
    assert parsed.metadata.tags == ["python", "testing"]
    assert parsed.metadata.author == "Test Author"
    assert parsed.metadata.layout == "post.html"
    assert "<h1>Test Content</h1>" in parsed.html
    assert "<strong>bold</strong>" in parsed.html
    assert "<em>italic</em>" in parsed.html


def test_parse_missing_title(temp_dir: Path):
    """Test that missing title raises error."""
    content = """---
date: 2024-03-15
---

Content without title.
"""
    
    file_path = temp_dir / "no_title.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    
    with pytest.raises(ParsingError, match="Missing required 'title'"):
        parser.parse_file(file_path, temp_dir)


def test_parse_missing_file():
    """Test that parsing non-existent file raises error."""
    parser = ContentParser()
    
    with pytest.raises(ParsingError, match="not found"):
        parser.parse_file(Path("nonexistent.md"), Path("."))


def test_parse_url_path_generation(temp_dir: Path):
    """Test URL path generation from file paths."""
    parser = ContentParser()
    
    # Test simple file
    content = """---
title: Simple Post
---
Content"""
    
    file_path = temp_dir / "simple.md"
    file_path.write_text(content)
    
    parsed = parser.parse_file(file_path, temp_dir)
    assert parsed.url_path == "/simple/"
    
    # Test nested file
    nested_dir = temp_dir / "blog"
    nested_dir.mkdir()
    nested_file = nested_dir / "post.md"
    nested_file.write_text(content)
    
    parsed = parser.parse_file(nested_file, temp_dir)
    assert parsed.url_path == "/blog/post/"


def test_parse_custom_slug(temp_dir: Path):
    """Test that custom slug overrides default URL path."""
    content = """---
title: My Post
slug: custom-url
---
Content"""
    
    file_path = temp_dir / "original.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    assert parsed.url_path == "/custom-url/"


def test_parse_index_file(temp_dir: Path):
    """Test that index.md maps to directory URL."""
    content = """---
title: Index Page
---
Content"""
    
    file_path = temp_dir / "index.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    assert parsed.url_path == "/"


def test_parse_tags_as_string(temp_dir: Path):
    """Test parsing comma-separated tags string."""
    content = """---
title: Post
tags: python, testing, web
---
Content"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    assert parsed.metadata.tags == ["python", "testing", "web"]


def test_parse_draft_flag(temp_dir: Path):
    """Test parsing draft flag."""
    content = """---
title: Draft Post
draft: true
---
Content"""
    
    file_path = temp_dir / "draft.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    assert parsed.metadata.draft is True


def test_parse_custom_metadata(temp_dir: Path):
    """Test that custom metadata is preserved."""
    content = """---
title: Post
custom_field: custom_value
another: 123
---
Content"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    assert parsed.metadata.custom["custom_field"] == "custom_value"
    assert parsed.metadata.custom["another"] == 123


def test_discover_content(temp_dir: Path):
    """Test content file discovery."""
    content_dir = temp_dir / "content"
    content_dir.mkdir()
    
    # Create some content files
    (content_dir / "post1.md").write_text("---\ntitle: Post 1\n---\n")
    (content_dir / "post2.md").write_text("---\ntitle: Post 2\n---\n")
    
    # Create nested content
    nested = content_dir / "blog"
    nested.mkdir()
    (nested / "nested.md").write_text("---\ntitle: Nested\n---\n")
    
    # Create a file to ignore (starts with _)
    (content_dir / "_draft.md").write_text("---\ntitle: Draft\n---\n")
    
    files = discover_content(content_dir)
    
    assert len(files) == 3
    assert content_dir / "post1.md" in files
    assert content_dir / "post2.md" in files
    assert nested / "nested.md" in files
    assert content_dir / "_draft.md" not in files


def test_discover_content_empty_directory(temp_dir: Path):
    """Test discovering content in empty directory."""
    content_dir = temp_dir / "empty"
    content_dir.mkdir()
    
    files = discover_content(content_dir)
    assert len(files) == 0


def test_discover_content_nonexistent_directory(temp_dir: Path):
    """Test discovering content in non-existent directory."""
    files = discover_content(temp_dir / "nonexistent")
    assert len(files) == 0


def test_parse_markdown_extensions(temp_dir: Path):
    """Test that Markdown extensions are properly rendered."""
    content = """---
title: Test
---

# Heading

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

~~strikethrough~~
"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    parsed = parser.parse_file(file_path, temp_dir)
    
    # Check table rendering
    assert "<table>" in parsed.html
    assert "<th>Header 1</th>" in parsed.html
