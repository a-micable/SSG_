"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from ssg.config import SiteConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config(temp_dir: Path) -> SiteConfig:
    """Create a sample site configuration."""
    content_dir = temp_dir / "content"
    template_dir = temp_dir / "templates"
    output_dir = temp_dir / "dist"
    
    content_dir.mkdir()
    template_dir.mkdir()
    
    config = SiteConfig(
        site_name="Test Site",
        base_url="https://example.com",
        content_dir=content_dir,
        template_dir=template_dir,
        output_dir=output_dir,
        posts_per_page=5,
        author="Test Author",
        description="A test site",
    )
    
    return config


@pytest.fixture
def sample_markdown_file(temp_dir: Path) -> Path:
    """Create a sample Markdown file with frontmatter."""
    content = """---
title: Test Post
date: 2024-03-15
tags:
  - python
  - testing
author: Test Author
description: A test post
layout: post.html
---

# Test Content

This is a test post with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2
"""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_template(temp_dir: Path) -> Path:
    """Create a sample Jinja2 template."""
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ page.title }} - {{ site.name }}</title>
</head>
<body>
    <h1>{{ page.title }}</h1>
    <div>{{ content | safe }}</div>
</body>
</html>
"""
    
    template_path = temp_dir / "templates" / "post.html"
    template_path.parent.mkdir(exist_ok=True)
    template_path.write_text(template_content, encoding="utf-8")
    return template_path


@pytest.fixture
def sample_site(temp_dir: Path) -> Path:
    """Create a complete sample site structure."""
    # Create directories
    (temp_dir / "content").mkdir()
    (temp_dir / "templates").mkdir()
    (temp_dir / "assets" / "css").mkdir(parents=True)
    
    # Create config
    config_content = """site_name: Test Blog
base_url: https://test.example.com
content_dir: content
template_dir: templates
output_dir: dist
posts_per_page: 5
author: Test Author
description: A test blog
"""
    (temp_dir / "config.yaml").write_text(config_content)
    
    # Create templates
    base_template = """<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{{ site.name }}{% endblock %}</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
"""
    (temp_dir / "templates" / "base.html").write_text(base_template)
    
    default_template = """{% extends "base.html" %}
{% block title %}{{ page.title }} - {{ site.name }}{% endblock %}
{% block content %}
<article>
    <h1>{{ page.title }}</h1>
    {% if page.date %}<p>Date: {{ page.date }}</p>{% endif %}
    <div>{{ content | safe }}</div>
</article>
{% endblock %}
"""
    (temp_dir / "templates" / "default.html").write_text(default_template)
    
    index_template = """{% extends "base.html" %}
{% block content %}
<h1>Posts</h1>
{% for post in posts %}
<article>
    <h2><a href="{{ post.url_path }}">{{ post.metadata.title }}</a></h2>
</article>
{% endfor %}
{% endblock %}
"""
    (temp_dir / "templates" / "index.html").write_text(index_template)
    
    # Create content
    for i in range(1, 4):
        post_content = f"""---
title: Test Post {i}
date: 2024-03-{i:02d}
tags:
  - test
  - post{i}
description: Test post {i}
layout: default.html
---

# Post {i}

This is test post number {i}.
"""
        (temp_dir / "content" / f"post{i}.md").write_text(post_content)
    
    # Create an asset
    css_content = """body { font-family: sans-serif; }"""
    (temp_dir / "assets" / "css" / "style.css").write_text(css_content)
    
    return temp_dir
