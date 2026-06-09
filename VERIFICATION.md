# Verification Guide

This document provides instructions for verifying the SSG installation, testing functionality, and confirming that all features work as expected.

## Table of Contents

1. [Installation Verification](#installation-verification)
2. [Feature Verification](#feature-verification)
3. [Test Suite Verification](#test-suite-verification)
4. [Build Verification](#build-verification)
5. [Docker Verification](#docker-verification)
6. [Bug Verification](#bug-verification)
7. [Performance Verification](#performance-verification)

## Installation Verification

### Step 1: Check Python Version

```bash
python --version
# Expected: Python 3.11.0 or higher
```

### Step 2: Verify Installation

```bash
ssg --version
# Expected: Version number displayed
```

### Step 3: Check Command Availability

```bash
ssg --help
# Expected: Help message with commands listed

ssg build --help
# Expected: Build command help

ssg init --help
# Expected: Init command help

ssg serve --help
# Expected: Serve command help
```

### Step 4: Verify Dependencies

```bash
pip list | grep -E '(click|jinja2|frontmatter|markdown|pyyaml|watchdog)'
# Expected: All dependencies listed with versions
```

## Feature Verification

### 1. Site Initialization

```bash
# Create test site
ssg init test-site --name "Test Site" --url "http://localhost:8000"

# Expected output:
# - "Initializing site in test-site"
# - "Created content/"
# - "Created templates/"
# - "Created assets/"
# - "Site initialized successfully!"

# Verify structure
ls test-site/
# Expected: config.yml, content/, templates/, assets/

ls test-site/content/posts/
# Expected: welcome.md

ls test-site/templates/
# Expected: base.html, post.html, index.html, tag.html
```

### 2. Configuration Loading

```bash
cd test-site

# Verify config is valid
python -c "
from pathlib import Path
from ssg.config import ConfigLoader
config = ConfigLoader.load(Path('config.yml'))
print(f'Site: {config.site_name}')
print(f'URL: {config.base_url}')
print(f'Posts per page: {config.posts_per_page}')
"

# Expected: Configuration values printed correctly
```

### 3. Content Parsing

```bash
# Test parser
python -c "
from pathlib import Path
from ssg.parser import MarkdownParser
parser = MarkdownParser()
content = parser.parse_directory(Path('content'))
print(f'Found {len(content)} posts')
for post in content:
    print(f'  - {post.title} ({post.date})')
"

# Expected: Posts listed with titles and dates
```

### 4. Build Process

```bash
# Build the site
ssg build

# Expected output:
# - "Loading configuration from config.yml"
# - "Starting site build"
# - "Parsing content..."
# - "Building X pages..."
# - "Processing assets..."
# - "Generating RSS feed..."
# - "Generating sitemap..."
# - "Build complete!"

# Verify output
ls dist/
# Expected: index.html, feed.xml, sitemap.xml, welcome/

ls dist/welcome/
# Expected: index.html

# Check file contents
head dist/index.html
# Expected: Valid HTML with site name

head dist/feed.xml
# Expected: Valid RSS XML with <?xml tag

head dist/sitemap.xml
# Expected: Valid sitemap XML
```

### 5. Development Server

```bash
# Start server
ssg serve --port 8001 &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Test server
curl -s http://localhost:8001/ | grep -q "Test Site"
if [ $? -eq 0 ]; then
    echo "✓ Server is working"
else
    echo "✗ Server test failed"
fi

# Stop server
kill $SERVER_PID

# Expected: "✓ Server is working"
```

### 6. Asset Processing

```bash
# Check assets were copied
ls dist/assets/css/
# Expected: style.css or style.*.css (fingerprinted)

# Verify fingerprinting
python -c "
from pathlib import Path
from ssg.config import ConfigLoader
from ssg.assets import AssetProcessor
config = ConfigLoader.load(Path('config.yml'))
processor = AssetProcessor(config)
processor.process()
print(f'Fingerprinted {len(processor.fingerprint_map)} assets')
for original, fingerprinted in processor.fingerprint_map.items():
    print(f'  {original} -> {fingerprinted}')
"

# Expected: Assets listed with fingerprinted names
```

### 7. Feed Generation

```bash
# Verify feed is valid XML
xmllint --noout dist/feed.xml 2>&1
# Expected: No errors (or "command not found" if xmllint not installed)

# Check feed content
grep -q "<rss version=\"2.0\">" dist/feed.xml && echo "✓ RSS version correct"
grep -q "<title>Test Site</title>" dist/feed.xml && echo "✓ Site title in feed"
grep -q "<item>" dist/feed.xml && echo "✓ Feed items present"
```

### 8. Sitemap Generation

```bash
# Verify sitemap is valid XML
xmllint --noout dist/sitemap.xml 2>&1
# Expected: No errors

# Check sitemap content
grep -q "xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"" dist/sitemap.xml && echo "✓ Sitemap namespace correct"
grep -q "<loc>http://localhost:8000/</loc>" dist/sitemap.xml && echo "✓ Homepage in sitemap"
grep -q "<url>" dist/sitemap.xml && echo "✓ URL entries present"
```

## Test Suite Verification

### Run All Tests

```bash
cd /path/to/SSG

# Run full test suite
pytest

# Expected output:
# - All tests pass
# - 59 tests collected and run
# - No failures or errors
```

### Run with Verbose Output

```bash
pytest -v

# Expected: Detailed test output showing each test result
```

### Run with Coverage

```bash
pytest --cov=ssg --cov-report=term-missing

# Expected:
# - Coverage report showing >80% coverage
# - List of covered and uncovered lines
```

### Run Specific Test Files

```bash
pytest tests/test_parser.py
# Expected: Parser tests pass

pytest tests/test_renderer.py
# Expected: Renderer tests pass

pytest tests/test_builder.py
# Expected: Builder tests pass

pytest tests/test_assets.py
# Expected: Asset tests pass
```

### Run Specific Tests

```bash
pytest tests/test_parser.py::TestMarkdownParser::test_parse_file_basic -v
# Expected: Single test passes with detailed output
```

## Build Verification

### Full Build Test

```bash
# Create test content
mkdir -p test-site/content/posts

# Add multiple posts
for i in {1..10}; do
    cat > test-site/content/posts/post-${i}.md << EOF
---
title: Test Post ${i}
date: 2024-03-$(printf "%02d" $i)
tags:
  - test
  - post-${i}
slug: post-${i}
---

# Post ${i}

This is test post number ${i}.
EOF
done

# Build
cd test-site
ssg build

# Verify all posts built
ls dist/post-*/index.html | wc -l
# Expected: 10 (or 11 with welcome post)

# Verify pagination
ls dist/page/*/index.html 2>/dev/null | wc -l
# Expected: 1 or more (depending on posts_per_page)

# Verify tag pages
ls dist/tags/test/index.html
# Expected: File exists
```

### Incremental Build Test

```bash
# Make a change
echo "\n\nUpdated content" >> content/posts/post-1.md

# Rebuild
ssg build --no-clean

# Verify change reflected
grep -q "Updated content" dist/post-1/index.html
if [ $? -eq 0 ]; then
    echo "✓ Incremental build works"
else
    echo "✗ Incremental build failed"
fi
```

### Draft Build Test

```bash
# Create draft
cat > content/posts/draft.md << EOF
---
title: Draft Post
date: 2024-03-15
draft: true
---

This is a draft.
EOF

# Build without drafts
ssg build --no-clean

# Verify draft not built
if [ ! -f dist/draft/index.html ]; then
    echo "✓ Drafts excluded by default"
else
    echo "✗ Draft was built"
fi

# Build with drafts
ssg build --no-clean --drafts

# Verify draft built
if [ -f dist/draft/index.html ]; then
    echo "✓ Drafts included with --drafts flag"
else
    echo "✗ Draft not built with --drafts"
fi
```

## Docker Verification

### Build Docker Image

```bash
docker build -t ssg .

# Expected: Image builds successfully
```

### Run Tests in Docker

```bash
docker run --rm ssg pytest

# Expected: All tests pass in container
```

### Build Site in Docker

```bash
docker run --rm -v $(pwd)/test-site:/site ssg build

# Expected: Site builds in container
```

### Serve with Docker

```bash
docker run --rm -p 8002:8000 -v $(pwd)/test-site:/site ssg serve &
DOCKER_PID=$!

sleep 3

curl -s http://localhost:8002/ | grep -q "Test Site"
if [ $? -eq 0 ]; then
    echo "✓ Docker serve works"
else
    echo "✗ Docker serve failed"
fi

docker stop $DOCKER_PID
```

## Bug Verification

These bugs are intentional and should be present:

### BUG 1: Date Type Mismatch

```bash
# Create template that uses strftime
cat > test-site/templates/test-bug1.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<p>Date: {{ date | strftime('%B %d, %Y') }}</p>
{% endblock %}
EOF

# This should work due to workaround in renderer
python -c "
from pathlib import Path
from ssg.config import ConfigLoader
from ssg.renderer import Renderer
config = ConfigLoader.load(Path('test-site/config.yml'))
renderer = Renderer(config)
html = renderer.render('test-bug1.html', {'date': '2024-03-15'})
print('✓ BUG 1 workaround works' if 'March 15, 2024' in html else '✗ BUG 1 workaround failed')
"
```

### BUG 2: Dependency Tracking

```python
# Run builder test
pytest tests/test_builder.py::TestDependencyGraph::test_get_affected_content_transitive -v

# Expected: Test passes but demonstrates the bug
```

### BUG 3: Pagination

```python
# Run pagination test
pytest tests/test_builder.py::TestPaginator::test_paginator_exact_division -v

# Expected: Test demonstrates the off-by-one error
```

### BUG 4: RSS Timezone

```bash
# Check feed dates
grep "pubDate" test-site/dist/feed.xml

# Expected: Dates with timezone offset (shows the bug)
```

### BUG 5: Asset Paths

```python
# Run asset test
pytest tests/test_assets.py::TestAssetProcessor::test_rewrite_asset_urls_relative_paths -v

# Expected: Test demonstrates the path resolution bug
```

## Performance Verification

### Build Time

```bash
time ssg build

# Expected: Completes in reasonable time (< 10 seconds for small sites)
```

### Memory Usage

```bash
/usr/bin/time -v ssg build 2>&1 | grep "Maximum resident set size"

# Expected: Reasonable memory usage for site size
```

### File Count Handling

```bash
# Create many files
for i in {1..100}; do
    cat > test-site/content/posts/post-${i}.md << EOF
---
title: Post ${i}
date: 2024-01-01
---
Content ${i}
EOF
done

time ssg build

# Expected: Handles 100+ files without issues
```

## Verification Checklist

Use this checklist to verify all functionality:

- [ ] Installation completes without errors
- [ ] `ssg --version` shows version number
- [ ] `ssg init` creates site structure
- [ ] Config file loads correctly
- [ ] Content parsing finds all files
- [ ] Build process completes successfully
- [ ] Output files generated correctly
- [ ] Assets copied to output
- [ ] RSS feed generated and valid
- [ ] Sitemap generated and valid
- [ ] Development server starts and serves content
- [ ] All 59 tests pass
- [ ] Test coverage >80%
- [ ] Docker image builds
- [ ] Docker tests pass
- [ ] Documentation complete and accessible
- [ ] 5 intentional bugs present and documented

## Troubleshooting

### Issue: Tests Fail

**Solution**:
```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run with verbose output
pytest -v

# Check specific failures
pytest --lf  # Run last failed
```

### Issue: Build Fails

**Solution**:
```bash
# Check config
python -c "from ssg.config import ConfigLoader; ConfigLoader.load('config.yml')"

# Check content directory exists
ls content/

# Check templates exist
ls templates/
```

### Issue: Server Won't Start

**Solution**:
```bash
# Check port availability
lsof -i :8000

# Use different port
ssg serve --port 8001
```

## Success Criteria

All verification steps should:
- ✓ Complete without errors
- ✓ Produce expected output
- ✓ Demonstrate correct behavior
- ✓ Show intentional bugs where expected
- ✓ Pass all automated tests

If any verification step fails unexpectedly, check:
1. Python version (must be 3.11+)
2. All dependencies installed
3. File permissions correct
4. Paths are correct
5. Configuration is valid

## Conclusion

This verification guide ensures that:
- Installation is correct
- All features work as expected
- Tests pass consistently
- Docker integration functions
- Documentation is accurate
- Bugs are present as intended

For issues not covered here, see:
- [README.md](README.md) for general usage
- [ARCHITECTURE.md](ARCHITECTURE.md) for internals
- [CONTRIBUTING.md](CONTRIBUTING.md) for development
- [project issues](/issues) for bug reports
