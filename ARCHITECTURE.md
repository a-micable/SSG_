# Architecture Overview

This document provides a detailed explanation of the SSG architecture, design decisions, and module interactions.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Module Breakdown](#module-breakdown)
3. [Data Flow](#data-flow)
4. [Dependency Management](#dependency-management)
5. [Extension Points](#extension-points)
6. [Known Bugs (Educational)](#known-bugs-educational)

## High-Level Architecture

The SSG follows a **pipeline architecture** with clear stages:

```
Content (Markdown) → Parser → Renderer → Builder → Output (HTML)
                                    ↓
                                 Assets → Fingerprinting → Output
                                    ↓
                              Feed/Sitemap → Output
```

### Design Principles

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Dependency Injection** - Configuration passed to components rather than hard-coded
3. **Immutable Data** - Parsed content represented as immutable dataclasses
4. **Fail-Fast** - Validation errors caught early with clear messages
5. **Testability** - All components designed to be easily tested in isolation

## Module Breakdown

### 1. Configuration (`config.py`)

**Purpose**: Load and validate site configuration from YAML files.

**Key Classes**:
- `SiteConfig` - Dataclass holding all configuration
- `ConfigLoader` - Loads and validates configuration
- `ConfigError` - Configuration-specific exceptions

**Responsibilities**:
- Parse YAML configuration files
- Validate required fields
- Convert relative paths to absolute
- Provide sensible defaults
- Raise clear errors for invalid configuration

**Example**:
```python
config = ConfigLoader.load(Path("config.yml"))
print(config.site_name)
print(config.posts_per_page)
```

### 2. Parser (`parser.py`)

**Purpose**: Convert Markdown files with frontmatter into structured data.

**Key Classes**:
- `ParsedContent` - Dataclass representing parsed content
- `MarkdownParser` - Parses Markdown and extracts metadata
- `ParseError` - Parser-specific exceptions

**Responsibilities**:
- Extract YAML frontmatter from Markdown files
- Parse frontmatter into typed fields
- Convert Markdown to HTML using markdown-it-py
- Handle file discovery in content directories
- Sort content by date

**Known Issue (BUG 1)**:
- Dates stored as strings instead of datetime objects
- Causes template rendering errors with date filters
- Location: `parse_file()` method around line 85

**Example**:
```python
parser = MarkdownParser()
content = parser.parse_file(Path("post.md"))
print(content.title)
print(content.date)  # String, not datetime!
```

### 3. Renderer (`renderer.py`)

**Purpose**: Render parsed content using Jinja2 templates.

**Key Classes**:
- `Renderer` - Jinja2 renderer with custom filters
- `RenderError` - Rendering-specific exceptions

**Responsibilities**:
- Configure Jinja2 environment
- Register custom filters (strftime, excerpt, etc.)
- Provide global functions (url_for, now)
- Render individual content pages
- Render list pages (index, tags)
- Inject site configuration into templates

**Custom Filters**:
- `strftime(date, format)` - Format dates (works around BUG 1)
- `dateformat(date, format)` - Format with config default
- `excerpt(text, length)` - Extract text excerpt
- `limit(items, count)` - Limit list length

**Custom Globals**:
- `now()` - Current datetime
- `url_for(path)` - Generate full URLs

**Example**:
```python
renderer = Renderer(config)
html = renderer.render("post.html", {
    "title": "My Post",
    "content": "<p>Content</p>"
})
```

### 4. Builder (`builder.py`)

**Purpose**: Orchestrate the entire build process.

**Key Classes**:
- `SiteBuilder` - Main builder orchestrator
- `Paginator` - Handles content pagination (BUG 3)
- `DependencyGraph` - Tracks dependencies (BUG 2)
- `BuildError` - Build-specific exceptions

**Responsibilities**:
- Coordinate parser, renderer, and asset processor
- Build individual content pages
- Generate index pages with pagination
- Create tag archive pages
- Trigger feed and sitemap generation
- Track dependencies for incremental builds
- Handle file watching callbacks

**Known Issues**:
- **BUG 2**: Dependency graph doesn't track transitive template dependencies
  - Location: `DependencyGraph.get_affected_content()`
  - Impact: Base template changes don't trigger child template rebuilds
  
- **BUG 3**: Pagination off-by-one error
  - Location: `Paginator.total_pages` property
  - Impact: Extra empty page when items divide evenly

**Build Process**:
1. Parse all content from `content_dir`
2. Build individual content pages
3. Build paginated index pages
4. Build tag archive pages
5. Process assets with fingerprinting
6. Generate RSS feed
7. Generate XML sitemap

**Example**:
```python
builder = SiteBuilder(config)
builder.build(clean=True)
```

### 5. Assets (`assets.py`)

**Purpose**: Process static assets with fingerprinting.

**Key Classes**:
- `AssetProcessor` - Handles asset copying and fingerprinting
- `AssetError` - Asset-specific exceptions

**Responsibilities**:
- Copy asset files to output directory
- Generate content hashes for CSS/JS files
- Create fingerprinted filenames (style.abc123.css)
- Maintain mapping of original → fingerprinted URLs
- Rewrite asset URLs in generated HTML

**Fingerprinting Process**:
1. Compute MD5 hash of file content
2. Generate filename: `{stem}.{hash}{suffix}`
3. Copy file with new name
4. Store mapping: `/style.css` → `/style.abc123.css`

**Known Issue (BUG 5)**:
- Relative asset paths break on nested pages
- Location: `rewrite_asset_urls()` method
- Impact: Assets work on root pages but fail on nested pages

**Example**:
```python
processor = AssetProcessor(config)
processor.process()
print(processor.fingerprint_map)
# {'/style.css': '/style.abc123.css'}
```

### 6. Feed (`feed.py`)

**Purpose**: Generate RSS 2.0 feeds for blog posts.

**Key Classes**:
- `FeedGenerator` - Generates RSS XML
- `FeedError` - Feed-specific exceptions

**Responsibilities**:
- Create RSS 2.0 compliant XML
- Format dates as RFC 822
- Include post metadata (title, link, description)
- Generate channel metadata
- Limit feed to most recent posts

**Known Issue (BUG 4)**:
- Dates emitted in local timezone instead of UTC/GMT
- Location: `_format_rfc822_date()` method
- Impact: Feed validators may fail or show wrong times

**Example**:
```python
generator = FeedGenerator(config)
generator.generate(parsed_content, max_items=20)
# Creates: output_dir/feed.xml
```

### 7. Sitemap (`sitemap.py`)

**Purpose**: Generate XML sitemaps for SEO.

**Key Classes**:
- `SitemapGenerator` - Generates sitemap XML
- `SitemapError` - Sitemap-specific exceptions

**Responsibilities**:
- Create sitemap XML with proper namespace
- Include all public pages
- Format dates as W3C datetime
- Set appropriate priority values
- Include homepage and content pages

**Example**:
```python
generator = SitemapGenerator(config)
generator.generate(parsed_content)
# Creates: output_dir/sitemap.xml
```

### 8. Watcher (`watcher.py`)

**Purpose**: Watch files and trigger rebuilds during development.

**Key Classes**:
- `FileWatcher` - Watches directories for changes
- `ChangeHandler` - Handles file system events
- `WatcherError` - Watcher-specific exceptions

**Responsibilities**:
- Monitor content, template, and asset directories
- Debounce rapid successive changes
- Filter out temporary and hidden files
- Invoke callback with list of changed files
- Handle graceful shutdown

**Example**:
```python
def on_change(files):
    print(f"Changed: {files}")
    builder.rebuild_changed(files)

watcher = FileWatcher(on_change)
watcher.watch(content_dir)
watcher.run()  # Blocks until Ctrl+C
```

### 9. CLI (`cli.py`)

**Purpose**: Provide command-line interface.

**Commands**:
- `ssg build` - Build the entire site
- `ssg init` - Initialize new site structure
- `ssg serve` - Development server with live reload

**Responsibilities**:
- Parse command-line arguments with Click
- Load configuration
- Execute build process
- Start development server
- Handle errors with user-friendly messages

**Example**:
```bash
ssg build --config site/config.yml
ssg serve --port 3000 --watch
```

## Data Flow

### Build Process Flow

```
1. Load Configuration
   ↓
2. Parse Content Files
   - Read Markdown files
   - Extract frontmatter
   - Convert to HTML
   - Create ParsedContent objects
   ↓
3. Render Pages
   - Load Jinja2 templates
   - Inject content + site context
   - Generate HTML for each page
   ↓
4. Build Collections
   - Create paginated index
   - Group by tags
   - Render list pages
   ↓
5. Process Assets
   - Copy static files
   - Fingerprint CSS/JS
   - Update URL mappings
   ↓
6. Generate Metadata
   - Create RSS feed
   - Create XML sitemap
   ↓
7. Write Output
   - Save all files to output_dir
```

### Incremental Build Flow

```
1. File Change Detected
   ↓
2. Identify Changed Files
   ↓
3. Check Dependency Graph
   - Content changed? → Rebuild that page
   - Template changed? → Rebuild dependent pages
   ↓
4. Execute Partial Rebuild
   - Parse changed content
   - Re-render affected pages
   - Update outputs
```

## Dependency Management

### Content Dependencies

Content files depend on:
- Their designated layout template
- Base templates (through inheritance)
- Partials/includes referenced in templates

### Template Dependencies

Templates depend on:
- Parent templates (via `extends`)
- Included templates (via `include`)
- Imported macros (via `import`)

### Asset Dependencies

Generated HTML depends on:
- Asset files (CSS, JS, images)
- Fingerprint mappings

### Tracking Strategy

The `DependencyGraph` tracks:
- **Content → Templates**: Which templates does each content file use?
- **Template → Content**: Which content uses each template?
- **Template → Template**: Which templates include other templates?

## Extension Points

### Adding Custom Filters

```python
# In renderer.py
def _filter_custom(self, value):
    return value.upper()

# Register in __init__
self.env.filters['custom'] = self._filter_custom
```

### Adding Custom Commands

```python
# In cli.py
@cli.command()
@click.option('--option')
def custom(option):
    """Custom command."""
    # Implementation
```

### Supporting New Content Types

```python
# Create new parser in parser.py
class CustomParser:
    def parse_file(self, path):
        # Parse custom format
        return ParsedContent(...)
```

## Known Bugs (Educational)

These bugs are intentionally included for educational purposes:

### BUG 1: Date Type Mismatch
**Location**: `parser.py`, line ~85
**Symptom**: Template errors when using date filters
**Cause**: Dates stored as strings instead of datetime objects
**Fix**: Parse dates to datetime in parser

### BUG 2: Incomplete Dependency Tracking
**Location**: `builder.py`, `DependencyGraph.get_affected_content()`
**Symptom**: Changes to base templates don't trigger rebuilds
**Cause**: Transitive dependencies not tracked
**Fix**: Recursively traverse template includes

### BUG 3: Pagination Off-By-One
**Location**: `builder.py`, `Paginator.total_pages`
**Symptom**: Extra empty page when items divide evenly
**Cause**: Adds 1 in both branches of conditional
**Fix**: Remove extra +1 in else branch

### BUG 4: RSS Timezone Issues
**Location**: `feed.py`, `_format_rfc822_date()`
**Symptom**: Feed dates in local time, not UTC
**Cause**: Using local strftime without timezone conversion
**Fix**: Convert to UTC before formatting

### BUG 5: Asset Path Resolution
**Location**: `assets.py`, `rewrite_asset_urls()`
**Symptom**: Asset links break on nested pages
**Cause**: Doesn't account for page depth in URL generation
**Fix**: Convert relative paths to absolute paths

## Performance Considerations

### Optimization Strategies

1. **Incremental Builds** - Only rebuild changed files
2. **Dependency Tracking** - Minimize unnecessary rebuilds
3. **Asset Fingerprinting** - Enable aggressive browser caching
4. **File Debouncing** - Batch rapid file changes

### Scalability Limits

- **Content Volume**: Tested with 1000+ posts
- **Asset Size**: Fingerprinting works on files up to ~10MB
- **Template Complexity**: No practical limit on template nesting

## Testing Strategy

### Test Organization

- `test_config.py` - Configuration loading and validation
- `test_parser.py` - Markdown parsing and frontmatter
- `test_renderer.py` - Template rendering
- `test_builder.py` - Build orchestration and pagination
- `test_assets.py` - Asset processing

### Test Philosophy

- **Behavior-based**: Test what the code does, not how
- **Integration-focused**: Test module interactions
- **Fixture-driven**: Use realistic test data
- **Bug-documenting**: Tests demonstrate known bugs

## Future Enhancements

Potential improvements (left as exercises):

1. Fix the 5 intentional bugs
2. Add plugin system for extensibility
3. Implement syntax highlighting configuration
4. Add image optimization pipeline
5. Support multiple content types (JSON, TOML)
6. Add search index generation
7. Implement draft preview server
8. Add content validation hooks
9. Support internationalization (i18n)
10. Add analytics integration

## Conclusion

The SSG architecture prioritizes:
- **Clarity** over cleverness
- **Modularity** over monoliths
- **Testability** over shortcuts
- **Real-world patterns** over academic purity

This makes it an excellent codebase for learning, debugging practice, and understanding how static site generators work under the hood.
