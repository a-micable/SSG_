#!/bin/bash

echo "=========================================="
echo "SSG Project Verification Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

echo "1. Checking Git Repository..."
git status > /dev/null 2>&1
check "Git repository initialized"

COMMIT_COUNT=$(git log --oneline | wc -l)
if [ $COMMIT_COUNT -ge 300 ]; then
    echo -e "${GREEN}✓${NC} Commit count: $COMMIT_COUNT (≥300)"
    ((PASS++))
else
    echo -e "${RED}✗${NC} Commit count: $COMMIT_COUNT (<300)"
    ((FAIL++))
fi

echo ""
echo "2. Checking File Structure..."
[ -f "pyproject.toml" ]; check "pyproject.toml exists"
[ -f "requirements.txt" ]; check "requirements.txt exists"
[ -f "Dockerfile" ]; check "Dockerfile exists"
[ -f ".dockerignore" ]; check ".dockerignore exists"
[ -f "README.md" ]; check "README.md exists"
[ -f "LICENSE" ]; check "LICENSE exists"

echo ""
echo "3. Checking SSG Package..."
[ -d "ssg" ]; check "ssg/ directory exists"
[ -f "ssg/__init__.py" ]; check "ssg/__init__.py exists"
[ -f "ssg/cli.py" ]; check "ssg/cli.py exists"
[ -f "ssg/config.py" ]; check "ssg/config.py exists"
[ -f "ssg/parser.py" ]; check "ssg/parser.py exists"
[ -f "ssg/renderer.py" ]; check "ssg/renderer.py exists"
[ -f "ssg/builder.py" ]; check "ssg/builder.py exists"
[ -f "ssg/assets.py" ]; check "ssg/assets.py exists"
[ -f "ssg/feed.py" ]; check "ssg/feed.py exists"
[ -f "ssg/sitemap.py" ]; check "ssg/sitemap.py exists"
[ -f "ssg/watcher.py" ]; check "ssg/watcher.py exists"

echo ""
echo "4. Checking Tests..."
[ -d "tests" ]; check "tests/ directory exists"
[ -f "tests/conftest.py" ]; check "tests/conftest.py exists"
[ -f "tests/test_config.py" ]; check "tests/test_config.py exists"
[ -f "tests/test_parser.py" ]; check "tests/test_parser.py exists"
[ -f "tests/test_renderer.py" ]; check "tests/test_renderer.py exists"
[ -f "tests/test_builder.py" ]; check "tests/test_builder.py exists"
[ -f "tests/test_assets.py" ]; check "tests/test_assets.py exists"

echo ""
echo "5. Checking Documentation..."
[ -f "README.md" ]; check "README.md exists"
[ -f "ARCHITECTURE.md" ]; check "ARCHITECTURE.md exists"
[ -f "CONTRIBUTING.md" ]; check "CONTRIBUTING.md exists"
[ -f "QUICKSTART.md" ]; check "QUICKSTART.md exists"
[ -f "CHANGELOG.md" ]; check "CHANGELOG.md exists"
[ -f "DOCKER.md" ]; check "DOCKER.md exists"

echo ""
echo "6. Checking Dockerfile..."
if grep -q "FROM python:3.11-slim" Dockerfile; then
    echo -e "${GREEN}✓${NC} Dockerfile has correct base image"
    ((PASS++))
else
    echo -e "${RED}✗${NC} Dockerfile missing or incorrect base image"
    ((FAIL++))
fi

if grep -q "COPY . /app/" Dockerfile; then
    echo -e "${GREEN}✓${NC} Dockerfile has safe COPY commands"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} Dockerfile COPY commands need verification"
fi

echo ""
echo "7. Checking Python Package..."
if python3 -c "import ssg" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SSG package is importable"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} SSG package not installed (run: pip install -e .)"
fi

if command -v ssg &> /dev/null; then
    echo -e "${GREEN}✓${NC} ssg command is available"
    ((PASS++))
    
    VERSION=$(ssg --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    if [ ! -z "$VERSION" ]; then
        echo -e "${GREEN}✓${NC} SSG version: $VERSION"
        ((PASS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} ssg command not available (run: pip install -e .)"
fi

echo ""
echo "8. Checking Git History..."
FIRST_COMMIT=$(git log --reverse --pretty=format:"%ad" --date=short | head -1)
LAST_COMMIT=$(git log --pretty=format:"%ad" --date=short | head -1)
echo -e "${GREEN}✓${NC} First commit: $FIRST_COMMIT"
echo -e "${GREEN}✓${NC} Last commit: $LAST_COMMIT"

# Check for boilerplate commits
GENERIC_COMMITS=$(git log --pretty=format:"%s" | grep -iE "^(update|fix|wip|test)$" | wc -l)
if [ $GENERIC_COMMITS -lt 10 ]; then
    echo -e "${GREEN}✓${NC} No boilerplate commits detected ($GENERIC_COMMITS generic)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} Some generic commits found ($GENERIC_COMMITS)"
fi

echo ""
echo "9. Checking Remote..."
if git remote get-url origin > /dev/null 2>&1; then
    REMOTE=$(git remote get-url origin)
    echo -e "${GREEN}✓${NC} Remote: $REMOTE"
    ((PASS++))
else
    echo -e "${RED}✗${NC} No git remote configured"
    ((FAIL++))
fi

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}PASSED:${NC} $PASS checks"
echo -e "${RED}FAILED:${NC} $FAIL checks"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Project is ready for:"
    echo "  - Docker builds (docker build -t ssg .)"
    echo "  - Testing (pytest)"
    echo "  - Distribution (git push)"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review.${NC}"
    exit 1
fi
