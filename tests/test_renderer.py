"""Tests for template rendering."""

from pathlib import Path

import pytest

from ssg import RenderingError
from ssg.parser import ContentParser
from ssg.renderer import TemplateRenderer


def test_render_simple_template(sample_config, sample_markdown_file, sample_template):
    """Test rendering content with a simple template."""
    parser = ContentParser()
    renderer = TemplateRenderer(sample_config)
    
    parsed = parser.parse_file(
        sample_markdown_file, sample_config.content_dir.parent
    )
    
    html = renderer.render_content(parsed)
    
    assert "<title>Test Post - Test Site</title>" in html
    assert "<h1>Test Post</h1>" in html
    assert "This is a test post" in html


def test_render_template_not_found(sample_config, temp_dir):
    """Test that missing template raises error."""
    content = """---
title: Test
layout: nonexistent.html
---
Content"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    renderer = TemplateRenderer(sample_config)
    
    parsed = parser.parse_file(file_path, temp_dir)
    
    with pytest.raises(RenderingError, match="Template not found"):
        renderer.render_content(parsed)


def test_render_with_site_context(sample_config, temp_dir, sample_template):
    """Test rendering with additional site context."""
    content = """---
title: Test
layout: post.html
---
Content"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    renderer = TemplateRenderer(sample_config)
    
    parsed = parser.parse_file(file_path, temp_dir)
    
    site_context = {"custom_var": "custom_value"}
    html = renderer.render_content(parsed, site_context)
    
    assert "Test Site" in html  # From config


def test_render_template_directly(sample_config, sample_template):
    """Test rendering a template with arbitrary context."""
    renderer = TemplateRenderer(sample_config)
    
    context = {
        "page": {"title": "Direct Render"},
        "content": "<p>Test content</p>",
    }
    
    html = renderer.render_template("post.html", context)
    
    assert "<title>Direct Render - Test Site</title>" in html
    assert "<p>Test content</p>" in html


def test_filter_url(sample_config, sample_template):
    """Test the url filter."""
    renderer = TemplateRenderer(sample_config)
    
    # Test relative path
    result = renderer._filter_url("/style.css")
    assert result == "https://example.com/style.css"
    
    # Test path without leading slash
    result = renderer._filter_url("style.css")
    assert result == "https://example.com/style.css"
    
    # Test absolute URL (should not change)
    result = renderer._filter_url("https://other.com/style.css")
    assert result == "https://other.com/style.css"


def test_filter_strftime_with_string_date_fails(sample_config):
    """
    Test that strftime filter fails with string dates.
    
    This demonstrates BUG 1 symptom: when parser stores date as string,
    template rendering fails when trying to use strftime filter.
    """
    renderer = TemplateRenderer(sample_config)
    
    # This is what happens when BUG 1 is active
    with pytest.raises(RenderingError, match="expected datetime object, got string"):
        renderer._filter_strftime("2024-03-15", "%B %d, %Y")


def test_filter_date(sample_config):
    """Test the date filter."""
    from datetime import datetime
    
    renderer = TemplateRenderer(sample_config)
    
    dt = datetime(2024, 3, 15, 10, 30)
    result = renderer._filter_date(dt)
    
    assert result == "March 15, 2024"


def test_template_inheritance(sample_config, temp_dir):
    """Test template inheritance with extends."""
    # Create base template
    base_template = """<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
</head>
<body>
    {% block content %}Default content{% endblock %}
</body>
</html>
"""
    
    # Create child template
    child_template = """{% extends "base.html" %}
{% block title %}{{ page.title }}{% endblock %}
{% block content %}<p>{{ content | safe }}</p>{% endblock %}
"""
    
    (sample_config.template_dir / "base.html").write_text(base_template)
    (sample_config.template_dir / "child.html").write_text(child_template)
    
    renderer = TemplateRenderer(sample_config)
    
    context = {
        "page": {"title": "Child Page"},
        "content": "<strong>Test</strong>",
    }
    
    html = renderer.render_template("child.html", context)
    
    assert "<title>Child Page</title>" in html
    assert "<p><strong>Test</strong></p>" in html


def test_template_includes(sample_config, temp_dir):
    """Test template includes."""
    # Create partial
    partial = """<nav><a href="/">Home</a></nav>"""
    (sample_config.template_dir / "nav.html").write_text(partial)
    
    # Create template with include
    template = """<!DOCTYPE html>
<html>
<body>
    {% include "nav.html" %}
    <main>{{ content | safe }}</main>
</body>
</html>
"""
    (sample_config.template_dir / "page.html").write_text(template)
    
    renderer = TemplateRenderer(sample_config)
    
    context = {"content": "<p>Content</p>"}
    html = renderer.render_template("page.html", context)
    
    assert "<nav><a href=\"/\">Home</a></nav>" in html
    assert "<main><p>Content</p></main>" in html


def test_rendering_with_collections(sample_config, temp_dir, sample_template):
    """Test rendering with collections in context."""
    content = """---
title: Post
layout: post.html
---
Content"""
    
    file_path = temp_dir / "post.md"
    file_path.write_text(content)
    
    parser = ContentParser()
    renderer = TemplateRenderer(sample_config)
    
    parsed = parser.parse_file(file_path, temp_dir)
    
    # Simulate collections
    site_context = {
        "collections": {
            "tags": {"python": [], "web": []},
            "all_posts": [parsed],
        }
    }
    
    html = renderer.render_content(parsed, site_context)
    assert html  # Should render successfully


def test_template_missing_directory():
    """Test that missing template directory raises error."""
    from ssg.config import SiteConfig
    
    config = SiteConfig(
        site_name="Test",
        base_url="https://example.com",
        content_dir=Path("content"),
        template_dir=Path("nonexistent_templates"),
        output_dir=Path("dist"),
    )
    
    with pytest.raises(RenderingError, match="Template directory not found"):
        TemplateRenderer(config)
