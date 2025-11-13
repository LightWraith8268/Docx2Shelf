# GitHub Release Instructions for Docx2Shelf v2.1.8

## Automated Release (Recommended)

### Step 1: Verify Release Assets
The following file is ready for release:
- **File**: `Docx2Shelf-Portable-2.1.8.zip` (15 MB)
- **Location**: `/mnt/s/coding/docx2shelf/Docx2Shelf-Portable-2.1.8.zip`
- **SHA256**: `5b2c6ea01a3ddef1e0610a3ca34187db7b847d5bb5d56e7cd3e3124b4107769d`

### Step 2: Create GitHub Release

Using GitHub CLI (if available):
```bash
gh release create v2.1.8 \
  --title "Docx2Shelf v2.1.8 - Fixed Portable Distribution" \
  --notes-file RELEASE_NOTES_v2.1.8.md \
  Docx2Shelf-Portable-2.1.8.zip
```

### Step 3: Manual Web Interface

If CLI is not available, use the web interface:

1. **Navigate to**: https://github.com/LightWraith8268/Docx2Shelf/releases/new

2. **Fill in Release Details**:
   - **Tag version**: `v2.1.8`
   - **Release title**: `Docx2Shelf v2.1.8 - Fixed Portable Distribution`
   - **Description**: Paste contents of `RELEASE_NOTES_v2.1.8.md`

3. **Upload Asset**:
   - Click "Attach binaries..." or drag and drop
   - Select: `Docx2Shelf-Portable-2.1.8.zip`

4. **Publish Release**:
   - Check "Set as the latest release"
   - Click "Publish release"

## Release Information

### Metadata
- **Tag**: v2.1.8
- **Branch**: main
- **Type**: Release (production-ready)
- **Portable Distribution**: Yes ✓
- **Binary Assets**: 1 ZIP file (15 MB)

### What's New in v2.1.8
- Fixed critical PyInstaller module bundling issues
- Portable distribution now fully functional
- All stdlib modules properly included
- Zero-installation Windows executable

### Asset Details
```
File: Docx2Shelf-Portable-2.1.8.zip
Size: 15 MB (compressed)
Contents: 
  - Docx2Shelf.exe (2.9 MB)
  - _internal/ (bundled dependencies)
  - README.md (portable usage instructions)
```

## Verification Checklist

Before releasing:
- ✓ ZIP file created successfully
- ✓ Portable_Distribution folder updated in repo
- ✓ Changes committed to git
- ✓ Release notes prepared
- ✓ SHA256 checksum calculated
- ✓ Version number verified (2.1.8)

## Post-Release Tasks

After creating the GitHub release:

1. **Verify Release**:
   - Check release appears on https://github.com/LightWraith8268/Docx2Shelf/releases
   - Verify ZIP asset is downloadable
   - Confirm release notes display correctly

2. **Update Documentation**:
   - README.md already references portable version
   - Installation section mentions v2.1.8

3. **Announce Release**:
   - Users can now download portable version
   - No installation wizard needed
   - Works on Windows 7+

## Rollback Plan

If issues are discovered after release:

1. **Unpublish**: Mark release as pre-release
2. **Investigate**: Check error reports
3. **Fix**: Modify spec file if needed
4. **Rebuild**: Create new executable
5. **Update**: Create v2.1.9 patch release

## Support

For issues during or after release:
- Check the error logs in `build/docx2shelf_gui/`
- Verify ZIP integrity with `unzip -t Docx2Shelf-Portable-2.1.8.zip`
- Test extraction and executable launch
