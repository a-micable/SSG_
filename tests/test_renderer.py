"""
Tests for the template renderer.
"""

import pytest
from datetime import datetime
from pathlib import Path
from ssg.renderer import Renderer, RenderError
from ssg.parser import ParsedContent


class TestRenderer:
    """Test cases for Renderer."""

    def test_render_basic_template(self, sample_config):
        """Test rendering a basic template."""
        renderer = Renderer(sample_config)

        html = renderer.render("base.html", {"title": "Test Page"})

        assert "<title>Test Page</title>" in html
        assert "<html>" in html

    def test_render_template_with_site_context(self, sample_config):
        """Test that site context is automatically added."""
        renderer = Renderer(sample_config)

        html = renderer.render("base.html", {})

        # Site name should be available
        assert "Test Site" in html

    def test_render_template_not_found(self, sample_config):
        """Test that missing template raises RenderError."""
        renderer = Renderer(sample_config)

        with pytest.raises(RenderError, match="Template not found"):
            renderer.render("nonexistent.html", {})

    def test_render_content(self, sample_config, temp_dir):
        """Test rendering parsed content."""
        # Create parsed content
        content = ParsedContent(
            source_path=temp_dir / "test.md",
            title="Test Post",
            content="<p>Test content</p>",
            raw_content="Test content",
            date="2024-03-15",
            slug="test-post",
            layout="post.html",
            tags=["testing"],
        )

        renderer = Renderer(sample_config)
        html = renderer.render_content(content)

        assert "<h1>Test Post</h1>" in html
        assert "<p>Test content</p>" in html
        assert "<time>2024-03-15</time>" in html

    def test_render_list(self, sample_config, temp_dir):
        """Test rendering a list of content items."""
        items = [
            ParsedContent(
                source_path=temp_dir / "post1.md",
                title="Post 1",
                content="<p>Content 1</p>",
                raw_content="Content 1",
                date="2024-03-15",
                slug="post-1",
            ),
            ParsedContent(
                source_path=temp_dir / "post2.md",
                title="Post 2",
                content="<p>Content 2</p>",
                raw_content="Content 2",
                date="2024-03-14",
                slug="post-2",
            ),
        ]

        renderer = Renderer(sample_config)
        html = renderer.render_list("index.html", items)

        assert "Post 1" in html
        assert "Post 2" in html

    def test_strftime_filter(self, sample_config):
        """Test the strftime custom filter."""
        renderer = Renderer(sample_config)

        # Test with string date (BUG 1: parser stores dates as strings)
        result = renderer._filter_strftime("2024-03-15", "%B %d, %Y")
        assert result == "March 15, 2024"

    def test_strftime_filter_with_datetime(self, sample_config):
        """Test strftime filter with datetime object."""
        renderer = Renderer(sample_config)

        date_obj = datetime(2024, 3, 15)
        result = renderer._filter_strftime(date_obj, "%B %d, %Y")
        assert result == "March 15, 2024"

    def test_strftime_filter_invalid_date(self, sample_config):
        """Test strftime filter with invalid date string."""
        renderer = Renderer(sample_config)

        # Should return as-is if can't parse
        result = renderer._filter_strftime("invalid-date", "%B %d, %Y")
        assert result == "invalid-date"

    def test_dateformat_filter(self, sample_config):
        """Test the dateformat filter."""
        renderer = Renderer(sample_config)

        result = renderer._filter_dateformat("2024-03-15")
        assert isinstance(result, str)

    def test_excerpt_filter(self, sample_config):
        """Test the excerpt filter."""
        renderer = Renderer(sample_config)

        text = "This is a long text. " * 50
        result = renderer._filter_excerpt(text, length=50)

        assert len(result) <= 54  # 50 + "..."
        assert result.endswith("...")

    def test_excerpt_filter_short_text(self, sample_config):
        """Test excerpt filter with short text."""
        renderer = Renderer(sample_config)

        text = "Short text"
        result = renderer._filter_excerpt(text, length=50)

        assert result == "Short text"
        assert "..." not in result

    def test_limit_filter(self, sample_config):
        """Test the limit filter."""
        renderer = Renderer(sample_config)

        items = [1, 2, 3, 4, 5]
        result = renderer._filter_limit(items, 3)

        assert result == [1, 2, 3]

    def test_url_for_function(self, sample_config):
        """Test the url_for global function."""
        renderer = Renderer(sample_config)

        result = renderer._url_for("/blog/post")
        assert result == "http://localhost:8000/blog/post"

        result = renderer._url_for("blog/post")
        assert result == "http://localhost:8000/blog/post"

    def test_template_inheritance(self, sample_config):
        """Test that template inheritance works."""
        renderer = Renderer(sample_config)

        # Post template extends base template
        html = renderer.render(
            "post.html", {"title": "Test Post", "date": "2024-03-15", "content": "<p>Test</p>"}
        )

        # Should have content from both base and post templates
        assert "<html>" in html  # From base
        assert "<article>" in html  # From post
        assert "<title>Test Post</title>" in html
