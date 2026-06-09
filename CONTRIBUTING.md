# Contributing to SSG

Thank you for your interest in contributing to the Static Site Generator project! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Commit Messages](#commit-messages)
8. [Pull Request Process](#pull-request-process)
9. [Bug Reports](#bug-reports)
10. [Feature Requests](#feature-requests)

## Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** - Treat all contributors with respect
- **Be constructive** - Provide helpful feedback
- **Be collaborative** - Work together toward shared goals
- **Be patient** - Remember that everyone is learning

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of static site generators
- Familiarity with Python development

### Finding Issues to Work On

1. Check the [GitHub Issues](https://github.com/a-micable/SSG/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to express interest
4. Wait for maintainer confirmation before starting work

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/SSG.git
cd SSG

# Add upstream remote
git remote add upstream https://github.com/a-micable/SSG.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e .
pip install pytest pytest-cov

# Verify installation
ssg --version
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ssg --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

## Making Changes

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Branch Naming Conventions

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions/changes
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add docstrings to functions and classes
- Include type hints where appropriate
- Update tests for your changes

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run specific tests
pytest tests/test_parser.py::TestMarkdownParser::test_parse_file_basic

# Run with verbose output
pytest -v

# Check code coverage
pytest --cov=ssg
```

## Testing

### Writing Tests

Tests should:
- Be behavior-focused
- Use descriptive names
- Test one thing per test
- Use fixtures for setup
- Include both positive and negative cases

### Test Example

```python
def test_parse_file_basic(temp_dir):
    """Test parsing a basic Markdown file with frontmatter."""
    # Arrange
    test_file = temp_dir / "test.md"
    test_file.write_text("""---
title: Test Post
---
Content here.
""")
    
    # Act
    parser = MarkdownParser()
    result = parser.parse_file(test_file)
    
    # Assert
    assert result.title == "Test Post"
    assert "Content here" in result.content
```

### Test Coverage

- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

- **Line Length**: Maximum 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Group by stdlib, third-party, local
- **Docstrings**: Google style

### Example Code

```python
"""
Module docstring explaining purpose.
"""

from pathlib import Path
from typing import List, Optional

import click
from jinja2 import Environment

from .config import SiteConfig


class MyClass:
    """
    Class docstring with brief description.
    
    Attributes:
        config: Configuration object
        items: List of items to process
    """
    
    def __init__(self, config: SiteConfig):
        """
        Initialize the class.
        
        Args:
            config: Site configuration
        """
        self.config = config
        self.items: List[str] = []
    
    def process_item(self, item: str) -> Optional[str]:
        """
        Process a single item.
        
        Args:
            item: Item to process
            
        Returns:
            Processed item or None if invalid
            
        Raises:
            ValueError: If item is empty
        """
        if not item:
            raise ValueError("Item cannot be empty")
        
        return item.upper()
```

### Type Hints

Use type hints for:
- Function parameters
- Return values
- Class attributes
- Complex variables

```python
from typing import List, Dict, Optional, Union
from pathlib import Path

def parse_files(
    paths: List[Path],
    config: Dict[str, Any]
) -> Optional[List[ParsedContent]]:
    """Parse multiple files."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining
    what the function does and why.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this happens
        IOError: When that happens
    """
    pass
```

## Commit Messages

### Format

```
type(scope): Short description (50 chars max)

Longer explanation of what changed and why (72 chars per line).
Include context and motivation for the change.

Closes #123
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Test additions/changes
- `refactor` - Code refactoring
- `style` - Formatting changes
- `perf` - Performance improvements
- `chore` - Maintenance tasks

### Examples

```
feat(parser): Add support for TOML frontmatter

Extends the parser to handle TOML frontmatter in addition
to YAML. Users can now use +++ delimiters for TOML.

Closes #45
```

```
fix(builder): Correct pagination off-by-one error

The paginator was creating an extra empty page when the
total items divided evenly by posts_per_page. This fixes
the calculation in Paginator.total_pages.

Fixes #123
```

## Pull Request Process

### 1. Update Your Branch

```bash
# Fetch latest changes
git fetch upstream
git rebase upstream/main

# Resolve conflicts if any
# Then continue
git rebase --continue
```

### 2. Push Your Changes

```bash
# Push to your fork
git push origin feature/your-feature-name

# If rebased, force push (be careful!)
git push --force-with-lease origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:
   - **Title**: Clear, descriptive title
   - **Description**: What changes and why
   - **Testing**: How you tested the changes
   - **Related Issues**: Link to related issues

### PR Template

```markdown
## Description
Brief description of changes.

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Another change
- And another

## Testing
How were these changes tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests passing
- [ ] No new warnings

## Related Issues
Closes #123
```

### 4. Code Review

- Respond to feedback promptly
- Be open to suggestions
- Make requested changes
- Push updates to the same branch

### 5. Merge

Once approved:
- Maintainer will merge your PR
- Your changes will be in the next release
- You'll be added to contributors list

## Bug Reports

### Before Reporting

1. Check existing issues
2. Verify it's reproducible
3. Test on latest version
4. Collect relevant information

### Bug Report Template

```markdown
**Describe the Bug**
Clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Create file with '...'
2. Run command '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.2]
- SSG version: [e.g., 1.0.0]

**Additional Context**
Any other relevant information.

**Possible Solution**
(Optional) Ideas for fixing the bug.
```

## Feature Requests

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How might this feature work?

**Alternatives Considered**
Other approaches you've thought about.

**Additional Context**
Mockups, examples, or related features.
```

## Documentation

### Types of Documentation

1. **Code Documentation** - Docstrings and comments
2. **User Documentation** - README, guides, tutorials
3. **API Documentation** - Function/class references
4. **Architecture Documentation** - System design

### Documentation Standards

- Clear and concise
- Include examples
- Keep up-to-date with code
- Use proper formatting
- Link to related docs

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Build and publish to PyPI
5. Create GitHub release

## Questions?

- Open a [Discussion](https://github.com/a-micable/SSG/discussions)
- Ask in an existing issue
- Reach out to maintainers

## Recognition

Contributors will be:
- Listed in CHANGELOG
- Added to contributors list
- Credited in release notes

Thank you for contributing to SSG!
