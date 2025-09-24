#!/bin/bash
# Docx2Shelf Uninstaller for Linux

echo "=========================================="
echo "       Docx2Shelf Uninstaller"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_PATH="$SCRIPT_DIR/Docx2Shelf-"*".AppImage"

# Remove AppImage file
if ls $APPIMAGE_PATH 1> /dev/null 2>&1; then
    echo "Found AppImage files:"
    ls -1 $APPIMAGE_PATH
    echo ""
    read -p "Remove AppImage executable(s)? (y/N): " remove_app
    if [[ $remove_app =~ ^[Yy]$ ]]; then
        rm -f $APPIMAGE_PATH
        echo "✓ AppImage executable(s) removed"
    fi
else
    echo "⚠ No AppImage files found in current directory"
fi

# Remove desktop integration (if installed)
DESKTOP_FILE="$HOME/.local/share/applications/Docx2Shelf.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    echo ""
    read -p "Remove desktop integration? (y/N): " remove_desktop
    if [[ $remove_desktop =~ ^[Yy]$ ]]; then
        rm -f "$DESKTOP_FILE"
        rm -f "$HOME/.local/share/icons/hicolor/*/apps/docx2shelf.*" 2>/dev/null
        echo "✓ Desktop integration removed"
    fi
fi

# Remove user settings
echo ""
read -p "Remove user settings and preferences? (y/N): " remove_settings
if [[ $remove_settings =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.config/Docx2Shelf" 2>/dev/null
    rm -rf "$HOME/.local/share/Docx2Shelf" 2>/dev/null
    rm -rf "$HOME/.cache/Docx2Shelf" 2>/dev/null
    echo "✓ User settings removed"
fi

# Remove this uninstaller script
echo ""
read -p "Remove this uninstaller script? (y/N): " remove_script
if [[ $remove_script =~ ^[Yy]$ ]]; then
    echo "✓ Removing uninstaller script..."
    rm -f "$0"
fi

echo ""
echo "=========================================="
echo "Docx2Shelf uninstallation completed!"
echo "=========================================="

