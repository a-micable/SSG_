"""
Pytest configuration and shared fixtures for testing.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from ssg.config import SiteConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_site(temp_dir):
    """
    Create a complete sample site structure for testing.

    Returns a dictionary with paths to:
    - root: Site root directory
    - content: Content directory
    - templates: Template directory
    - output: Output directory
    - config: Configuration file
    """
    # Create directories
    content_dir = temp_dir / "content"
    template_dir = temp_dir / "templates"
    output_dir = temp_dir / "dist"
    assets_dir = temp_dir / "assets"

    content_dir.mkdir()
    template_dir.mkdir()
    (content_dir / "posts").mkdir()
    (assets_dir / "css").mkdir(parents=True)

    # Create sample content files
    post1 = content_dir / "posts" / "first-post.md"
    post1.write_text("""---
title: First Post
date: 2024-01-15
tags:
  - python
  - web
slug: first-post
layout: post.html
---

# First Post

This is the first post content.

## Section

More content here.
""")

    post2 = content_dir / "posts" / "second-post.md"
    post2.write_text("""---
title: Second Post
date: 2024-02-20
tags:
  - python
slug: second-post
layout: post.html
draft: false
---

# Second Post

This is the second post.
""")

    draft_post = content_dir / "posts" / "draft.md"
    draft_post.write_text("""---
title: Draft Post
date: 2024-03-01
slug: draft
layout: post.html
draft: true
---

This is a draft.
""")

    # Create sample templates
    base_template = template_dir / "base.html"
    base_template.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{{ title | default(site.name) }}{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
""")

    post_template = template_dir / "post.html"
    post_template.write_text("""{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<article>
    <h1>{{ title }}</h1>
    <time>{{ date }}</time>
    {{ content | safe }}
</article>
{% endblock %}
""")

    index_template = template_dir / "index.html"
    index_template.write_text("""{% extends "base.html" %}
{% block content %}
<h1>Posts</h1>
{% for post in posts %}
<article>
    <h2>{{ post.title }}</h2>
    <time>{{ post.date }}</time>
</article>
{% endfor %}
{% endblock %}
""")

    tag_template = template_dir / "tag.html"
    tag_template.write_text("""{% extends "base.html" %}
{% block content %}
<h1>Tag: {{ tag }}</h1>
{% for post in posts %}
<article>{{ post.title }}</article>
{% endfor %}
{% endblock %}
""")

    # Create sample assets
    css_file = assets_dir / "css" / "style.css"
    css_file.write_text("""body { margin: 0; }""")

    # Create config file
    config_file = temp_dir / "config.yml"
    config_file.write_text(f"""site_name: Test Site
base_url: http://localhost:8000
content_dir: {content_dir}
template_dir: {template_dir}
output_dir: {output_dir}
posts_per_page: 5
asset_dirs:
  - {assets_dir}
""")

    return {
        "root": temp_dir,
        "content": content_dir,
        "templates": template_dir,
        "output": output_dir,
        "assets": assets_dir,
        "config": config_file,
    }


@pytest.fixture
def sample_config(sample_site):
    """Load configuration from sample site."""
    from ssg.config import ConfigLoader

    return ConfigLoader.load(sample_site["config"])
