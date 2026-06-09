"""
Tests for the Markdown parser.
"""

import pytest
from pathlib import Path
from ssg.parser import MarkdownParser, ParsedContent, ParseError, extract_excerpt


class TestMarkdownParser:
    """Test cases for MarkdownParser."""
    
    def test_parse_file_basic(self, temp_dir):
        """Test parsing a basic Markdown file with frontmatter."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
title: Test Post
date: 2024-03-15
slug: test-post
tags:
  - testing
  - python
---

# Hello World

This is **bold** and this is *italic*.
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        assert isinstance(result, ParsedContent)
        assert result.title == "Test Post"
        assert result.date == "2024-03-15"
        assert result.slug == "test-post"
        assert result.tags == ["testing", "python"]
        assert "<h1>Hello World</h1>" in result.content
        assert "<strong>bold</strong>" in result.content
        assert "<em>italic</em>" in result.content
    
    def test_parse_file_missing_title(self, temp_dir):
        """Test that missing title raises ParseError."""
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
date: 2024-03-15
---

Content without title.
""")
        
        parser = MarkdownParser()
        with pytest.raises(ParseError, match="Missing required field 'title'"):
            parser.parse_file(test_file)
    
    def test_parse_file_default_slug(self, temp_dir):
        """Test that slug defaults to filename stem."""
        test_file = temp_dir / "my-awesome-post.md"
        test_file.write_text("""---
title: My Post
---

Content.
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        assert result.slug == "my-awesome-post"
    
    def test_parse_file_draft_flag(self, temp_dir):
        """Test parsing draft flag."""
        test_file = temp_dir / "draft.md"
        test_file.write_text("""---
title: Draft Post
draft: true
---

Draft content.
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        assert result.draft is True
        assert result.is_draft is True
    
    def test_parse_file_tags_as_string(self, temp_dir):
        """Test parsing tags as comma-separated string."""
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
title: Test Post
tags: python, web, testing
---

Content.
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        assert result.tags == ["python", "web", "testing"]
    
    def test_parse_file_not_found(self, temp_dir):
        """Test parsing non-existent file raises error."""
        parser = MarkdownParser()
        with pytest.raises(ParseError, match="File not found"):
            parser.parse_file(temp_dir / "nonexistent.md")
    
    def test_parse_directory(self, sample_site):
        """Test parsing all files in a directory."""
        parser = MarkdownParser()
        results = parser.parse_directory(sample_site['content'])
        
        # Should find 2 non-draft posts
        assert len(results) == 2
        assert all(isinstance(r, ParsedContent) for r in results)
        
        # Should be sorted by date (newest first)
        dates = [r.date for r in results]
        assert dates == sorted(dates, reverse=True)
    
    def test_parse_directory_include_drafts(self, sample_site):
        """Test parsing directory with drafts included."""
        parser = MarkdownParser()
        results = parser.parse_directory(sample_site['content'], include_drafts=True)
        
        # Should find 3 posts including draft
        assert len(results) == 3
        
        # Check that draft is included
        drafts = [r for r in results if r.is_draft]
        assert len(drafts) == 1
    
    def test_url_property(self, temp_dir):
        """Test URL generation from slug."""
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
title: Test Post
slug: my-awesome-post
---

Content.
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        assert result.url == "/my-awesome-post/"
    
    def test_markdown_extensions(self, temp_dir):
        """Test that Markdown extensions work correctly."""
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
title: Test Post
---

## Code Block

```python
def hello():
    print("world")
```

## Table

| Column 1 | Column 2 |
|----------|----------|
| A        | B        |
""")
        
        parser = MarkdownParser()
        result = parser.parse_file(test_file)
        
        # Check code block rendering
        assert "<code" in result.content
        assert "python" in result.content.lower()
        
        # Check table rendering
        assert "<table>" in result.content
        assert "<th>Column 1</th>" in result.content


class TestExtractExcerpt:
    """Test cases for excerpt extraction."""
    
    def test_extract_excerpt_short_content(self):
        """Test excerpt of content shorter than limit."""
        content = "<p>This is short content.</p>"
        excerpt = extract_excerpt(content, length=100)
        
        assert excerpt == "This is short content."
        assert "..." not in excerpt
    
    def test_extract_excerpt_long_content(self):
        """Test excerpt of content longer than limit."""
        content = "<p>" + ("word " * 100) + "</p>"
        excerpt = extract_excerpt(content, length=50)
        
        assert len(excerpt) <= 54  # 50 + "..."
        assert excerpt.endswith("...")
    
    def test_extract_excerpt_strips_html(self):
        """Test that HTML tags are stripped."""
        content = "<p>This is <strong>bold</strong> and <em>italic</em>.</p>"
        excerpt = extract_excerpt(content)
        
        assert "<strong>" not in excerpt
        assert "<em>" not in excerpt
        assert "bold" in excerpt
        assert "italic" in excerpt
