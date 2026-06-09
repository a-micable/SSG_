"""
Command-line interface for the Static Site Generator.
Provides build, init, and serve commands.
"""

import http.server
import socketserver
from pathlib import Path
import click
from .config import ConfigLoader, SiteConfig, ConfigError
from .builder import SiteBuilder, BuildError
from .watcher import FileWatcher


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Static Site Generator - A production-grade SSG for building fast, modern websites.
    
    Commands:
        build   Build the entire site
        init    Initialize a new site
        serve   Start development server with live reload
    """
    pass


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    default='config.yml',
    help='Path to configuration file'
)
@click.option(
    '--clean/--no-clean',
    default=True,
    help='Clean output directory before building'
)
@click.option(
    '--drafts',
    is_flag=True,
    help='Include draft content in build'
)
def build(config: Path, clean: bool, drafts: bool):
    """
    Build the entire site into the output directory.
    
    This command:
    - Parses all Markdown content
    - Renders templates with Jinja2
    - Processes and fingerprints assets
    - Generates RSS feed and sitemap
    - Creates paginated index pages
    - Builds tag archive pages
    
    Example:
        ssg build
        ssg build --config mysite/config.yml
        ssg build --no-clean --drafts
    """
    try:
        # Load configuration
        click.echo(f"Loading configuration from {config}")
        site_config = ConfigLoader.load(config)
        
        # Override draft setting if specified
        if drafts:
            site_config.build_drafts = True
        
        # Create builder and execute build
        builder = SiteBuilder(site_config)
        builder.build(clean=clean)
        
        click.echo(click.style("\n✓ Build complete!", fg='green', bold=True))
        
    except ConfigError as e:
        click.echo(click.style(f"Configuration error: {e}", fg='red'), err=True)
        raise click.Abort()
    except BuildError as e:
        click.echo(click.style(f"Build error: {e}", fg='red'), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg='red'), err=True)
        raise click.Abort()


@cli.command()
@click.argument('path', type=click.Path(path_type=Path))
@click.option(
    '--name',
    prompt='Site name',
    help='Name of the site'
)
@click.option(
    '--url',
    prompt='Base URL',
    default='http://localhost:8000',
    help='Base URL for the site'
)
def init(path: Path, name: str, url: str):
    """
    Initialize a new site with starter structure.
    
    Creates:
    - config.yml with site configuration
    - content/ directory with sample posts
    - templates/ directory with base layouts
    - assets/ directory for CSS, JS, images
    
    Example:
        ssg init mysite
        ssg init myblog --name "My Blog" --url "https://example.com"
    """
    try:
        # Create site directory
        if path.exists():
            if not click.confirm(f"{path} already exists. Continue?"):
                raise click.Abort()
        else:
            path.mkdir(parents=True)
        
        click.echo(f"Initializing site in {path}")
        
        # Create directory structure
        directories = [
            path / "content" / "posts",
            path / "templates",
            path / "assets" / "css",
            path / "assets" / "js",
            path / "assets" / "images",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            click.echo(f"  Created {directory.relative_to(path)}/")
        
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
        config_path.write_text(config_content, encoding='utf-8')
        click.echo(f"  Created config.yml")
        
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
        sample_post.write_text(sample_content, encoding='utf-8')
        click.echo(f"  Created sample post")
        
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
        base_template.write_text(base_content, encoding='utf-8')
        click.echo(f"  Created base template")
        
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
        post_template.write_text(post_content, encoding='utf-8')
        click.echo(f"  Created post template")
        
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
        index_template.write_text(index_content, encoding='utf-8')
        click.echo(f"  Created index template")
        
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
        tag_template.write_text(tag_content, encoding='utf-8')
        click.echo(f"  Created tag template")
        
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
        css_file.write_text(css_content, encoding='utf-8')
        click.echo(f"  Created sample CSS")
        
        click.echo(click.style("\n✓ Site initialized successfully!", fg='green', bold=True))
        click.echo(f"\nNext steps:")
        click.echo(f"  cd {path}")
        click.echo(f"  ssg build")
        click.echo(f"  ssg serve")
        
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        raise click.Abort()


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    default='config.yml',
    help='Path to configuration file'
)
@click.option(
    '--port',
    type=int,
    default=8000,
    help='Port to serve on'
)
@click.option(
    '--watch/--no-watch',
    default=True,
    help='Watch for changes and rebuild automatically'
)
def serve(config: Path, port: int, watch: bool):
    """
    Start a local development server.
    
    Serves the built site and optionally watches for changes to rebuild automatically.
    
    Example:
        ssg serve
        ssg serve --port 3000
        ssg serve --no-watch
    """
    try:
        # Load configuration
        site_config = ConfigLoader.load(config)
        
        # Build site first
        click.echo("Building site...")
        builder = SiteBuilder(site_config)
        builder.build()
        
        # Set up file watcher if enabled
        if watch:
            def on_change(changed_files):
                click.echo(f"\nDetected changes in {len(changed_files)} file(s)")
                try:
                    builder.rebuild_changed(changed_files)
                    click.echo(click.style("✓ Rebuild complete", fg='green'))
                except Exception as e:
                    click.echo(click.style(f"✗ Rebuild failed: {e}", fg='red'))
            
            watcher = FileWatcher(on_change)
            watcher.watch(site_config.content_dir)
            watcher.watch(site_config.template_dir)
            watcher.start()
        
        # Start HTTP server
        handler = http.server.SimpleHTTPRequestHandler
        
        class CustomHandler(handler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(site_config.output_dir), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress request logs (or customize as needed)
                pass
        
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            click.echo(click.style(f"\n✓ Server running at http://localhost:{port}/", fg='green', bold=True))
            if watch:
                click.echo("Watching for changes... (Press Ctrl+C to stop)")
            else:
                click.echo("Press Ctrl+C to stop")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                click.echo("\nStopping server...")
                if watch:
                    watcher.stop()
        
    except ConfigError as e:
        click.echo(click.style(f"Configuration error: {e}", fg='red'), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
