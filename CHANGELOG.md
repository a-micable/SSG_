# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-03-15

### Added

- Initial release of SSG static site generator
- Markdown content processing with YAML frontmatter
- Jinja2 template engine with custom filters
- Asset processing with optional content-based fingerprinting
- RSS 2.0 feed generation
- XML sitemap generation
- Development server with file watching
- Incremental builds with dependency tracking
- Tag-based content collections
- Date-based content archives
- Pagination support for large content sets
- CLI with `build`, `init`, and `serve` commands
- Comprehensive test suite with 59+ tests
- Type hints throughout codebase
- Docker support
- Complete documentation

### Architecture

- **config.py**: YAML configuration loading with validation
- **parser.py**: Markdown and frontmatter parsing
- **renderer.py**: Jinja2 template rendering
- **builder.py**: Build orchestration and dependency tracking
- **assets.py**: Asset copying and fingerprinting
- **feed.py**: RSS feed generation
- **sitemap.py**: XML sitemap generation
- **watcher.py**: File system watching for development
- **cli.py**: Command-line interface

### Known Issues

This release includes several documented bugs that represent realistic issues that might occur during development. These are intentionally left unfixed for educational purposes:

1. **Date Parsing (BUG 1)**: Dates in frontmatter are stored as strings instead of datetime objects, causing template rendering errors when using strftime filters. Location: `parser.py:_extract_metadata()`

2. **Template Dependency Tracking (BUG 2)**: Changes to base templates may not trigger rebuilds of all dependent content due to incomplete dependency graph traversal. Location: `builder.py:DependencyGraph.get_affected_content()`

3. **Pagination Off-by-One (BUG 3)**: When total posts is exactly divisible by posts_per_page, an extra empty page is created. Location: `builder.py:_generate_pagination()`

4. **RSS Timezone Handling (BUG 4)**: Feed dates are emitted in local time instead of UTC, despite claiming +0000 offset. Location: `feed.py:_format_rfc822_date()`

5. **Asset URL Rewriting (BUG 5)**: Asset URLs work correctly for root-level pages but may break on nested pages due to incorrect relative path handling. Location: `assets.py:rewrite_asset_urls()`

### Dependencies

- Python 3.11+
- click >= 8.1.0
- jinja2 >= 3.1.0
- python-frontmatter >= 1.0.0
- markdown-it-py >= 3.0.0
- pyyaml >= 6.0
- watchdog >= 3.0.0

### Testing

- 59 behavior-based tests covering all major functionality
- Fixtures for realistic test scenarios
- Integration tests for complete builds
- Test coverage for error conditions
- Bug reproduction tests

### Documentation

- **README.md**: Complete user guide
- **ARCHITECTURE.md**: Internal design documentation
- **CONTRIBUTING.md**: Contributor guide
- **LICENSE**: MIT License
- Comprehensive inline code documentation
- Detailed docstrings for all public APIs

## [Unreleased]

### Planned Features

- Syntax highlighting for code blocks
- Image optimization and responsive images
- Search index generation
- Multilingual content support
- Plugin system for extensibility
- Theme packaging and distribution
- Parallel processing for large sites
- Build caching for faster rebuilds

### Planned Bug Fixes

- Fix date parsing to use datetime objects (BUG 1)
- Enhance template dependency tracking (BUG 2)
- Fix pagination off-by-one error (BUG 3)
- Add proper timezone handling for RSS feeds (BUG 4)
- Fix asset URL rewriting for nested pages (BUG 5)

### Planned Improvements

- Performance optimizations for large sites
- Better error messages with suggestions
- Progress indicators for long builds
- Configuration validation with helpful hints
- Template debugging tools
- Content linting and validation
- Broken link detection
- Dead code elimination

---

## Version History

### Version Numbering

SSG follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

### Release Process

1. Update CHANGELOG.md with changes
2. Bump version in pyproject.toml and __init__.py
3. Run full test suite
4. Tag release in git
5. Build and publish to PyPI
6. Update documentation

### Support Policy

- Latest major version receives active development
- Previous major version receives security fixes for 6 months
- Older versions are community-maintained only

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Setting up development environment
- Running tests
- Code style guidelines
- Submitting pull requests
- Reporting bugs
- Requesting features

## Credits

### Core Team

- SSG Contributors

### Dependencies

Built with these excellent open-source projects:

- [Click](https://click.palletsprojects.com/) - CLI framework by Pallets
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine by Pallets
- [python-frontmatter](https://github.com/eyeseast/python-frontmatter) - YAML frontmatter parsing
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) - Markdown rendering
- [PyYAML](https://pyyaml.org/) - YAML parser
- [Watchdog](https://github.com/gorakhargosh/watchdog) - File system events
- [pytest](https://pytest.org/) - Testing framework

### Inspiration

Inspired by:

- Jekyll - Ruby static site generator
- Hugo - Go static site generator  
- Eleventy - JavaScript static site generator
- Pelican - Python static site generator

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 SSG Contributors
