# Docx2Shelf v1.9.6
### Security - Enhanced Anti-Malware Mitigations

#### Added
- **Custom Windows manifest**: Added legitimate application manifest to reduce false positives
- **Enhanced version metadata**: Comprehensive version info and application descriptions  
- **Additional import excludes**: Removed suspicious modules that trigger antivirus detection
- **Anti-virus friendly PyInstaller settings**: Optimized for minimal false positive triggers
- **Code signing**: Self-signed executable to establish trust with Windows Defender

#### Technical Details
- Added docx2shelf.manifest with proper Windows compatibility declarations
- Excluded win32api, distutils, setuptools and other commonly flagged imports
- Enhanced version info with company, description, and copyright metadata
- Configured PyInstaller with strip=False and no UAC elevation requests
- Added DPI awareness and Windows version compatibility declarations
- Implemented code signing workflow with self-signed certificates

## 📥 Downloads

**Installation instructions**: See [README.md](https://github.com/LightWraith8268/Docx2Shelf/blob/main/README.md) for detailed installation guide.

---

**Full Changelog**: https://github.com/LightWraith8268/Docx2Shelf/blob/main/CHANGELOG.md
