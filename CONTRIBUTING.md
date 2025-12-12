# Contributing to SSG

Thank you for your interest in contributing to SSG! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something useful together.

## Getting Started

### Development Setup

1. **Fork and Clone**

```bash
git clone https://github.com/yourusername/ssg.git
cd ssg
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Development Dependencies**

```bash
pip install -e ".[dev]"
```

4. **Verify Installation**

```bash
# Run tests
pytest

# Check types
mypy ssg/

# Format code
black --check ssg/ tests/

# Lint
ruff check ssg/ tests/
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 2. Make Changes

- Write code following our style guide (see below)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_builder.py

# Run with coverage
pytest --cov=ssg --cov-report=html

# Run specific test
pytest tests/test_builder.py::test_full_site_build
```

### 4. Check Code Quality

```bash
# Format code
black ssg/ tests/

# Check types
mypy ssg/

# Lint
ruff check ssg/ tests/

# Fix auto-fixable lint issues
ruff check --fix ssg/ tests/
```

### 5. Commit Changes

Write clear commit messages:

```
Add pagination support for tag archives

- Implement tag-specific pagination
- Add tests for tag pagination
- Update documentation

Fixes #123
```

### 6. Push and Create PR

```bash
git push origin feature/my-feature
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots for UI changes
- Test results

## Code Style

### Python Style

We follow PEP 8 with these specifics:

- **Line length**: 100 characters
- **Quotes**: Use double quotes for strings
- **Imports**: Organize as stdlib, third-party, local
- **Type hints**: Required for all functions
- **Docstrings**: Required for public APIs

### Example

```python
"""Module docstring explaining purpose."""

import logging
from pathlib import Path
from typing import List, Optional

from third_party import SomeClass

from ssg import SSGError

logger = logging.getLogger(__name__)


class MyClass:
    """
    Class docstring explaining what this class does.
    
    Attributes:
        name: Description of name attribute
        value: Description of value attribute
    """
    
    def __init__(self, name: str, value: int) -> None:
        """
        Initialize MyClass.
        
        Args:
            name: The name to use
            value: The initial value
        """
        self.name = name
        self.value = value
    
    def process(self, data: List[str]) -> Optional[str]:
        """
        Process data and return result.
        
        Args:
            data: List of strings to process
            
        Returns:
            Processed result, or None if empty
            
        Raises:
            SSGError: If processing fails
        """
        if not data:
            return None
        
        try:
            result = " ".join(data)
            logger.debug(f"Processed {len(data)} items")
            return result
        except Exception as e:
            raise SSGError(f"Processing failed: {e}")
```

## Testing Guidelines

### Test Structure

- One test file per module: `test_<module>.py`
- Descriptive test names: `test_<what>_<scenario>`
- Use fixtures from `conftest.py`
- Test behavior, not implementation

### Test Example

```python
def test_parse_markdown_with_frontmatter(sample_markdown_file: Path, temp_dir: Path):
    """Test parsing a Markdown file with frontmatter."""
    parser = ContentParser()
    parsed = parser.parse_file(sample_markdown_file, temp_dir)
    
    # Test observable behavior
    assert parsed.metadata.title == "Test Post"
    assert "<h1>Test Content</h1>" in parsed.html
```

### What to Test

✅ **Do Test**:
- Public API behavior
- Error conditions
- Edge cases
- Integration between modules
- Generated output

❌ **Don't Test**:
- Private methods directly
- Implementation details
- Third-party libraries

### Fixtures

Use fixtures for common test data:

```python
@pytest.fixture
def sample_site(temp_dir: Path) -> Path:
    """Create a complete sample site structure."""
    # Setup code
    return temp_dir
```

## Documentation

### When to Update Docs

- Adding new features → Update README.md
- Changing architecture → Update ARCHITECTURE.md
- Changing config options → Update README.md
- Adding dependencies → Update requirements

### Documentation Style

- Clear, concise explanations
- Code examples for features
- Link to related documentation
- Keep examples up-to-date

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted (black)
- [ ] No type errors (mypy)
- [ ] No lint errors (ruff)
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Related Issues
Fixes #123
Related to #456

## Screenshots
If applicable
```

### Review Process

1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Address feedback
4. Approval and merge

## Bug Reports

### Good Bug Reports Include

1. **Description**: What happened vs what you expected
2. **Reproduction**: Minimal steps to reproduce
3. **Environment**: Python version, OS, SSG version
4. **Logs**: Relevant error messages
5. **Example**: Minimal example site if possible

### Bug Report Template

```markdown
## Description
Brief description of the bug

## To Reproduce
1. Create site with...
2. Run command...
3. Observe error...

## Expected Behavior
What should happen

## Actual Behavior
What actually happened

## Environment
- SSG version: 0.1.0
- Python version: 3.11.5
- OS: Ubuntu 22.04

## Error Output
```
Error logs here
```

## Additional Context
Any other relevant information
```

## Feature Requests

### Good Feature Requests Include

1. **Use Case**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Examples**: Similar features in other tools

### Feature Request Template

```markdown
## Problem
Description of the problem this solves

## Proposed Solution
How should this feature work?

## Example Usage
```python
# Code example of proposed feature
```

## Alternatives Considered
Other approaches and why this is better

## Additional Context
Any other relevant information
```

## Fixing Known Bugs

We have documented several known bugs for educational purposes. These make excellent first contributions!

### BUG 1: Date Parsing

**Location**: `ssg/parser.py`

**Issue**: Dates stored as strings instead of datetime objects

**Fix**:
```python
# In _extract_metadata()
if date_value:
    # Parse string to datetime
    dt = datetime.strptime(str(date_value), "%Y-%m-%d")
    date = dt
else:
    date = None
```

**Tests to Update**: `tests/test_parser.py`, `tests/test_renderer.py`

### BUG 2: Dependency Tracking

**Location**: `ssg/builder.py`

**Issue**: Template inheritance chains not fully traversed

**Fix**: Enhance `DependencyGraph.get_affected_content()` to recursively find all templates that depend on the changed template.

### BUG 3: Pagination Off-by-One

**Location**: `ssg/builder.py` in `_generate_pagination()`

**Issue**: Extra empty page when posts divide evenly

**Fix**:
```python
for page_num in range(1, total_pages + 1):
    start_idx = (page_num - 1) * posts_per_page
    end_idx = start_idx + posts_per_page
    page_posts = all_posts[start_idx:end_idx]
    
    # Skip empty pages
    if not page_posts:
        continue
    
    # ... rest of rendering
```

### BUG 4: RSS Timezone

**Location**: `ssg/feed.py` in `_format_rfc822_date()`

**Issue**: Dates not converted to UTC

**Fix**: Use timezone-aware datetime and convert to UTC before formatting.

### BUG 5: Asset URL Rewriting

**Location**: `ssg/assets.py` in `rewrite_asset_urls()`

**Issue**: Nested pages get incorrect asset paths

**Fix**: Always use absolute paths from root for all asset references.

## Project Structure

```
ssg/
├── ssg/                  # Main package
│   ├── __init__.py      # Package init and exceptions
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Configuration management
│   ├── parser.py        # Content parsing
│   ├── renderer.py      # Template rendering
│   ├── builder.py       # Build orchestration
│   ├── assets.py        # Asset processing
│   ├── feed.py          # RSS generation
│   ├── sitemap.py       # Sitemap generation
│   └── watcher.py       # File watching
├── tests/               # Test suite
│   ├── conftest.py      # Test fixtures
│   └── test_*.py        # Test modules
├── docs/                # Additional documentation
├── pyproject.toml       # Project metadata
├── requirements.txt     # Dependencies
├── README.md            # Main documentation
├── ARCHITECTURE.md      # Architecture guide
├── CONTRIBUTING.md      # This file
├── LICENSE              # MIT License
└── Dockerfile           # Docker image
```

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Read ARCHITECTURE.md for design details

## Recognition

Contributors will be:
- Listed in README.md
- Credited in release notes
- Thanked profusely!

Thank you for contributing to SSG! 🎉
