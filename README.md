# Static Site Generator (SSG)

A production-grade static site generator built with Python, featuring Markdown parsing, Jinja2 templating, asset fingerprinting, RSS feeds, and more.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

### Core Functionality
- **Markdown Parsing** - Full-featured Markdown to HTML conversion with frontmatter support
- **Jinja2 Templating** - Powerful template engine with inheritance and custom filters
- **Asset Pipeline** - Automatic asset copying with fingerprinting for cache busting
- **RSS Feed Generation** - Standards-compliant RSS 2.0 feeds
- **XML Sitemap** - SEO-friendly sitemap generation
- **File Watching** - Development mode with automatic rebuilds
- **Pagination** - Built-in support for paginated content lists
- **Tag Archives** - Automatic tag-based content organization

### Developer Experience
- **CLI Interface** - Intuitive command-line tools (`build`, `init`, `serve`)
- **Configuration** - YAML-based configuration with validation
- **Incremental Builds** - Smart dependency tracking for fast rebuilds
- **Local Development Server** - Built-in HTTP server for testing
- **Comprehensive Tests** - Full test suite with pytest

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/a-micable/SSG.git
cd SSG

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Create Your First Site

```bash
# Initialize a new site
ssg init mysite

# Change to site directory
cd mysite

# Build the site
ssg build

# Serve locally
ssg serve
```

Visit http://localhost:8000 to see your site!

## Usage

### Commands

#### `ssg build`

Build your entire site from source.

```bash
# Basic build
ssg build

# Build with custom config
ssg build --config path/to/config.yml

# Build including drafts
ssg build --drafts

# Build without cleaning output directory
ssg build --no-clean
```

#### `ssg init`

Initialize a new site with starter templates.

```bash
# Interactive initialization
ssg init mysite

# With options
ssg init mysite --name "My Blog" --url "https://myblog.com"
```

#### `ssg serve`

Start a development server with live reload.

```bash
# Start server on default port (8000)
ssg serve

# Use custom port
ssg serve --port 3000

# Serve without watching for changes
ssg serve --no-watch
```

## Configuration

Create a `config.yml` file:

```yaml
# Required fields
site_name: My Awesome Blog
base_url: https://example.com

# Directory paths
content_dir: content
template_dir: templates
output_dir: dist

# Pagination
posts_per_page: 10

# Date formatting
date_format: "%B %d, %Y"
timezone: UTC

# Asset directories
asset_dirs:
  - assets
  - static

# Build options
build_drafts: false
feed_enabled: true
sitemap_enabled: true

# Metadata
author: Your Name
description: A blog about cool stuff
language: en
```

## Content Structure

### Markdown Files

Content files use Markdown with YAML frontmatter:

```markdown
---
title: My First Post
date: 2024-03-15
tags:
  - python
  - web-development
slug: my-first-post
layout: post.html
draft: false
---

# My First Post

Your content goes here in **Markdown** format.

## Features

- Lists
- Code blocks
- Tables
- And more!
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Post title |
| `date` | No | Publication date (YYYY-MM-DD) |
| `slug` | No | URL slug (defaults to filename) |
| `layout` | No | Template to use (default: `post.html`) |
| `tags` | No | List of tags |
| `draft` | No | Draft status (default: false) |

## Templates

Templates use Jinja2 syntax with layout inheritance:

### Base Template (`templates/base.html`)

```html
<!DOCTYPE html>
<html lang="{{ site.language }}">
<head>
    <title>{% block title %}{{ site.name }}{% endblock %}</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

### Post Template (`templates/post.html`)

```html
{% extends "base.html" %}

{% block title %}{{ title }} - {{ site.name }}{% endblock %}

{% block content %}
<article>
    <h1>{{ title }}</h1>
    <time>{{ date | strftime('%B %d, %Y') }}</time>
    {{ content | safe }}
</article>
{% endblock %}
```

### Available Template Variables

- `site.name` - Site name from config
- `site.base_url` - Base URL
- `site.description` - Site description
- `site.author` - Default author
- `title` - Content title
- `date` - Publication date
- `content` - Rendered HTML content
- `tags` - List of tags
- `url` - Content URL

### Custom Filters

- `{{ date | strftime('%B %d, %Y') }}` - Format dates
- `{{ text | excerpt(200) }}` - Extract excerpt
- `{{ items | limit(10) }}` - Limit list length
- `{{ path | url_for }}` - Generate full URLs

## Project Structure

```
mysite/
├── config.yml          # Site configuration
├── content/            # Markdown content
│   └── posts/
│       ├── post-1.md
│       └── post-2.md
├── templates/          # Jinja2 templates
│   ├── base.html
│   ├── post.html
│   ├── index.html
│   └── tag.html
├── assets/             # Static assets
│   ├── css/
│   ├── js/
│   └── images/
└── dist/               # Generated output
    ├── index.html
    ├── feed.xml
    ├── sitemap.xml
    └── ...
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ssg

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Running with Docker

```bash
# Build the image
docker build -t ssg .

# Run tests
docker run --rm ssg pytest

# Build a site
docker run --rm -v $(pwd)/mysite:/site ssg build
```

## Architecture

The SSG follows a modular architecture with clear separation of concerns:

- **Parser** (`parser.py`) - Markdown and frontmatter parsing
- **Renderer** (`renderer.py`) - Template rendering with Jinja2
- **Builder** (`builder.py`) - Build orchestration and dependency tracking
- **Assets** (`assets.py`) - Asset processing and fingerprinting
- **Feed** (`feed.py`) - RSS 2.0 feed generation
- **Sitemap** (`sitemap.py`) - XML sitemap generation
- **Watcher** (`watcher.py`) - File watching for development
- **CLI** (`cli.py`) - Command-line interface
- **Config** (`config.py`) - Configuration management

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## Known Issues & Debugging

This project intentionally includes realistic bugs for educational purposes:

1. **Date Parsing** - Dates stored as strings instead of datetime objects
2. **Cache Invalidation** - Template changes may not trigger dependent rebuilds
3. **Pagination** - Off-by-one error when total items divide evenly
4. **RSS Timezone** - Dates in feed use local time instead of UTC
5. **Asset Paths** - Fingerprinted assets break on nested pages

See tests for expected behavior and bug demonstrations.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/a-micable/SSG.git
cd SSG

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/a-micable/SSG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/a-micable/SSG/discussions)

## Acknowledgments

Built with:
- [Python](https://www.python.org/)
- [Click](https://click.palletsprojects.com/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [python-frontmatter](https://github.com/eyeseast/python-frontmatter)
- [Markdown](https://python-markdown.github.io/)
- [Watchdog](https://github.com/gorakhargosh/watchdog)
- [pytest](https://pytest.org/)
