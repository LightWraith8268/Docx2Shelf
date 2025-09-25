# Docx2Shelf v1.9.7

## 🔧 Bug Fixes - PyInstaller Configuration

### Fixed
- **Critical PyInstaller build error**: Fixed duplicate parameter `bootloader_ignore_signals` in Windows executable specification
- **Build system integrity**: Resolved syntax errors preventing successful Windows executable compilation

### Technical Details
- Removed duplicate `bootloader_ignore_signals` and `strip` parameters from PyInstaller EXE configuration
- Cleaned up PyInstaller spec file to eliminate redundant anti-virus mitigation settings
- All Windows manifest, version metadata, and code signing features from v1.9.6 remain intact

**Note**: This is a build system fix. All anti-malware mitigations (code signing, custom manifest, enhanced metadata) introduced in v1.9.6 are preserved and functional.

## 📥 Downloads

**Installation instructions**: See [README.md](https://github.com/LightWraith8268/Docx2Shelf/blob/main/README.md) for detailed installation guide.

---

**Full Changelog**: https://github.com/LightWraith8268/Docx2Shelf/blob/main/CHANGELOG.md