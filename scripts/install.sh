#!/bin/bash
# Docx2Shelf Installation Script for Linux/macOS
# This script downloads and installs the latest version of Docx2Shelf

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "  Docx2Shelf Installation Script"
echo "========================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    INSTALLER_PATTERN="AppImage"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    INSTALLER_PATTERN="dmg"
else
    echo -e "${RED}[!] Unsupported operating system${NC}"
    exit 1
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${YELLOW}[*] Detecting latest version...${NC}"

# Get latest release info from GitHub API
RELEASE_INFO=$(curl -s https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest)
DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep "browser_download_url" | grep "$INSTALLER_PATTERN" | head -1 | cut -d'"' -f4)
RELEASE_TAG=$(echo "$RELEASE_INFO" | grep "tag_name" | head -1 | cut -d'"' -f4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo -e "${RED}[!] Could not find installer for your system${NC}"
    echo "Please download manually from:"
    echo "https://github.com/LightWraith8268/Docx2Shelf/releases/latest"
    exit 1
fi

echo -e "${GREEN}[+] Found version: $RELEASE_TAG${NC}"
echo -e "${YELLOW}[*] Downloading installer...${NC}"

# Download installer
INSTALLER_FILE="$TEMP_DIR/docx2shelf-installer"
if ! curl -L -o "$INSTALLER_FILE" "$DOWNLOAD_URL"; then
    echo -e "${RED}[!] Failed to download installer${NC}"
    exit 1
fi

echo -e "${GREEN}[+] Download complete${NC}"
echo ""

# Handle different formats
case "$OS" in
    linux)
        echo -e "${YELLOW}[*] Installing Docx2Shelf...${NC}"
        chmod +x "$INSTALLER_FILE"
        
        # Run AppImage with no sandbox for better compatibility
        APPIMAGE_EXTRACTED_DIR=$(mktemp -d)
        export APPDIR="$APPIMAGE_EXTRACTED_DIR"
        "$INSTALLER_FILE" --appimage-mount > /dev/null 2>&1 &
        MOUNT_PID=$!
        
        if [ $MOUNT_PID -gt 0 ]; then
            wait $MOUNT_PID 2>/dev/null || true
        fi
        
        # Install to applications directory
        INSTALL_DIR="$HOME/.local/share/applications"
        mkdir -p "$INSTALL_DIR"
        cp "$INSTALLER_FILE" "$HOME/.local/bin/docx2shelf" 2>/dev/null || \
        cp "$INSTALLER_FILE" "/usr/local/bin/docx2shelf" 2>/dev/null || {
            echo -e "${YELLOW}[*] Installing to home directory...${NC}"
            cp "$INSTALLER_FILE" "$HOME/.docx2shelf"
            chmod +x "$HOME/.docx2shelf"
            echo -e "${GREEN}[+] Installed at: $HOME/.docx2shelf${NC}"
        }
        ;;
    macos)
        echo -e "${YELLOW}[*] Installing Docx2Shelf...${NC}"
        
        # Mount DMG
        MOUNT_POINT="/Volumes/Docx2Shelf"
        hdiutil attach "$INSTALLER_FILE" -nobrowse -noverify > /dev/null
        
        if [ -d "$MOUNT_POINT/Docx2Shelf.app" ]; then
            cp -r "$MOUNT_POINT/Docx2Shelf.app" /Applications/
            hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
            echo -e "${GREEN}[+] Installed to /Applications/Docx2Shelf.app${NC}"
        else
            echo -e "${RED}[!] Could not find application in DMG${NC}"
            hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
            exit 1
        fi
        ;;
esac

echo ""
echo -e "${GREEN}[+] Installation complete!${NC}"
echo ""
echo "To launch Docx2Shelf:"
if [ "$OS" = "linux" ]; then
    echo "  ~/.docx2shelf  (or docx2shelf if in PATH)"
else
    echo "  /Applications/Docx2Shelf.app"
fi
echo ""
