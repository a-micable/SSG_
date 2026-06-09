#!/bin/bash
# Restore all SSG source files

cd /home/amicable/SSG

# Clean up pyc files
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Restoring source files..."
