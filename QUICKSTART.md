# SSG Quick Start Guide

Get up and running with SSG in under 5 minutes.

## Installation

```bash
pip install -e .
```

## Create Your First Site

```bash
# Initialize a new site
ssg init mysite
cd mysite

# Build the site
ssg build

# Start the development server
ssg serve
```

Visit http://localhost:8000 to see your site!

## Project Structure

```
mysite/
├── config.yaml          # Site configuration
├── content/             # Your Markdown files
│   ├── hello-world.md
│   └── about.md
├── templates/           # Jinja2 templates
│   ├── base.html       # Base template
│   ├── default.html    # Content template
│   └── index.html      # Index/archive template
├── assets/              # Static files
│   └── css/
│       └── style.css
└── dist/                # Generated site (after build)
```

## Writing Content

Create a new Markdown file in `content/`:

```markdown
---
title: My First Post
date: 2024-03-15
tags:
  - python
  - web
description: An introduction to my blog
---

# Welcome

Your content here in **Markdown**!

## Features

- Lists
- **Bold** and *italic*
- [Links](https://example.com)
- Code blocks
- And more!
```

## Configuration

Edit `config.yaml`:

```yaml
site_name: My Awesome Blog
base_url: https://myblog.com
content_dir: content
template_dir: templates
output_dir: dist
posts_per_page: 10
author: Your Name
description: A blog about awesome things
```

## Common Tasks

### Add a New Post

```bash
# Create a new file
cat > content/my-new-post.md << 'EOF'
---
title: My New Post
date: 2024-03-20
tags: [python, tutorial]
---

# My New Post

Content goes here!
EOF

# Rebuild
ssg build
```

### Customize Templates

Edit templates in `templates/`:

- `base.html` - Site-wide layout
- `default.html` - Individual page layout
- `index.html` - Home page / archive pages

Templates use Jinja2:

```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>{{ page.title }} - {{ site.name }}</title>
</head>
<body>
    <h1>{{ page.title }}</h1>
    {{ content | safe }}
</body>
</html>
```

### Add Custom Styles

Edit `assets/css/style.css`:

```css
body {
    font-family: Georgia, serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: #2c3e50;
}
```

### Deploy Your Site

The `dist/` directory contains your complete static site. Deploy it to:

**Netlify:**
```bash
# Drag and drop the dist/ folder to netlify.com
```

**GitHub Pages:**
```bash
git add dist/
git commit -m "Build site"
git subtree push --prefix dist origin gh-pages
```

**Any Web Server:**
```bash
rsync -avz dist/ user@server:/var/www/html/
```

## Development Workflow

### Live Reload Development

```bash
ssg serve
# Edit files in content/ or templates/
# Browser automatically reloads
```

### Build Options

```bash
# Clean build
ssg build

# Keep existing files
ssg build --no-clean

# Disable asset fingerprinting
ssg build --no-fingerprint

# Custom config
ssg build --config custom.yaml
```

### Serve Options

```bash
# Default (port 8000 with watch)
ssg serve

# Custom port
ssg serve --port 3000

# Without auto-reload
ssg serve --no-watch
```

## Template Variables

### Site Variables

```jinja2
{{ site.name }}          # Site name from config
{{ site.base_url }}      # Base URL
{{ site.author }}        # Default author
{{ site.description }}   # Site description
```

### Page Variables

```jinja2
{{ page.title }}         # Page title
{{ page.date }}          # Publication date
{{ page.tags }}          # List of tags
{{ page.author }}        # Page author
{{ page.description }}   # Page description
{{ page.url }}           # Page URL
```

### Content

```jinja2
{{ content | safe }}     # Rendered HTML
```

### Collections

```jinja2
{% for post in collections.all_posts %}
    <h2>{{ post.metadata.title }}</h2>
{% endfor %}

{% for tag, posts in collections.tags.items() %}
    <h3>{{ tag }}</h3>
    {% for post in posts %}
        {{ post.metadata.title }}
    {% endfor %}
{% endfor %}
```

## Tips & Tricks

### Custom URLs

Use the `slug` field to customize URLs:

```yaml
---
title: My Post
slug: custom-url
---
```

Result: `/custom-url/` instead of `/my-post/`

### Draft Posts

Mark posts as drafts to exclude from builds:

```yaml
---
title: Work in Progress
draft: true
---
```

### Date Formatting

Format dates in templates:

```jinja2
{{ page.date | strftime('%B %d, %Y') }}
# Note: This will fail with BUG 1 until fixed
```

### Absolute URLs

Convert paths to absolute URLs:

```jinja2
<link rel="stylesheet" href="{{ '/style.css' | url }}">
# Outputs: https://yourdomain.com/style.css
```

### Template Inheritance

Create reusable layouts:

**base.html:**
```jinja2
<!DOCTYPE html>
<html>
<head>
    {% block head %}
    <title>{{ site.name }}</title>
    {% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

**post.html:**
```jinja2
{% extends "base.html" %}

{% block head %}
<title>{{ page.title }} - {{ site.name }}</title>
{% endblock %}

{% block content %}
<article>
    <h1>{{ page.title }}</h1>
    {{ content | safe }}
</article>
{% endblock %}
```

## Troubleshooting

### Build Fails

```bash
# Enable verbose logging
ssg build --verbose

# Check configuration
cat config.yaml

# Verify paths exist
ls content/
ls templates/
```

### Content Not Appearing

- Check for `draft: true` in frontmatter
- Ensure file ends with `.md`
- Verify file is in `content_dir`
- Don't start filename with `_`

### Template Errors

- Check template syntax
- Verify template file exists
- Check `layout` field in frontmatter
- Look for undefined variables

### Asset Links Broken

- Verify assets are in correct directory
- Use absolute paths: `/assets/style.css`
- Check `base_url` in config
- Try without fingerprinting: `--no-fingerprint`

## Next Steps

- Read the full [README.md](README.md)
- Explore [ARCHITECTURE.md](ARCHITECTURE.md)
- Check [CONTRIBUTING.md](CONTRIBUTING.md)
- Browse example sites (coming soon)
- Join the community (coming soon)

## Getting Help

- Check documentation first
- Search existing issues
- Create a new issue with:
  - SSG version
  - Python version
  - Error message
  - Minimal reproduction

## Resources

- **Documentation**: README.md
- **Architecture**: ARCHITECTURE.md  
- **Contributing**: CONTRIBUTING.md
- **Changelog**: CHANGELOG.md
- **License**: LICENSE (MIT)

Happy building! 🚀
