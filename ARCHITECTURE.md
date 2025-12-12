# SSG Architecture

This document describes the internal architecture of the SSG static site generator.

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Type Safety**: Comprehensive type hints throughout for maintainability
3. **Testability**: Behavior-based testing with minimal mocking
4. **Extensibility**: Clear interfaces for adding features
5. **Error Handling**: Custom exceptions with helpful messages

## Module Overview

### `config.py` - Configuration Management

**Responsibility**: Load, validate, and provide access to site configuration.

**Key Classes**:
- `SiteConfig`: Strongly-typed configuration dataclass
- `load_config()`: Loads and validates YAML configuration
- `create_default_config()`: Generates starter configuration

**Design Notes**:
- Uses dataclasses for type safety and validation
- Path resolution relative to config file location
- Custom exceptions for clear error messages
- Validates required fields and data types

### `parser.py` - Content Parsing

**Responsibility**: Parse Markdown files with YAML frontmatter.

**Key Classes**:
- `ContentParser`: Stateless parser for Markdown content
- `ContentMetadata`: Structured frontmatter data
- `ParsedContent`: Complete parsed content with metadata and HTML

**Design Notes**:
- Separates metadata extraction from content rendering
- URL generation logic isolated in `_generate_url_path()`
- Support for custom slugs and automatic path generation
- Extensible custom metadata storage

**Known Issues**:
- **BUG 1**: Date fields stored as strings instead of datetime objects. This is a historical bug that causes template rendering errors when using date filters. The fix requires updating `_extract_metadata()` to parse date strings into datetime objects.

### `renderer.py` - Template Rendering

**Responsibility**: Render content using Jinja2 templates with custom filters.

**Key Classes**:
- `TemplateRenderer`: Manages Jinja2 environment and rendering
- Custom filters: `strftime`, `date`, `url`

**Design Notes**:
- Template dependency tracking for incremental builds
- Site-wide context merging with page-specific context
- Template inheritance and includes support
- Custom filters for common operations

**Known Issues**:
- **BUG 1 Symptom**: The `strftime` filter will fail when receiving string dates from the parser. This is where the bug manifests, but the root cause is in `parser.py`.

### `builder.py` - Build Orchestration

**Responsibility**: Coordinate the entire build process.

**Key Classes**:
- `SiteBuilder`: Main build orchestrator
- `DependencyGraph`: Tracks template and content dependencies

**Build Process**:
1. Parse all content files
2. Build collections (tags, archives)
3. Render all content with templates
4. Generate paginated index pages
5. Process static assets
6. Rewrite asset URLs in HTML
7. Generate RSS feed
8. Generate XML sitemap

**Design Notes**:
- Dependency graph enables incremental builds
- Collection building is extensible
- Clean separation between full and incremental builds

**Known Issues**:
- **BUG 2**: Template dependency tracking may not fully traverse inheritance chains. When a base template changes, derived templates are found, but content using those templates may not be marked for rebuild. Fix requires enhancing `DependencyGraph.get_affected_content()` to recursively traverse template dependencies.
- **BUG 3**: Pagination off-by-one error when `total_posts % posts_per_page == 0`. The calculation in `_generate_pagination()` creates an extra empty page. Fix: Check if `page_posts` is empty before rendering.

### `assets.py` - Asset Processing

**Responsibility**: Copy and fingerprint static assets.

**Key Classes**:
- `AssetProcessor`: Processes static assets with optional fingerprinting

**Features**:
- Content-based fingerprinting using SHA-256
- Asset URL mapping for HTML rewriting
- Support for various asset types (CSS, JS, images, fonts)

**Design Notes**:
- Deterministic fingerprinting for consistent builds
- Asset map tracks original → fingerprinted URL mappings
- Separate processing from URL rewriting for flexibility

**Known Issues**:
- **BUG 5**: Asset URL rewriting doesn't properly handle nested pages. Root pages work correctly, but nested pages (e.g., `/blog/post/`) may get incorrect relative paths. The `rewrite_asset_urls()` method should convert all asset references to absolute paths from root, not relative paths. Fix: Always use absolute paths starting with `/` for asset references.

### `feed.py` - RSS Feed Generation

**Responsibility**: Generate standards-compliant RSS 2.0 feeds.

**Key Classes**:
- `FeedGenerator`: Creates RSS XML from content

**Design Notes**:
- RSS 2.0 specification compliance
- XML generation using ElementTree
- Configurable item limits

**Known Issues**:
- **BUG 4**: Timezone handling is incorrect. The `_format_rfc822_date()` method claims dates are in UTC (using `+0000`) but doesn't actually convert dates to UTC. Dates are emitted in local system time, which fails feed validators. Fix: Parse dates with timezone awareness and convert to UTC before formatting.

### `sitemap.py` - Sitemap Generation

**Responsibility**: Generate XML sitemaps for SEO.

**Key Classes**:
- `SitemapGenerator`: Creates sitemap XML from content

**Design Notes**:
- Sitemap protocol compliance
- Includes change frequency and priority hints
- Date formatting in ISO 8601

### `watcher.py` - File Watching

**Responsibility**: Monitor file changes for development mode.

**Key Classes**:
- `SiteWatcher`: File system event handler
- `watch_site()`: Main watching loop

**Design Notes**:
- Debouncing to prevent excessive rebuilds
- Filters relevant file types
- Triggers incremental builds on changes

### `cli.py` - Command Line Interface

**Responsibility**: Provide user-facing commands.

**Commands**:
- `build`: Full site build
- `init`: Create new site structure
- `serve`: Development server with live reload

**Design Notes**:
- Click framework for CLI
- Comprehensive help messages
- Sensible defaults with override options

## Data Flow

### Full Build Flow

```
config.yaml
    ↓
SiteConfig → SiteBuilder
    ↓
ContentParser → ParsedContent[]
    ↓
Collections (tags, archives)
    ↓
TemplateRenderer → HTML files
    ↓
AssetProcessor → Fingerprinted assets
    ↓
URL Rewriting → Final HTML
    ↓
FeedGenerator → RSS feed
    ↓
SitemapGenerator → Sitemap
    ↓
Output directory
```

### Incremental Build Flow

```
Changed files
    ↓
DependencyGraph → Affected content
    ↓
Parse changed content
    ↓
Render affected pages
    ↓
Output directory
```

## Dependency Management

### Content Dependencies

- Content files depend on their specified templates
- Changes to content only require rebuilding that content

### Template Dependencies

- Templates can extend other templates (inheritance)
- Templates can include other templates (composition)
- Changes to templates require rebuilding all dependent content

**Current Limitation**: BUG 2 means that deep template inheritance chains may not fully invalidate. For example:

```
base.html (changed)
    ↓ extends
post.html
    ↓ used by
article.md
```

When `base.html` changes, `article.md` should rebuild, but the current implementation may miss this.

## Error Handling

### Exception Hierarchy

```
SSGError (base)
    ├── ConfigurationError
    ├── ParsingError
    ├── RenderingError
    └── BuildError
```

### Error Propagation

- Low-level modules raise specific exceptions
- CLI catches exceptions and displays user-friendly messages
- Logging provides debugging information

## Testing Strategy

### Test Organization

- `conftest.py`: Shared fixtures
- One test file per module
- Fixtures provide realistic test data

### Testing Approach

1. **Behavior-based**: Test public APIs and observable behavior
2. **Fixture-driven**: Use real files and directories, not mocks
3. **Integration-friendly**: Tests exercise multiple components together
4. **Bug documentation**: Tests document known bugs for future fixes

### Example Test Pattern

```python
def test_full_site_build(sample_site: Path):
    """Test building a complete site."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    builder.build()
    
    # Verify observable outputs
    assert (config.output_dir / "index.html").exists()
    assert (config.output_dir / "rss.xml").exists()
```

## Extension Points

### Adding Custom Filters

Edit `renderer.py`:

```python
def _register_filters(self) -> None:
    self.env.filters["custom"] = self._filter_custom

def _filter_custom(self, value: str) -> str:
    return value.upper()
```

### Adding New Collections

Edit `builder.py` in `_build_collections()`:

```python
# Custom collection logic
custom = {}
for content in self.all_content:
    # Organization logic
    pass

self.collections["custom"] = custom
```

### Adding Custom Content Fields

Extend `ContentMetadata` in `parser.py`:

```python
@dataclass
class ContentMetadata:
    # ... existing fields ...
    custom_field: Optional[str] = None
```

Update `_extract_metadata()` to parse the new field.

## Performance Considerations

### Build Performance

- **Content parsing**: O(n) where n = number of content files
- **Template rendering**: O(n × m) where m = template complexity
- **Asset processing**: O(a) where a = number of assets
- **URL rewriting**: O(n × a) for all HTML files and assets

### Incremental Builds

Incremental builds are O(c) where c = number of changed files, plus their dependencies.

**Optimization opportunities**:
- Parallel rendering of independent pages
- Asset fingerprint caching
- Template compilation caching

### Memory Usage

The builder loads all content into memory, which is acceptable for sites with <10,000 pages. For larger sites, streaming processing would be needed.

## Security Considerations

### Path Traversal

- All paths are resolved relative to configured directories
- Output paths are validated to prevent writing outside output directory

### Template Injection

- Jinja2 autoescape is enabled by default
- User content is marked safe only after Markdown rendering

### Asset Processing

- Assets are copied, not executed
- Binary files are handled safely

## Future Enhancements

### Planned Features

1. **Plugin System**: Allow third-party extensions
2. **Themes**: Packaged template collections
3. **Image Optimization**: Automatic image resizing and compression
4. **Syntax Highlighting**: Built-in code syntax highlighting
5. **Search Index**: Generate client-side search index
6. **Multilingual**: Support for multiple languages
7. **Performance**: Parallel processing for large sites

### Architectural Changes

1. **Plugin Architecture**: Registry-based plugin system
2. **Event System**: Hooks for build lifecycle events
3. **Caching Layer**: Persistent cache for faster rebuilds
4. **Streaming Processing**: Handle large sites without loading everything into memory

## Debugging

### Logging

Enable verbose logging:

```bash
ssg build --verbose
```

### Common Issues

1. **Templates not found**: Check `template_dir` in config
2. **Content not appearing**: Check for `draft: true` in frontmatter
3. **Asset links broken**: Verify asset paths are relative to asset directory
4. **Date formatting errors**: BUG 1 - dates stored as strings

### Debug Checklist

1. Verify configuration is valid
2. Check file paths are correct
3. Review logs for specific errors
4. Test with minimal example site
5. Check permissions on output directory

## Contributing

When contributing, please:

1. Maintain existing architectural patterns
2. Add type hints to all new code
3. Write tests for new functionality
4. Update this document for significant changes
5. Follow existing code style
