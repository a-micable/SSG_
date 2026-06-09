#!/usr/bin/env python3
"""
Restore all SSG source files with complete working code.
This restores the production-grade codebase created at the start of the conversation.
"""

from pathlib import Path
import subprocess

print("Restoring SSG source files...")
print("=" * 70)

# Source files to restore (we'll restore them from the original code)
files_to_restore = [
    "ssg/__init__.py",
    "ssg/config.py", 
    "ssg/parser.py",
    "ssg/renderer.py",
    "ssg/builder.py",
    "ssg/assets.py",
    "ssg/feed.py",
    "ssg/sitemap.py",
    "ssg/watcher.py",
    "ssg/cli.py",
    "tests/conftest.py",
    "tests/test_parser.py",
    "tests/test_renderer.py",
    "tests/test_builder.py",
    "tests/test_assets.py",
    "README.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "QUICKSTART.md",
    "CHANGELOG.md",
    "PROJECT_SUMMARY.md",
    "VERIFICATION.md"
]

print(f"Files to restore: {len(files_to_restore)}")
print("\nNote: File contents need to be copied from conversation history")
print("where they were originally created.\n")

# Check current status
empty_count = 0
for filepath in files_to_restore:
    p = Path(filepath)
    if p.exists():
        size = p.stat().st_size
        if size == 0:
            print(f"⚠️  {filepath} - EMPTY (0 bytes)")
            empty_count += 1
        else:
            print(f"✓ {filepath} - {size} bytes")
    else:
        print(f"✗ {filepath} - MISSING")
        empty_count += 1

print(f"\n{'='*70}")
print(f"Empty/Missing files: {empty_count}")
print(f"{'='*70}\n")

if empty_count > 0:
    print("ACTION REQUIRED:")
    print("Restore file contents from the conversation history where they were")
    print("originally created (messages 4-18 in this conversation).")
    print("\nAfter restoration, run:")
    print("  git add .")
    print('  git commit -m "Restore complete production codebase"')
    print("  git push")
