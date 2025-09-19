# Release Process Documentation

This document outlines the automated release process for Docx2Shelf, ensuring consistency and completeness for every release.

## Overview - Fully Automated Tag-Based Releases

The release process is now **fully automated**. Simply push your changes and create a version tag, and everything else happens automatically:

### Developer Workflow
1. ✅ Update version in `pyproject.toml`
2. ✅ Update `ROADMAP.md` marking current version as completed
3. ✅ Update `CHANGELOG.md` with release notes
4. ✅ Update `README.md` with new user-facing features
5. ✅ Commit and push changes
6. ✅ Create and push a version tag (e.g., `v1.2.8`)

### Automated by GitHub Actions
7. 🤖 **Automatically extracts** version and milestone from tag and CHANGELOG
8. 🤖 **Automatically creates** GitHub release with comprehensive notes
9. 🤖 **Automatically attaches** installation assets (`install.bat`, `scripts/install.sh`)
10. 🤖 **Automatically triggers** PyPI publishing workflow

**Release Assets Automatically Included:**
- `install.bat` - Windows installation script
- `scripts/install.sh` - macOS/Linux installation script

## Simple Tag-Based Release Process

### Complete Example Workflow

Here's the complete process for releasing v1.2.8:

```bash
# 1. Update version in pyproject.toml
sed -i 's/version = "1.2.7"/version = "1.2.8"/' pyproject.toml

# 2. Update ROADMAP.md (mark v1.2.8 as completed)
# Edit ROADMAP.md manually or using your editor

# 3. Update CHANGELOG.md (add v1.2.8 entry)
# Add new section at the top:
## [1.2.8] - 2025-01-20
### Community & Ecosystem
- Plugin marketplace with community ratings and reviews
- Community forums integration and collaboration tools
- Enhanced ecosystem integration with popular writing tools

# 4. Update README.md with new user-facing features
# Add or update feature sections as needed

# 5. Commit all changes
git add .
git commit -m "feat: Release v1.2.8 - Community & Ecosystem"

# 6. Push changes
git push

# 7. Create and push version tag - THIS TRIGGERS THE RELEASE!
git tag v1.2.8
git push origin v1.2.8
```

**That's it!** The GitHub Actions workflow will automatically:
- Extract version and milestone from the tag and CHANGELOG
- Create a GitHub release with comprehensive notes
- Attach `install.bat` and `scripts/install.sh` as assets
- Trigger PyPI publishing

### Alternative: Using GitHub CLI

```bash
# Steps 1-6 same as above...

# 7. Create and push tag with GitHub CLI
gh release create v1.2.8 --generate-notes --title "v1.2.8 - Community & Ecosystem"
```

### Alternative: Using GitHub Web UI

1. Go to **Releases** in your GitHub repository
2. Click **Create a new release**
3. Click **Choose a tag** → Type `v1.2.8` → **Create new tag**
4. **Release title**: `v1.2.8 - Community & Ecosystem`
5. Click **Generate release notes** (optional)
6. Click **Publish release**

The automation will still run and attach the installation assets!

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

Use this simple format for release commits:

```
feat: Release v1.2.8 - Community & Ecosystem

- Updated version to 1.2.8 in pyproject.toml
- Updated ROADMAP.md marking v1.2.8 as completed
- Updated CHANGELOG.md with Community & Ecosystem features
- Updated README.md with new user-facing features
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