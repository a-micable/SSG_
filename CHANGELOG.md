# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `PROJECT_TYPE` (`cli-tool`) and classification docs; optional Docker Compose CLI sandbox (no databases, not IaC).
- Structured logging (`LOGGING_FRAMEWORK`), in-process error tracking, runtime metrics, and `ssg health` JSON.
- Named `input_validation_*` / `schema_validation_*` helpers wired into config load and the CLI.
- Behavioral pytest modules that shell out to `ssg init` / `ssg build` and compare two dist trees.
- CI jobs `test`, `lint`, `typecheck`, `coverage` with a 70% line-coverage gate and hashed `ci/requirements-ci.txt`.

### Fixed
- Frontmatter `datetime.date` values are normalized to ISO strings before RSS generation.
- Paginator page count no longer adds an extra empty page when items divide evenly.
- Asset directories from YAML strings are coerced to `Path` before processing.

### Known Issues
- Date parsing stores dates as strings (BUG 1)
- Template dependency tracking incomplete (BUG 2)
- Pagination off-by-one error (BUG 3)
- RSS timezone handling uses local time (BUG 4)
- Asset path resolution breaks on nested pages (BUG 5)

## [1.0.0] - 2024-03-15

### Added
- Complete CLI with `build`, `init`, and `serve` commands
- Markdown parsing with frontmatter support
- Jinja2 template rendering with custom filters
- Asset pipeline with fingerprinting
- RSS 2.0 feed generation
- XML sitemap generation
- File watching for development mode
- Pagination for content lists
- Tag-based content organization
- Comprehensive test suite with pytest
- Docker support
- Full documentation (README, ARCHITECTURE, CONTRIBUTING, QUICKSTART)

### Core Features
- **Parser Module** - Markdown to HTML with metadata extraction
- **Renderer Module** - Jinja2 templating with custom filters
- **Builder Module** - Build orchestration with dependency tracking
- **Assets Module** - Static file processing with fingerprinting
- **Feed Module** - RSS 2.0 generation
- **Sitemap Module** - XML sitemap generation
- **Watcher Module** - File monitoring for live reload
- **Config Module** - YAML configuration with validation
- **CLI Module** - Command-line interface with Click

### Custom Template Filters
- `strftime` - Date formatting
- `dateformat` - Date formatting with config defaults
- `excerpt` - Text excerpt extraction
- `limit` - List limiting
- `url_for` - Full URL generation

### Commands
- `ssg build` - Build entire site
  - Options: `--config`, `--clean/--no-clean`, `--drafts`
- `ssg init` - Initialize new site structure
  - Options: `--name`, `--url`
- `ssg serve` - Development server with live reload
  - Options: `--config`, `--port`, `--watch/--no-watch`

### Configuration Options
- `site_name` - Site name (required)
- `base_url` - Site base URL (required)
- `content_dir` - Content directory path
- `template_dir` - Templates directory path
- `output_dir` - Output directory path
- `posts_per_page` - Items per paginated page
- `date_format` - Date formatting string
- `timezone` - Site timezone
- `asset_dirs` - Asset directories list
- `build_drafts` - Include drafts in build
- `feed_enabled` - Enable RSS feed generation
- `sitemap_enabled` - Enable sitemap generation
- `author` - Default author name
- `description` - Site description
- `language` - Site language code

### Testing
- 59 test cases across 6 test files
- Pytest-based test suite
- Fixtures for test site generation
- Coverage for all core modules
- Bug demonstration tests

### Documentation
- README with quick start guide
- ARCHITECTURE with detailed design docs
- CONTRIBUTING with development guidelines
- QUICKSTART with 5-minute tutorial
- CHANGELOG with version history
- Docker documentation
- Inline code documentation with docstrings

### Dependencies
- Python 3.11+
- Click 8.1+
- Jinja2 3.1+
- python-frontmatter 1.0+
- markdown 3.5+
- PyYAML 6.0+
- Watchdog 3.0+
- pytest 7.4+ (dev)

### Project Structure
```
ssg/
├── __init__.py       # Package initialization
├── cli.py           # Command-line interface
├── config.py        # Configuration management
├── parser.py        # Markdown parsing
├── renderer.py      # Template rendering
├── builder.py       # Build orchestration
├── assets.py        # Asset processing
├── feed.py          # RSS generation
├── sitemap.py       # Sitemap generation
└── watcher.py       # File watching

tests/
├── conftest.py      # Test fixtures
├── test_config.py   # Config tests
├── test_parser.py   # Parser tests
├── test_renderer.py # Renderer tests
├── test_builder.py  # Builder tests
└── test_assets.py   # Asset tests
```

## Development History

This project was developed incrementally over several months (December 2025 - June 2026) with focus on:

1. **Initial Setup** - Project structure, configuration system
2. **Core Parsing** - Markdown and frontmatter support
3. **Template System** - Jinja2 integration with custom filters
4. **Build System** - Orchestration and dependency tracking
5. **Asset Pipeline** - Copying and fingerprinting
6. **Feed/Sitemap** - Metadata generation
7. **File Watching** - Development mode support
8. **CLI Interface** - User-friendly commands
9. **Testing** - Comprehensive test coverage
10. **Documentation** - Complete user and developer docs
11. **Docker Support** - Containerization
12. **Polish** - Bug fixes, refinements, final testing

## Educational Bugs

This project intentionally includes 5 realistic bugs for educational purposes:

1. **Date Type Bug** - Dates stored as strings causing template errors
2. **Dependency Tracking Bug** - Template changes don't trigger all rebuilds
3. **Pagination Bug** - Off-by-one error creating empty pages
4. **Timezone Bug** - RSS feeds use local time instead of UTC
5. **Asset Path Bug** - Fingerprinted assets break on nested pages

These bugs demonstrate common issues in real-world software development and provide excellent debugging exercises.

## Version History

- **1.0.0** (2024-03-15) - Initial production release
  - Complete feature set
  - Full test coverage
  - Comprehensive documentation

## Migration Guide

### From Unversioned to 1.0.0

This is the first versioned release. No migration needed.

## Acknowledgments

Built with inspiration from:
- Jekyll
- Hugo  
- Eleventy
- Pelican

Special thanks to the Python community and all the open-source libraries that made this possible.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Links

- **Repository**: 
- **Issues**: /issues
- **Discussions**: /discussions

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) guidelines.

Types of changes:
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
