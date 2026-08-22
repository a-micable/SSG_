"""Write starter site files for `ssg init`."""

from collections.abc import Callable
from pathlib import Path

Echo = Callable[[str], None]


def write_new_site(path: Path, name: str, url: str, echo: Echo) -> None:
    """Create config, content, templates, and assets under path."""
    directories = [
        path / "content" / "posts",
        path / "templates",
        path / "assets" / "css",
        path / "assets" / "js",
        path / "assets" / "images",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        echo(f"  Created {directory.relative_to(path)}/")

    # Create config.yml
    config_path = path / "config.yml"
    config_content = f"""site_name: {name}
base_url: {url}
content_dir: content
template_dir: templates
output_dir: dist
posts_per_page: 10
date_format: "%B %d, %Y"
timezone: UTC
asset_dirs:
  - assets
build_drafts: false
feed_enabled: true
sitemap_enabled: true
author: {name}
description: A site built with SSG
language: en
"""
    config_path.write_text(config_content, encoding="utf-8")
    echo("  Created config.yml")

    # Create sample post
    sample_post = path / "content" / "posts" / "welcome.md"
    sample_content = """---
title: Welcome to Your New Site
date: 2024-03-15
tags:
  - welcome
  - getting-started
slug: welcome
layout: post.html
draft: false
---

# Welcome!

This is your first post. Edit this file in `content/posts/welcome.md` to get started.

## Features

- **Markdown Support**: Write content in Markdown
- **Frontmatter**: Configure posts with YAML frontmatter
- **Templates**: Customize layouts with Jinja2
- **Assets**: Include CSS, JavaScript, and images
- **RSS Feed**: Automatically generated
- **Sitemap**: SEO-friendly sitemap generation

## Next Steps

1. Edit `config.yml` to configure your site
2. Create more posts in `content/posts/`
3. Customize templates in `templates/`
4. Add your styles in `assets/css/`
5. Build your site with `ssg build`
6. Serve locally with `ssg serve`

Happy building!
"""
    sample_post.write_text(sample_content, encoding="utf-8")
    echo("  Created sample post")

    # Create base template
    base_template = path / "templates" / "base.html"
    base_content = """<!DOCTYPE html>
<html lang="{{ site.language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ site.name }}{% endblock %}</title>
    <meta name="description" content="{{ site.description }}">
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <nav>
            <h1><a href="/">{{ site.name }}</a></h1>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; {{ now().year }} {{ site.name }}. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    base_template.write_text(base_content, encoding="utf-8")
    echo("  Created base template")

    # Create post template
    post_template = path / "templates" / "post.html"
    post_content = """{% extends "base.html" %}

{% block title %}{{ title }} - {{ site.name }}{% endblock %}

{% block content %}
<article>
    <header>
        <h1>{{ title }}</h1>
        <time datetime="{{ date }}">{{ date | strftime('%B %d, %Y') }}</time>
        {% if tags %}
        <div class="tags">
            {% for tag in tags %}
            <a href="/tags/{{ tag }}/">#{{ tag }}</a>
            {% endfor %}
        </div>
        {% endif %}
    </header>
    
    <div class="content">
        {{ content | safe }}
    </div>
</article>
{% endblock %}
"""
    post_template.write_text(post_content, encoding="utf-8")
    echo("  Created post template")

    # Create index template
    index_template = path / "templates" / "index.html"
    index_content = """{% extends "base.html" %}

{% block content %}
<section class="posts">
    <h2>Recent Posts</h2>
    {% for post in posts %}
    <article>
        <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
        <time datetime="{{ post.date }}">{{ post.date | strftime('%B %d, %Y') }}</time>
        <p>{{ post.content | excerpt(200) }}</p>
        <a href="{{ post.url }}">Read more →</a>
    </article>
    {% endfor %}
</section>

{% if total_pages > 1 %}
<nav class="pagination">
    {% if has_prev %}
    <a href="{{ prev_url }}">&larr; Newer</a>
    {% endif %}
    <span>Page {{ page_num }} of {{ total_pages }}</span>
    {% if has_next %}
    <a href="{{ next_url }}">Older &rarr;</a>
    {% endif %}
</nav>
{% endif %}
{% endblock %}
"""
    index_template.write_text(index_content, encoding="utf-8")
    echo("  Created index template")

    # Create tag template
    tag_template = path / "templates" / "tag.html"
    tag_content = """{% extends "base.html" %}

{% block title %}Tag: {{ tag }} - {{ site.name }}{% endblock %}

{% block content %}
<h2>Posts tagged "{{ tag }}"</h2>
<section class="posts">
    {% for post in posts %}
    <article>
        <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
        <time datetime="{{ post.date }}">{{ post.date | strftime('%B %d, %Y') }}</time>
    </article>
    {% endfor %}
</section>
{% endblock %}
"""
    tag_template.write_text(tag_content, encoding="utf-8")
    echo("  Created tag template")

    # Create sample CSS
    css_file = path / "assets" / "css" / "style.css"
    css_content = """/* Basic styling for your site */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 2px solid #eee;
}

header h1 a {
    color: #333;
    text-decoration: none;
}

main {
    min-height: 60vh;
}

article {
    margin-bottom: 40px;
}

article h1, article h2, article h3 {
    margin-top: 1em;
    margin-bottom: 0.5em;
}

time {
    color: #666;
    font-size: 0.9em;
}

.tags a {
    display: inline-block;
    padding: 4px 8px;
    margin: 4px;
    background: #f0f0f0;
    color: #666;
    text-decoration: none;
    border-radius: 3px;
    font-size: 0.9em;
}

.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
}

footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 2px solid #eee;
    color: #666;
    font-size: 0.9em;
}
"""
    css_file.write_text(css_content, encoding="utf-8")
    echo("  Created sample CSS")
