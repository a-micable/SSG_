"""
Command-line interface for SSG.

Provides commands for building, initializing, and serving sites.
"""

import http.server
import logging
import socketserver
import sys
from pathlib import Path
from typing import Optional

import click

from ssg import __version__
from ssg.builder import SiteBuilder
from ssg.config import SiteConfig, create_default_config, load_config
from ssg.watcher import watch_site

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="ssg")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """
    SSG - A production-grade static site generator.
    
    Build fast, maintainable static sites with Markdown and Jinja2.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default="config.yaml",
    help="Path to configuration file",
)
@click.option("--clean/--no-clean", default=True, help="Clean output directory before building")
@click.option(
    "--fingerprint/--no-fingerprint",
    default=True,
    help="Enable asset fingerprinting for cache busting",
)
def build(config: Path, clean: bool, fingerprint: bool) -> None:
    """
    Build the static site.
    
    Processes all content, templates, and assets to generate a complete
    static website in the output directory.
    """
    try:
        logger.info("SSG Build")
        logger.info("=" * 50)
        
        # Load configuration
        site_config = load_config(config)
        logger.info(f"Site: {site_config.site_name}")
        logger.info(f"Output: {site_config.output_dir}")
        
        # Build site
        builder = SiteBuilder(site_config)
        builder.build(clean=clean, fingerprint_assets=fingerprint)
        
        logger.info("=" * 50)
        logger.info("Build completed successfully!")
        
    except Exception as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("site_name", default="mysite")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (defaults to site_name)",
)
def init(site_name: str, output: Optional[Path]) -> None:
    """
    Initialize a new site structure.
    
    Creates a starter site with example content, templates, and configuration.
    """
    if output is None:
        output = Path(site_name)
    
    if output.exists() and any(output.iterdir()):
        logger.error(f"Directory {output} already exists and is not empty")
        sys.exit(1)
    
    try:
        logger.info(f"Initializing new site: {site_name}")
        
        # Create directory structure
        output.mkdir(parents=True, exist_ok=True)
        (output / "content").mkdir(exist_ok=True)
        (output / "templates").mkdir(exist_ok=True)
        (output / "assets").mkdir(exist_ok=True)
        (output / "assets" / "css").mkdir(exist_ok=True)
        
        # Create config file
        config_path = output / "config.yaml"
        create_default_config(config_path, site_name)
        
        # Create base template
        _create_base_template(output / "templates" / "base.html")
        _create_default_template(output / "templates" / "default.html")
        _create_index_template(output / "templates" / "index.html")
        
        # Create example content
        _create_example_post(output / "content" / "hello-world.md")
        _create_about_page(output / "content" / "about.md")
        
        # Create example stylesheet
        _create_example_css(output / "assets" / "css" / "style.css")
        
        logger.info(f"Site initialized in {output}")
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  cd {output}")
        logger.info("  ssg build")
        logger.info("  ssg serve")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default="config.yaml",
    help="Path to configuration file",
)
@click.option("--port", "-p", type=int, default=8000, help="Port to serve on")
@click.option("--watch/--no-watch", default=True, help="Watch for changes and rebuild")
def serve(config: Path, port: int, watch: bool) -> None:
    """
    Serve the site locally for development.
    
    Starts a local HTTP server and optionally watches for file changes
    to automatically rebuild the site.
    """
    try:
        logger.info("SSG Development Server")
        logger.info("=" * 50)
        
        # Load configuration
        site_config = load_config(config)
        
        # Build site initially
        logger.info("Building site...")
        builder = SiteBuilder(site_config)
        builder.build(clean=True, fingerprint_assets=False)
        
        # Start watching if requested
        if watch:
            logger.info("Watch mode enabled")
            
            # Start watcher in background thread
            import threading
            
            def rebuild_on_change(changed_files):
                logger.info(f"Changes detected, rebuilding...")
                try:
                    builder.incremental_build(changed_files)
                    logger.info("Rebuild complete")
                except Exception as e:
                    logger.error(f"Rebuild failed: {e}")
            
            watcher_thread = threading.Thread(
                target=watch_site,
                args=(site_config, rebuild_on_change),
                daemon=True,
            )
            watcher_thread.start()
        
        # Start HTTP server
        output_dir = site_config.output_dir
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)
            
            def log_message(self, format, *args):
                # Custom log format
                logger.info(f"{self.address_string()} - {format % args}")
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            logger.info("=" * 50)
            logger.info(f"Serving at http://localhost:{port}")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 50)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("\nShutting down server...")
    
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


def _create_base_template(path: Path) -> None:
    """Create base template."""
    content = """<!DOCTYPE html>
<html lang="{{ site.language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ page.title }} - {{ site.name }}{% endblock %}</title>
    <meta name="description" content="{% block description %}{{ page.description or site.description }}{% endblock %}">
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <h1><a href="/">{{ site.name }}</a></h1>
        <nav>
            <a href="/">Home</a>
            <a href="/about/">About</a>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2024 {{ site.name }}. Built with SSG.</p>
    </footer>
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def _create_default_template(path: Path) -> None:
    """Create default content template."""
    content = """{% extends "base.html" %}

{% block content %}
<article>
    <h1>{{ page.title }}</h1>
    
    {% if page.date %}
    <p class="meta">
        Published: {{ page.date }}
        {% if page.author %} by {{ page.author }}{% endif %}
    </p>
    {% endif %}
    
    {% if page.tags %}
    <p class="tags">
        Tags: {% for tag in page.tags %}<span class="tag">{{ tag }}</span>{% if not loop.last %}, {% endif %}{% endfor %}
    </p>
    {% endif %}
    
    <div class="content">
        {{ content | safe }}
    </div>
</article>
{% endblock %}
"""
    path.write_text(content, encoding="utf-8")


def _create_index_template(path: Path) -> None:
    """Create index/pagination template."""
    content = """{% extends "base.html" %}

{% block title %}{{ site.name }}{% if page_num > 1 %} - Page {{ page_num }}{% endif %}{% endblock %}

{% block content %}
<h1>Recent Posts</h1>

{% for post in posts %}
<article class="post-preview">
    <h2><a href="{{ post.url_path }}">{{ post.metadata.title }}</a></h2>
    {% if post.metadata.date %}
    <p class="meta">{{ post.metadata.date }}</p>
    {% endif %}
    {% if post.metadata.description %}
    <p>{{ post.metadata.description }}</p>
    {% endif %}
</article>
{% endfor %}

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
    path.write_text(content, encoding="utf-8")


def _create_example_post(path: Path) -> None:
    """Create example blog post."""
    content = """---
title: Hello World!
date: 2024-03-15
tags:
  - welcome
  - getting-started
author: SSG
description: Welcome to your new static site
layout: default.html
---

# Welcome to SSG!

This is your first post. Edit this file to get started with your new static site.

## Features

SSG provides:

- **Markdown support** with frontmatter
- **Jinja2 templating** with inheritance
- **Asset fingerprinting** for cache busting
- **RSS feeds** and sitemaps
- **Live reload** development server

## Getting Started

1. Edit content in the `content/` directory
2. Customize templates in `templates/`
3. Add styles to `assets/css/`
4. Run `ssg build` to generate your site
5. Use `ssg serve` for development

Happy building!
"""
    path.write_text(content, encoding="utf-8")


def _create_about_page(path: Path) -> None:
    """Create about page."""
    content = """---
title: About
slug: about
layout: default.html
---

# About This Site

This site is built with [SSG](https://github.com/yourusername/ssg), a production-grade static site generator.

## Technology

- Python 3.11+
- Markdown rendering
- Jinja2 templates
- Asset fingerprinting
- RSS & Sitemap generation

## Contact

Edit this page to add your contact information!
"""
    path.write_text(content, encoding="utf-8")


def _create_example_css(path: Path) -> None:
    """Create example stylesheet."""
    content = """/* Basic styling for SSG sites */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    border-bottom: 2px solid #eee;
    padding-bottom: 20px;
    margin-bottom: 40px;
}

header h1 a {
    color: #2c3e50;
    text-decoration: none;
}

nav {
    margin-top: 10px;
}

nav a {
    margin-right: 15px;
    color: #3498db;
    text-decoration: none;
}

nav a:hover {
    text-decoration: underline;
}

article {
    margin-bottom: 40px;
}

article h1 {
    color: #2c3e50;
    margin-bottom: 10px;
}

article h2 {
    color: #34495e;
    margin-top: 30px;
    margin-bottom: 15px;
}

.meta {
    color: #7f8c8d;
    font-size: 0.9em;
    margin-bottom: 20px;
}

.tags {
    margin-bottom: 20px;
}

.tag {
    background: #ecf0f1;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 0.85em;
}

.content {
    margin-top: 30px;
}

.post-preview {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
}

.post-preview h2 a {
    color: #2c3e50;
    text-decoration: none;
}

.post-preview h2 a:hover {
    color: #3498db;
}

.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

.pagination a {
    color: #3498db;
    text-decoration: none;
}

.pagination a:hover {
    text-decoration: underline;
}

footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 2px solid #eee;
    text-align: center;
    color: #7f8c8d;
    font-size: 0.9em;
}

code {
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

pre {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 20px 0;
}

pre code {
    background: none;
    padding: 0;
}
"""
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    cli()
