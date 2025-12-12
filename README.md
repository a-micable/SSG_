# SSG - Static Site Generator

A production-grade static site generator built with Python. Fast, maintainable, and feature-rich.

## Features

- **Markdown Processing**: Full-featured Markdown rendering with frontmatter support
- **Jinja2 Templates**: Powerful templating with inheritance and includes
- **Asset Pipeline**: Automatic asset copying with optional fingerprinting for cache busting
- **Collections**: Automatic tag and date-based content organization
- **Pagination**: Built-in pagination for large content collections
- **RSS Feeds**: Standards-compliant RSS 2.0 feed generation
- **Sitemaps**: XML sitemap generation for SEO
- **Incremental Builds**: Smart dependency tracking for faster rebuilds
- **Dev Server**: Built-in development server with live reload
- **Type Safety**: Comprehensive type hints throughout

## Quick Start

### Installation

```bash
pip install -e .
```

Or install development dependencies:

```bash
pip install -e ".[dev]"
```

### Create a New Site

```bash
ssg init mysite
cd mysite
```

This creates a starter site structure:

```
mysite/
├── config.yaml          # Site configuration
├── content/             # Markdown content files
│   ├── hello-world.md
│   └── about.md
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── default.html
│   └── index.html
└── assets/              # Static assets
    └── css/
        └── style.css
```

### Build Your Site

```bash
ssg build
```

Your built site will be in the `dist/` directory, ready to deploy.

### Development Server

```bash
ssg serve
```

Visit http://localhost:8000 to preview your site. The server watches for changes and automatically rebuilds.

## Configuration

Configuration is managed via `config.yaml`:

```yaml
site_name: My Blog
base_url: https://example.com
content_dir: content
template_dir: templates
output_dir: dist
posts_per_page: 10
timezone: UTC
author: Your Name
description: A site built with SSG
language: en
```

### Required Fields

- `site_name`: Display name for your site
- `base_url`: Full base URL (must include `http://` or `https://`)
- `content_dir`: Directory containing Markdown files
- `template_dir`: Directory containing Jinja2 templates
- `output_dir`: Where to generate the built site

### Optional Fields

- `posts_per_page`: Number of posts per paginated page (default: 10)
- `timezone`: Timezone for date handling (default: UTC)
- `author`: Default author name
- `description`: Site description for feeds
- `language`: Language code (default: en)

## Content

### Frontmatter

Content files use YAML frontmatter:

```markdown
---
title: My First Post
date: 2024-03-15
tags:
  - python
  - web
slug: my-first-post
layout: default.html
author: Jane Doe
description: An introduction to my blog
draft: false
---

# Welcome

Your content here...
```

#### Frontmatter Fields

- `title` (required): Page title
- `date`: Publication date (YYYY-MM-DD format)
- `tags`: List of tags or comma-separated string
- `slug`: Custom URL slug (overrides auto-generated path)
- `layout`: Template file to use (default: default.html)
- `author`: Author name (overrides site default)
- `description`: Page description for SEO and feeds
- `draft`: Set to `true` to exclude from builds

### URL Generation

URLs are automatically generated from file paths:

- `content/blog/my-post.md` → `/blog/my-post/`
- `content/about.md` → `/about/`
- `content/index.md` → `/`

Custom slugs override the default:

```yaml
slug: custom-url
```

Result: `/custom-url/`

## Templates

Templates use Jinja2 with these special variables:

### Site Variables

```jinja2
{{ site.name }}          <!-- Site name -->
{{ site.base_url }}      <!-- Base URL -->
{{ site.author }}        <!-- Default author -->
{{ site.description }}   <!-- Site description -->
{{ site.language }}      <!-- Language code -->
```

### Page Variables

```jinja2
{{ page.title }}         <!-- Page title -->
{{ page.date }}          <!-- Publication date -->
{{ page.tags }}          <!-- List of tags -->
{{ page.author }}        <!-- Page author -->
{{ page.description }}   <!-- Page description -->
{{ page.url }}           <!-- Page URL path -->
```

### Content

```jinja2
{{ content | safe }}     <!-- Rendered HTML content -->
```

### Collections

```jinja2
{{ collections.all_posts }}          <!-- All posts, newest first -->
{{ collections.tags }}                <!-- Posts organized by tag -->
{{ collections.archives }}            <!-- Posts organized by year -->
```

### Custom Filters

```jinja2
{{ page.date | strftime('%B %d, %Y') }}   <!-- Format date -->
{{ page.date | date }}                     <!-- Format with default -->
{{ '/style.css' | url }}                   <!-- Absolute URL -->
```

### Template Inheritance

```jinja2
{% extends "base.html" %}

{% block title %}{{ page.title }}{% endblock %}

{% block content %}
  <article>
    <h1>{{ page.title }}</h1>
    {{ content | safe }}
  </article>
{% endblock %}
```

## CLI Commands

### `ssg build`

Build the entire site:

```bash
ssg build                    # Clean build with fingerprinting
ssg build --no-clean         # Keep existing files
ssg build --no-fingerprint   # Disable asset fingerprinting
ssg build --config custom.yaml
```

### `ssg init`

Initialize a new site:

```bash
ssg init mysite              # Create site in ./mysite
ssg init --output /path/to/site
```

### `ssg serve`

Run development server:

```bash
ssg serve                    # Serve on port 8000 with watch
ssg serve --port 3000        # Custom port
ssg serve --no-watch         # Disable file watching
```

## Architecture

### Core Components

```
ssg/
├── cli.py          # Command-line interface
├── config.py       # Configuration loading and validation
├── parser.py       # Markdown and frontmatter parsing
├── renderer.py     # Jinja2 template rendering
├── builder.py      # Build orchestration and dependency tracking
├── assets.py       # Asset processing and fingerprinting
├── feed.py         # RSS feed generation
├── sitemap.py      # XML sitemap generation
└── watcher.py      # File watching for development
```

### Build Process

1. **Parse Configuration**: Load and validate `config.yaml`
2. **Discover Content**: Find all Markdown files in content directory
3. **Parse Content**: Extract frontmatter and render Markdown to HTML
4. **Build Collections**: Organize content by tags and dates
5. **Render Pages**: Apply templates to generate HTML files
6. **Generate Pagination**: Create paginated index pages
7. **Process Assets**: Copy and fingerprint static files
8. **Rewrite URLs**: Update asset references in HTML
9. **Generate Feeds**: Create RSS feed with latest posts
10. **Generate Sitemap**: Create XML sitemap for SEO

### Dependency Tracking

The builder tracks dependencies for incremental builds:

- **Content → Templates**: When content changes, only that page rebuilds
- **Templates → Content**: When a template changes, all pages using it rebuild
- **Template Inheritance**: Changes to base templates trigger rebuilds of child templates

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=ssg --cov-report=html
```

Run specific tests:

```bash
pytest tests/test_parser.py
pytest tests/test_builder.py::test_full_site_build
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_config.py       # Configuration tests
├── test_parser.py       # Content parsing tests
├── test_renderer.py     # Template rendering tests
├── test_builder.py      # Site building tests
└── test_assets.py       # Asset processing tests
```

Tests use behavior-based testing with real fixtures rather than mocking internal implementation details.

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/ssg.git
cd ssg

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black ssg/ tests/

# Lint
ruff check ssg/ tests/

# Type checking
mypy ssg/
```

### Project Guidelines

- **Type Hints**: All functions must have type hints
- **Docstrings**: Public APIs require docstrings
- **Testing**: New features require tests
- **Error Handling**: Use custom exceptions from `ssg/__init__.py`
- **Logging**: Use the logging module, not print statements

## Deployment

### Static Hosts

Built sites are pure HTML/CSS/JS and can be deployed to:

- **Netlify**: Drop the `dist/` folder or connect to Git
- **Vercel**: Deploy from Git repository
- **GitHub Pages**: Push `dist/` to `gh-pages` branch
- **S3 + CloudFront**: Upload `dist/` to S3 bucket
- **Any web server**: Copy `dist/` to your server

### Docker

Build and run in Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install .

WORKDIR /site
CMD ["ssg", "build"]
```

Build:

```bash
docker build -t ssg .
docker run -v $(pwd)/mysite:/site ssg
```

## Known Issues & Roadmap

See the issue tracker for known bugs and planned features.

### Current Limitations

- No built-in syntax highlighting (can be added via Markdown extensions)
- No image optimization (process images externally)
- No multilingual support (planned for future release)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built with:

- [Click](https://click.palletsprojects.com/) - CLI framework
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [python-frontmatter](https://github.com/eyeseast/python-frontmatter) - Frontmatter parsing
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) - Markdown rendering
- [PyYAML](https://pyyaml.org/) - YAML parsing
- [Watchdog](https://github.com/gorakhargosh/watchdog) - File watching
- [pytest](https://pytest.org/) - Testing framework
