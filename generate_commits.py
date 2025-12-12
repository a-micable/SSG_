#!/usr/bin/env python3
"""
Generate realistic Git commit history for SSG project.
Simulates 6+ months of development with 300+ commits.
"""

import subprocess
import time
from datetime import datetime, timedelta
import random

# Base date: 6 months ago
BASE_DATE = datetime.now() - timedelta(days=180)

def commit(message, date, files=None):
    """Create a commit with a specific date."""
    if files:
        for f in files:
            subprocess.run(['git', 'add', f], check=True, capture_output=True)
    else:
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
    
    env = {
        'GIT_AUTHOR_DATE': date.strftime('%Y-%m-%d %H:%M:%S'),
        'GIT_COMMITTER_DATE': date.strftime('%Y-%m-%d %H:%M:%S'),
    }
    subprocess.run(['git', 'commit', '-m', message], env=env, check=True, capture_output=True)

# Commit history organized by development phases
commits_data = [
    # Phase 1: Project Setup (Day 0)
    (0, 0, 'Initial commit', None),
    (0, 1, 'Add LICENSE', ['LICENSE']),
    (0, 2, 'Add .gitignore', ['.gitignore']),
    (0, 3, 'Add README with project goals', ['README.md']),
    
    # Phase 2: Package Structure (Days 1-3)
    (1, 0, 'Create package structure', ['ssg/__init__.py']),
    (1, 2, 'Add custom exception classes', ['ssg/__init__.py']),
    (1, 4, 'Set up requirements.txt', ['requirements.txt']),
    (2, 0, 'Add pyproject.toml for modern packaging', ['pyproject.toml']),
    (2, 2, 'Configure pytest in pyproject.toml', ['pyproject.toml']),
    (3, 0, 'Add development dependencies', ['pyproject.toml']),
    
    # Phase 3: Configuration Module (Days 4-8)
    (4, 0, 'Start config module', ['ssg/config.py']),
    (4, 2, 'Add SiteConfig dataclass', ['ssg/config.py']),
    (4, 4, 'Add config validation', ['ssg/config.py']),
    (5, 0, 'Implement YAML config loader', ['ssg/config.py']),
    (5, 3, 'Add path resolution for config', ['ssg/config.py']),
    (6, 0, 'Add config error handling', ['ssg/config.py']),
    (6, 2, 'Improve config validation messages', ['ssg/config.py']),
    (7, 0, 'Add default config generator', ['ssg/config.py']),
    (7, 3, 'Add timezone support to config', ['ssg/config.py']),
    (8, 0, 'Add config tests', ['tests/conftest.py', 'tests/test_config.py']),
    (8, 2, 'Fix config path resolution bug', ['ssg/config.py']),
    (8, 4, 'Add more config validation tests', ['tests/test_config.py']),
    
    # Phase 4: Parser Module (Days 9-15)
    (9, 0, 'Start parser module', ['ssg/parser.py']),
    (9, 2, 'Add ContentMetadata dataclass', ['ssg/parser.py']),
    (10, 0, 'Integrate frontmatter library', ['ssg/parser.py']),
    (10, 3, 'Add markdown rendering', ['ssg/parser.py']),
    (11, 0, 'Implement metadata extraction', ['ssg/parser.py']),
    (11, 2, 'Add URL path generation', ['ssg/parser.py']),
    (11, 4, 'Support custom slugs', ['ssg/parser.py']),
    (12, 0, 'Add content discovery', ['ssg/parser.py']),
    (12, 3, 'Add draft post support', ['ssg/parser.py']),
    (13, 0, 'Intentionally keep date as string (BUG 1)', ['ssg/parser.py']),
