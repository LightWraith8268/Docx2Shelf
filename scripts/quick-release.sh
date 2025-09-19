#!/bin/bash
# Quick release script for Docx2Shelf
# Usage: ./scripts/quick-release.sh 1.2.8 "Community & Ecosystem"

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <version> <milestone>"
    echo "Example: $0 1.2.8 \"Community & Ecosystem\""
    exit 1
fi

VERSION="$1"
MILESTONE="$2"
DATE=$(date +%Y-%m-%d)

echo "🚀 Starting release process for v$VERSION - $MILESTONE"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: You must be on the main branch to create a release"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes first."
    git status --short
    exit 1
fi

echo "✅ Git status is clean"

# Pull latest changes
echo "📥 Pulling latest changes from remote..."
git pull

# Check if tag already exists
if git tag -l | grep -q "^v$VERSION$"; then
    echo "❌ Error: Tag v$VERSION already exists"
    exit 1
fi

echo "✅ Tag v$VERSION does not exist yet"

# Update version in pyproject.toml
echo "📝 Updating version in pyproject.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/version = \"[^\"]*\"/version = \"$VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/version = \"[^\"]*\"/version = \"$VERSION\"/" pyproject.toml
fi

# Verify the change
NEW_VERSION=$(grep 'version = ' pyproject.toml | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')
if [ "$NEW_VERSION" != "$VERSION" ]; then
    echo "❌ Error: Failed to update version in pyproject.toml"
    echo "Expected: $VERSION, Got: $NEW_VERSION"
    exit 1
fi

echo "✅ Updated version to $VERSION in pyproject.toml"

# Show what needs to be updated manually
echo ""
echo "🔧 MANUAL UPDATES REQUIRED:"
echo "================================"
echo ""
echo "1. Update ROADMAP.md:"
echo "   - Mark v$VERSION as completed"
echo "   - Move to next version planning"
echo ""
echo "2. Update CHANGELOG.md:"
echo "   - Add this section at the top:"
echo ""
echo "## [$VERSION] - $DATE"
echo "### $MILESTONE"
echo ""
echo "- [List your features here]"
echo "- [Add more features as needed]"
echo ""
echo "3. Update README.md:"
echo "   - Add new user-facing features"
echo "   - Update version references if needed"
echo ""
echo "4. When done, run:"
echo "   git add ."
echo "   git commit -m \"feat: Release v$VERSION - $MILESTONE\""
echo "   git push"
echo "   git tag v$VERSION"
echo "   git push origin v$VERSION"
echo ""
echo "The GitHub Actions workflow will automatically:"
echo "- Create the GitHub release"
echo "- Attach install.bat and scripts/install.sh"
echo "- Trigger PyPI publishing"
echo ""

# Open files for editing (if on macOS or Linux with common editors)
if command -v code >/dev/null 2>&1; then
    echo "📝 Opening files in VS Code..."
    code ROADMAP.md CHANGELOG.md README.md pyproject.toml
elif command -v vim >/dev/null 2>&1; then
    echo "📝 Files ready for editing:"
    echo "   - ROADMAP.md"
    echo "   - CHANGELOG.md"
    echo "   - README.md"
    echo "   - pyproject.toml (already updated)"
fi

echo ""
echo "✅ Release preparation complete!"
echo "📋 Next: Make your manual updates, then commit and tag"