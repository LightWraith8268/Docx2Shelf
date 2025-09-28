# 🪶 Docx2Shelf

**Professional desktop application** for converting documents to EPUB ebooks. Simple, powerful, and completely GUI-based.

Docx2Shelf is a complete desktop application designed for authors and publishers who want professional EPUB creation through an intuitive graphical interface. No command-line knowledge required! The application handles all aspects of ebook creation: document conversion, cover integration, metadata management, chapter splitting, CSS theming, quality validation, and batch processing. Features high-fidelity Pandoc conversions with intelligent fallbacks, built-in update management, and comprehensive tool integration.

## ✨ Features

### 📖 **Document Conversion**
- **DOCX to EPUB 3**: High-fidelity conversion with Pandoc integration and intelligent fallback
- **Multiple Formats**: Supports Markdown, HTML, and TXT input files
- **Chapter Detection**: Automatic splitting by headings or page breaks with customizable depth
- **Image Processing**: Handles JPEG/PNG images with optimization and format conversion

### 🎨 **Professional Presentation**
- **CSS Themes**: Built-in serif, sans-serif, and print-like themes with custom CSS support
- **Cover Integration**: Drag-and-drop cover image support with automatic sizing
- **Typography Control**: Font selection, line spacing, and margin customization
- **Modern Interface**: Intuitive tabbed interface with dark/light theme switching

### 📝 **Metadata Management**
- **Complete Metadata**: Title, author, description, language, genre, and publication details
- **Series Support**: Calibre-compatible series information and numbering
- **ISBN/UUID**: Automatic unique identifier generation
- **Publisher Ready**: Industry-standard metadata for professional publishing

### ⚙️ **Advanced Tools**
- **Batch Processing**: Convert multiple files with progress tracking and detailed logs
- **Quality Assessment**: Built-in EPUB validation with EPUBCheck integration
- **System Diagnostics**: Environment health checking and dependency validation
- **Tool Management**: Integrated Pandoc and EPUBCheck installation and updates

### 🔄 **User Experience**
- **Interactive Wizard**: Step-by-step guided conversion process
- **Real-time Preview**: Progress tracking with detailed processing logs
- **Auto-Updates**: Built-in update checking and download integration
- **Settings Management**: Persistent preferences with import/export capability

## 📥 Installation

**Download from**: [GitHub Releases](https://github.com/LightWraith8268/Docx2Shelf/releases/latest)

### System Requirements
- **Windows**: Windows 10/11 (64-bit)
- **macOS**: macOS 10.15+ (Catalina or newer)
- **Linux**: Modern distribution with glibc 2.28+ (Ubuntu 18.04+, CentOS 8+)

### 💾 GUI Installers (Recommended)

Download the latest installer for your platform from the [Releases page](https://github.com/LightWraith8268/Docx2Shelf/releases/latest):

**🪟 Windows**
- Download `Docx2Shelf-Windows-Installer.exe`
- Double-click to install with desktop shortcuts and file associations
- **Note**: If Windows SmartScreen appears, click "More info" → "Run anyway" (the app is safe but unsigned)

**🍎 macOS**
- Download `Docx2Shelf-macOS-Installer.dmg`
- Open and drag Docx2Shelf to Applications folder

**🐧 Linux**
- Download `Docx2Shelf-Linux-x86_64.AppImage`
- Make executable: `chmod +x Docx2Shelf-*.AppImage`
- Run: `./Docx2Shelf-*.AppImage`

### 📦 Portable Versions

For users who prefer portable applications without installation:

**🪟 Windows Portable**
- Download `Docx2Shelf-windows-portable.zip`
- Extract and run `Docx2Shelf.exe`

**🍎 macOS Portable**
- Download `Docx2Shelf-macos-portable.zip`
- Extract and run `Docx2Shelf.app`

**🐧 Linux Portable**
- Download `Docx2Shelf-linux-portable.tar.gz`
- Extract and run `./Docx2Shelf`

### 🔄 Updating

The application includes built-in update checking. When an update is available, you'll see a notification with download links to get the latest version.

**Enhanced Installation Experience (v2.1.2+)**:
- Automatic upgrade detection preserves your settings during updates
- Smart permission handling for seamless Windows installation
- Robust error recovery for reliable installation on all systems

### 🗑️ Uninstalling

**🪟 Windows**:
1. Go to Settings → Apps → Installed Apps
2. Find "Docx2Shelf" and click Uninstall
3. Follow the uninstaller prompts to remove all files and settings

**🍎 macOS**:
1. **Easy Method**: Download `Uninstall-Docx2Shelf.command` from [releases](https://github.com/LightWraith8268/Docx2Shelf/releases/latest) and double-click to run
2. **Manual Method**: Drag Docx2Shelf from Applications folder to Trash
3. **Complete Removal**: Also delete these folders if they exist:
   - `~/Library/Preferences/com.docx2shelf.app.plist`
   - `~/Library/Application Support/Docx2Shelf`
   - `~/Library/Caches/com.docx2shelf.app`

**🐧 Linux**:
1. **Easy Method**: Download `uninstall-docx2shelf.sh` from [releases](https://github.com/LightWraith8268/Docx2Shelf/releases/latest) and run it
2. **Manual Method**: Delete the AppImage file
3. **Complete Removal**: Also delete `~/.config/Docx2Shelf` and `~/.local/share/Docx2Shelf` if they exist

## 🚀 Getting Started

### Launch the Application
1. **Install**: Download and install for your platform (see Installation section above)
2. **Launch**: Open Docx2Shelf from your desktop, Start Menu, or Applications folder
3. **Convert**: Use the intuitive interface to convert your documents to EPUB

### Basic Conversion Workflow
1. **Select Document**: Click "Browse" and choose your DOCX, Markdown, HTML, or TXT file
2. **Enter Metadata**: Fill in title, author, description, and other book details
3. **Choose Settings**: Select theme, chapter splitting options, and output preferences
4. **Convert**: Click "Convert to EPUB" and watch the real-time progress
5. **Done**: Your EPUB is ready for reading or publishing!

### Advanced Features
- **Batch Processing**: Convert multiple documents at once with the Batch tab
- **Interactive Wizard**: Use the step-by-step wizard for guided conversion
- **Quality Assessment**: Validate your EPUB with built-in quality tools
- **Theme Customization**: Preview and customize CSS themes
- **Tool Management**: Install and manage Pandoc and EPUBCheck tools

### Need Help?
- **Built-in Help**: Each tab includes tooltips and help information
- **System Diagnostics**: Use the Tools tab to run environment health checks
- **Update Notifications**: The app will notify you when updates are available

## 🎯 Why Choose Docx2Shelf?

- **🖱️ Pure GUI Experience**: Everything accessible through the graphical interface - no terminal required
- **🚀 Zero Technical Knowledge**: Professional EPUB creation with point-and-click simplicity
- **💻 Native Desktop App**: Feels natural on Windows, macOS, and Linux with proper installers
- **📖 Publisher Ready**: Industry-standard EPUB 3 output compatible with all major ebook platforms
- **🔒 Privacy First**: Completely offline operation - your manuscripts never leave your computer
- **🆓 Open Source**: Free forever with active community development
- **⚡ High Performance**: Fast conversions with Pandoc integration and intelligent fallbacks

## License

MIT

## Changelog

For a detailed list of changes, please refer to the [CHANGELOG.md](CHANGELOG.md) file.