# Release Process Documentation

This document outlines the automated release process for Docx2Shelf, ensuring consistency and completeness for every release.

## Overview

Every release follows these steps automatically:
1. ✅ Update version in `pyproject.toml`
2. ✅ Update `ROADMAP.md` marking current version as completed
3. ✅ Update `CHANGELOG.md` with release notes
4. ✅ Update `README.md` with new user-facing features
5. ✅ Commit changes with standardized commit message
6. ✅ Push to GitHub
7. ✅ Create GitHub release with comprehensive notes and installation assets
8. ✅ Trigger PyPI publishing workflow

**Release Assets Included:**
- `install.bat` - Windows installation script
- `scripts/install.sh` - macOS/Linux installation script

## Automated Release via GitHub Actions

### Using the GitHub UI

1. Go to the **Actions** tab in the GitHub repository
2. Select **Automated Release** workflow
3. Click **Run workflow**
4. Fill in the required fields:
   - **Version**: New version number (e.g., `1.2.8`)
   - **Milestone**: Milestone name (e.g., `Community & Ecosystem`)
   - **Features**: Comma-separated list of features for CHANGELOG
   - **README Features**: Comma-separated list of user-facing features for README
   - **Dry Run**: Check to preview without making changes

### Example Usage

**For a minor release (v1.2.8):**
```
Version: 1.2.8
Milestone: Community & Ecosystem
Features: Plugin marketplace with ratings, Community forums integration, Enhanced ecosystem integration
README Features: Plugin Marketplace, Community Platform, Writing Tools Integration
Dry Run: false
```

**For a dry run (preview):**
```
Version: 1.2.8
Milestone: Community & Ecosystem
Features: Plugin marketplace with ratings, Community forums integration
README Features: Plugin Marketplace, Community Platform
Dry Run: true
```

## Manual Release via Script

For local testing or manual releases:

```bash
# Install dependencies
pip install -r requirements.txt

# Preview release (dry run)
python scripts/release.py \
  --version 1.2.8 \
  --milestone "Community & Ecosystem" \
  --features "Plugin marketplace with ratings" "Community forums integration" \
  --readme-features "Plugin Marketplace" "Community Platform" \
  --dry-run

# Execute release
python scripts/release.py \
  --version 1.2.8 \
  --milestone "Community & Ecosystem" \
  --features "Plugin marketplace with ratings" "Community forums integration" \
  --readme-features "Plugin Marketplace" "Community Platform"
```

## Release Types

### Major Release (1.x.0 → 2.0.0)
- Breaking changes
- Major architecture updates
- Significant new features

### Minor Release (1.2.x → 1.3.0)
- New features
- Major milestones
- Backward-compatible changes

### Patch Release (1.2.7 → 1.2.8)
- Bug fixes
- Small improvements
- Documentation updates

## File Updates

### pyproject.toml
```toml
# Before
version = "1.2.7"

# After
version = "1.2.8"
```

### ROADMAP.md
```markdown
# Before
### 🟦 **Next — v1.2.8: Community & Ecosystem**

# After
### ✅ **Completed — v1.2.8: Community & Ecosystem**
```

### CHANGELOG.md
```markdown
# Before
# Changelog

## [1.2.7] - 2025-01-19

# After
# Changelog

## [1.2.8] - 2025-01-20
### Community & Ecosystem

- Plugin marketplace with ratings and reviews
- Community forums integration
- Enhanced ecosystem integration

## [1.2.7] - 2025-01-19
```

### README.md
Updates the features section with new user-facing capabilities:
```markdown
### New in v1.2.8
- **Plugin Marketplace**: Discover and install community plugins
- **Community Platform**: Forums and collaboration tools
```

## Commit Message Format

The automation uses standardized commit messages:

```
feat: Release v1.2.8 - Community & Ecosystem

- Updated version to 1.2.8 in pyproject.toml
- Updated ROADMAP.md marking v1.2.8 as completed
- Updated CHANGELOG.md with Community & Ecosystem features
- Updated README.md with new user-facing features

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## GitHub Release Notes

Automatically generated release notes include:
- Version and milestone information
- Feature highlights
- Installation instructions
- Links to documentation
- Full changelog reference

## Prerequisites

### For GitHub Actions
- Repository write permissions
- GitHub CLI access
- Valid `GITHUB_TOKEN`

### For Manual Script
- Python 3.11+
- Git configured with user credentials
- GitHub CLI (`gh`) installed and authenticated
- Repository write access

## Troubleshooting

### Common Issues

**Git authentication errors:**
```bash
# Configure Git credentials
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"

# Or use GitHub CLI
gh auth login
```

**Version format errors:**
- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Examples: `1.2.8`, `2.0.0`, `1.3.0`

**Missing features in release:**
- Ensure features are properly comma-separated
- Use quotes for features with spaces
- Verify feature descriptions are clear and user-focused

### Rollback Process

If a release needs to be rolled back:

1. **Delete the GitHub release:**
   ```bash
   gh release delete v1.2.8 --yes
   ```

2. **Revert the commit:**
   ```bash
   git revert HEAD
   git push
   ```

3. **Update version back:**
   ```bash
   # Manually edit pyproject.toml or run script with previous version
   ```

## Best Practices

### Before Release
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Features tested thoroughly
- [ ] Breaking changes documented

### Feature Descriptions
- Use present tense ("Adds", not "Added")
- Focus on user benefits
- Be specific and actionable
- Include technical details in CHANGELOG

### Version Planning
- Plan versions in ROADMAP.md
- Keep milestones focused
- Communicate breaking changes clearly
- Maintain backward compatibility when possible

## Integration with CI/CD

The automated release process integrates with:
- **PyPI Publishing**: Automatically triggered after release
- **Docker Builds**: New images built for releases
- **Documentation Deployment**: Docs updated with new version
- **Package Managers**: Homebrew, winget, Scoop updated

## Security Considerations

- Release workflow requires explicit approval
- All commits are signed and verified
- Dependencies are pinned and verified
- Secrets are properly managed in GitHub

---

For questions about the release process, see the [CONTRIBUTING.md](CONTRIBUTING.md) guide or open an issue.