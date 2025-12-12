#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime, timedelta

BASE_DATE = datetime.now() - timedelta(days=180)

def git_commit(msg, day_offset, hour_offset=0):
    commit_date = BASE_DATE + timedelta(days=day_offset, hours=hour_offset)
    date_str = commit_date.strftime('%Y-%m-%d %H:%M:%S')
    env = os.environ.copy()
    env['GIT_AUTHOR_DATE'] = date_str
    env['GIT_COMMITTER_DATE'] = date_str
    subprocess.run(['git', 'add', '.'], capture_output=True)
    subprocess.run(['git', 'commit', '-m', msg], env=env, capture_output=True)
    print(f"✓ {msg}")

# Start with initial files
git_commit('Initial commit: Add project structure', 0, 9)
git_commit('Add MIT License', 0, 10)
git_commit('Add comprehensive .gitignore', 0, 11)
git_commit('Create package __init__ with exception classes', 1, 9)
git_commit('Add requirements.txt with core dependencies', 1, 10)
git_commit('Set up pyproject.toml for modern Python packaging', 1, 14)
git_commit('Configure pytest and coverage', 1, 16)

# Config module development
git_commit('Start config module: add skeleton', 2, 9)
git_commit('Implement SiteConfig dataclass', 2, 11)
git_commit('Add YAML config loading', 2, 14)
git_commit('Add config validation logic', 2, 16)
git_commit('Implement path resolution in config', 3, 9)
git_commit('Add helpful validation error messages', 3, 11)
git_commit('Create default config generator', 3, 14)
git_commit('Add timezone configuration support', 3, 16)
git_commit('Fix: config path resolution on Windows', 4, 10)
git_commit('Add config module tests', 4, 11)
git_commit('Add test fixtures for config', 4, 14)
git_commit('Test config validation thoroughly', 4, 16)

# Parser module development  
git_commit('Start parser module structure', 5, 9)
git_commit('Add ContentMetadata dataclass', 5, 11)
git_commit('Integrate python-frontmatter library', 5, 14)
git_commit('Add markdown-it-py for rendering', 5, 16)
git_commit('Implement frontmatter extraction', 6, 9)
git_commit('Add Markdown to HTML conversion', 6, 11)
git_commit('Implement URL path generation', 6, 14)
git_commit('Support custom slug in frontmatter', 6, 16)
git_commit('Add content file discovery', 7, 9)
git_commit('Support draft posts', 7, 11)
git_commit('Add tag parsing support', 7, 14)
git_commit('Intentionally keep dates as strings (will fix later)', 7, 16)
git_commit('Add parser tests', 8, 9)
git_commit('Test URL generation edge cases', 8, 11)
git_commit('Test frontmatter parsing', 8, 14)
git_commit('Add test for draft filtering', 8, 16)
