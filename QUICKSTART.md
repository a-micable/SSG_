# Quick Start Guide

Get up and running with SSG in 5 minutes!

## Installation

### Option 1: Install from Source

```bash
git clone .git
cd SSG
pip install -e .
```

### Option 2: Install from PyPI (when available)

```bash
pip install static-site-generator
```

### Verify Installation

```bash
ssg --version
```

## Create Your First Site

### Step 1: Initialize a New Site

```bash
ssg init myblog --name "My Blog" --url "http://localhost:8000"
cd myblog
```

This creates:
```
myblog/
├── config.yml         # Configuration
├── content/          # Your Markdown files
│   └── posts/
│       └── welcome.md
├── templates/        # Jinja2 templates
│   ├── base.html
│   ├── post.html
│   ├── index.html
│   └── tag.html
└── assets/          # CSS, JS, images
    ├── css/
    │   └── style.css
    ├── js/
    └── images/
```

### Step 2: Build Your Site

```bash
ssg build
```

Output goes to `dist/` directory.

### Step 3: Preview Your Site

```bash
ssg serve
```

Visit http://localhost:8000

## Write Your First Post

### Create a New Post

Create `content/posts/my-first-post.md`:

```markdown
---
title: My First Post
date: 2024-03-15
tags:
  - tutorial
  - getting-started
slug: my-first-post
layout: post.html
draft: false
---

# Welcome to My Blog!

This is my first post using SSG.

## What I'm Learning

- Markdown syntax
- Frontmatter configuration
- Template customization

Check out more at [example.com](https://example.com).
```

### Rebuild

```bash
ssg build
```

Your new post appears at `http://localhost:8000/my-first-post/`

## Customize Your Site

### Edit Configuration

Edit `config.yml`:

```yaml
site_name: My Awesome Blog
base_url: https://myblog.com
author: Your Name
description: A blog about cool stuff

posts_per_page: 5
date_format: "%B %d, %Y"
```

### Customize Templates

Edit `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}{{ site.name }}{% endblock %}</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <h1><a href="/">{{ site.name }}</a></h1>
        <p>{{ site.description }}</p>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; {{ now().year }} {{ site.author }}</p>
    </footer>
</body>
</html>
```

### Style Your Site

Edit `assets/css/style.css`:

```css
body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    line-height: 1.6;
}

header {
    border-bottom: 2px solid #333;
    margin-bottom: 40px;
    padding-bottom: 20px;
}

header h1 a {
    color: #333;
    text-decoration: none;
}
```

## Common Tasks

### Add a Draft Post

```markdown
---
title: Work in Progress
draft: true
---

This won't appear in builds unless you use `--drafts`.
```

Build with drafts:
```bash
ssg build --drafts
```

### Add Tags

```markdown
---
title: Tagged Post
tags:
  - python
  - web-dev
  - tutorial
---
```

Tags automatically create archive pages at `/tags/python/`

### Create Custom Pages

Create `content/about.md`:

```markdown
---
title: About Me
slug: about
layout: page.html
---

# About This Blog

Information about me and this blog.
```

Add a page template `templates/page.html`:

```html
{% extends "base.html" %}

{% block content %}
<article>
    <h1>{{ title }}</h1>
    {{ content | safe }}
</article>
{% endblock %}
```

## Development Workflow

### Watch Mode

```bash
ssg serve --watch
```

Changes to content or templates trigger automatic rebuilds.

### Build Without Cleaning

```bash
ssg build --no-clean
```

Faster builds when you haven't changed structure.

### Custom Port

```bash
ssg serve --port 3000
```

## Common Issues

### Issue: Template Not Found

**Problem**: `RenderError: Template not found: post.html`

**Solution**: Check that template exists in `templates/` directory and matches `layout:` in frontmatter.

### Issue: Missing Title Error

**Problem**: `ParseError: Missing required field 'title'`

**Solution**: Add `title:` to your frontmatter:

```yaml
---
title: My Post Title
---
```

### Issue: Site Name Not Showing

**Problem**: Templates show empty site name

**Solution**: Check `config.yml` has `site_name:` field

### Issue: Assets Not Loading

**Problem**: CSS/JS files give 404

**Solution**: Check `asset_dirs` in config.yml points to correct directories

## Next Steps

Now that you have a working site:

1. **Read the full [README](README.md)** for detailed features
2. **Check [ARCHITECTURE.md](ARCHITECTURE.md)** to understand how it works
3. **Explore [CONTRIBUTING.md](CONTRIBUTING.md)** if you want to contribute
4. **Review the test files** to see expected behavior

## Tips and Tricks

### Date Formatting

Use custom date formats in templates:

```html
{{ date | strftime('%B %d, %Y') }}
<!-- Output: March 15, 2024 -->

{{ date | strftime('%Y-%m-%d') }}
<!-- Output: 2024-03-15 -->
```

### Limit Posts on Homepage

```html
{% for post in posts | limit(5) %}
    <!-- Show only 5 posts -->
{% endfor %}
```

### Generate Full URLs

```html
<link rel="canonical" href="{{ url | url_for }}">
<!-- Generates: http://yourdomain.com/post-slug/ -->
```

### Create Excerpts

```html
{{ post.content | excerpt(200) }}
<!-- Shows first 200 characters -->
```

## Deployment

### Static File Hosting

Your built site in `dist/` is ready to deploy to:

- static hosting
- Netlify
- Vercel
- AWS S3
- Any static host

### Simple Deploy Example

```bash
# Build for production
ssg build

# Deploy to any static host
# Example: Copy to server
scp -r dist/* user@server:/var/www/html/

# Example: static hosting
cd dist
git init
git add .
git commit -m "Deploy site"
git push --force git@github.com:username/username.github.io.git main
```

## Docker Usage

### Build Docker Image

```bash
docker build -t ssg .
```

### Build Site with Docker

```bash
docker run --rm -v $(pwd):/site ssg build
```

### Serve with Docker

```bash
docker run --rm -p 8000:8000 -v $(pwd):/site ssg serve
```

## Help

### Command Help

```bash
ssg --help
ssg build --help
ssg init --help
ssg serve --help
```

### Get Support

- Check [README.md](README.md) for detailed docs
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for internals
- Open an [issue](/issues) on GitHub

## What's Next?

You now have a working static site! Explore these features:

- RSS feeds (automatically generated at `/feed.xml`)
- Sitemaps (automatically generated at `/sitemap.xml`)
- Tag archives (automatically at `/tags/{tag}/`)
- Pagination (automatically when posts exceed `posts_per_page`)
- Asset fingerprinting (automatic for CSS/JS)

Happy building! 🚀
