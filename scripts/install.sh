#!/bin/bash

# Docx2Shelf Installer for macOS and Linux
# This script installs Python (if needed) and Docx2Shelf, ensuring both are available globally on PATH
# Features:
# - Automatic Python 3.11+ installation if not found (Linux only, macOS users directed to python.org)
# - Multiple installation fallback methods
# - Automatic PATH configuration
# - Optional custom installation location
# - User-friendly error handling and diagnostics
#
# Usage:
#   ./install.sh                    - Standard installation
#   ./install.sh --path "/opt/tools"  - Install to custom location
#   ./install.sh --help             - Show help

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show manual installation guidance
show_manual_install_guidance() {
    echo
    echo "========================================"
    echo "    Manual Installation Required"
    echo "========================================"
    echo
    echo "Git is required to install docx2shelf from GitHub."
    echo
    echo "Options:"
    echo "1. Install Git:"
    if [[ "$OS" == "linux" ]]; then
        echo "   Ubuntu/Debian: sudo apt-get install git"
        echo "   CentOS/RHEL: sudo yum install git"
        echo "   Fedora: sudo dnf install git"
        echo "   Arch: sudo pacman -S git"
    elif [[ "$OS" == "macos" ]]; then
        echo "   Homebrew: brew install git"
        echo "   Xcode: xcode-select --install"
    fi
    echo "   Or download from: https://git-scm.com"
    echo "   Then run this installer again"
    echo
    echo "2. Download the source code manually:"
    echo "   - Go to: https://github.com/LightWraith8268/Docx2Shelf"
    echo "   - Click \"Code\" → \"Download ZIP\""
    echo "   - Extract and run: $PYTHON_CMD -m pip install --user -e ."
    echo
    echo "Press any key to continue..."
    read -n 1 -s
}

# Function to show installation failed guidance
show_installation_failed_guidance() {
    echo
    echo -e "${RED}[ERROR] All installation methods failed${NC}"
    echo
    echo "Diagnostic information:"
    echo "Python version:"
    $PYTHON_CMD --version
    echo
    echo "Pip version:"
    $PYTHON_CMD -m pip --version
    echo
    echo "Git available: $([[ $GIT_AVAILABLE -eq 1 ]] && echo "Yes" || echo "No")"
    echo
    echo "Possible solutions:"
    echo "1. Check your internet connection"
    echo "2. Update pip: $PYTHON_CMD -m pip install --upgrade pip"
    echo "3. Clear pip cache: $PYTHON_CMD -m pip cache purge"
    echo "4. Try manual installation from source"
    echo "5. Contact support with the information above"
    echo
    echo "Press any key to continue..."
    read -n 1 -s
}

# Variables
CUSTOM_INSTALL_PATH=""
SHOW_HELP=""
PYTHON_CMD=""
VERIFICATION_RESULT=""
CUSTOM_INSTALL_SUCCESS=""
INSTALLATION_SUCCESS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=1
            shift
            ;;
        --path)
            CUSTOM_INSTALL_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show help if requested
if [[ -n "$SHOW_HELP" ]]; then
    echo "Docx2Shelf Installer for macOS and Linux"
    echo
    echo "Usage:"
    echo "  ./install.sh                      - Standard installation"
    echo "  ./install.sh --path \"/opt/tools\"  - Install to custom location"
    echo "  ./install.sh --help               - Show this help"
    echo
    echo "Standard installation uses system-appropriate locations:"
    echo "  - Python: System package manager or user profile"
    echo "  - Docx2Shelf: pipx managed location or user site-packages"
    echo
    echo "Custom installation allows you to specify a target directory."
    echo
    echo "Press any key to continue..."
    read -n 1 -s
    exit 0
fi

echo "========================================"
echo "   Docx2Shelf Unix/Linux Installer"
echo "========================================"
echo

if [[ -n "$CUSTOM_INSTALL_PATH" ]]; then
    echo -e "${BLUE}Custom installation path: $CUSTOM_INSTALL_PATH${NC}"
    echo
fi

# Detect operating system
OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

echo -e "${BLUE}Detected OS: $OS${NC}"
echo

# Function to install Python on Linux
install_python_linux() {
    echo
    echo "========================================"
    echo "   Installing Python Automatically"
    echo "========================================"
    echo

    # Try different package managers
    if command -v apt-get &> /dev/null; then
        echo "Using apt (Debian/Ubuntu)..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        echo "Using yum (RHEL/CentOS)..."
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        echo "Using dnf (Fedora)..."
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        echo "Using pacman (Arch Linux)..."
        sudo pacman -S python python-pip
    elif command -v zypper &> /dev/null; then
        echo "Using zypper (openSUSE)..."
        sudo zypper install -y python3 python3-pip
    else
        echo -e "${RED}No supported package manager found${NC}"
        echo "Please install Python 3.11+ manually from your distribution's package manager"
        return 1
    fi

    echo -e "${GREEN}Python installation completed${NC}"
    return 0
}

# Function to get latest version from GitHub API
get_latest_version() {
    LATEST_VERSION=""
    echo "Querying GitHub API for latest release..."

    # Try using curl first, then wget as fallback
    if command -v curl &> /dev/null; then
        LATEST_VERSION=$(curl -s https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest | grep -o '"tag_name": *"[^"]*"' | sed 's/"tag_name": *"\([^"]*\)"/\1/' 2>/dev/null || echo "")
    elif command -v wget &> /dev/null; then
        LATEST_VERSION=$(wget -qO- https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest | grep -o '"tag_name": *"[^"]*"' | sed 's/"tag_name": *"\([^"]*\)"/\1/' 2>/dev/null || echo "")
    else
        echo "[Note] Neither curl nor wget available for version checking"
    fi

    if [[ -z "$LATEST_VERSION" ]]; then
        echo "[Note] Could not retrieve version info from GitHub API"
    else
        echo "Found latest release: $LATEST_VERSION"
    fi
}

# Function to check current installed version
check_current_version() {
    CURRENT_VERSION=""
    if command -v docx2shelf &> /dev/null; then
        # Try to get version, handle different output formats
        VERSION_OUTPUT=$(docx2shelf --version 2>/dev/null | head -n1)
        if [[ -n "$VERSION_OUTPUT" ]]; then
            # Extract version number from output like "docx2shelf 1.4.3"
            CURRENT_VERSION=$(echo "$VERSION_OUTPUT" | awk '{print $2}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' || echo "")
        fi
    fi
}

# Function to compare two version strings
compare_versions() {
    local v1="$1"
    local v2="$2"
    VERSION_COMPARISON=0

    # Remove 'v' prefix if present
    v1="${v1#v}"
    v2="${v2#v}"

    # Use sort with version comparison if available
    if command -v sort &> /dev/null && sort --version-sort /dev/null &> /dev/null; then
        if [[ "$(printf '%s\n%s\n' "$v1" "$v2" | sort --version-sort | head -n1)" == "$v1" ]]; then
            if [[ "$v1" == "$v2" ]]; then
                VERSION_COMPARISON=0  # Equal
            else
                VERSION_COMPARISON=1  # v2 is newer
            fi
        else
            VERSION_COMPARISON=-1  # v1 is newer
        fi
    else
        # Fallback: simple string comparison
        if [[ "$v1" == "$v2" ]]; then
            VERSION_COMPARISON=0
        elif [[ "$v1" < "$v2" ]]; then
            VERSION_COMPARISON=1
        else
            VERSION_COMPARISON=-1
        fi
    fi
}

# Check for Python
echo "Checking for Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if it's Python 3
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "")
    if [[ "$PYTHON_VERSION" == "3."* ]]; then
        PYTHON_CMD="python"
    else
        PYTHON_CMD=""
    fi
else
    PYTHON_CMD=""
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "${YELLOW}Python not found on this system.${NC}"
    echo
    echo "Docx2Shelf requires Python 3.11 or higher to function."
    echo

    if [[ "$OS" == "linux" ]]; then
        echo -n "Would you like to install Python automatically? (Y/n): "
        read -r AUTO_INSTALL
        if [[ "$AUTO_INSTALL" =~ ^[Nn]$ ]]; then
            echo "Installation cancelled by user."
            echo "Please install Python 3.11+ manually from your package manager"
            echo
            echo "Press any key to continue..."
            read -n 1 -s
            exit 1
        fi

        echo "Installing Python automatically..."
        if ! install_python_linux; then
            echo -e "${RED}ERROR: Failed to install Python automatically${NC}"
            echo "Please install Python 3.11+ manually from your package manager"
            echo
            echo "Press any key to continue..."
            read -n 1 -s
            exit 1
        fi

        # Re-check after installation
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}ERROR: Python installation failed or PATH not updated${NC}"
            echo "Please restart your terminal and run this installer again"
            echo "Or install Python manually from your package manager"
            echo
            echo "Press any key to continue..."
            read -n 1 -s
            exit 1
        fi
    else
        echo -e "${YELLOW}macOS detected. Please install Python manually:${NC}"
        echo "1. Download from https://python.org"
        echo "2. Or use Homebrew: brew install python@3.11"
        echo "3. Or use pyenv: pyenv install 3.11.9"
        echo
        echo "Press any key to continue..."
        read -n 1 -s
        exit 1
    fi
fi

echo -e "${GREEN}Python found: $PYTHON_CMD${NC}"

# Check Python version compatibility
echo "Checking Python version compatibility..."
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "")

if [[ -n "$PYTHON_VERSION" ]]; then
    echo "Python version: $PYTHON_VERSION"

    # Check if version is 3.11 or higher
    if $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        echo -e "${GREEN}[SUCCESS] Python version is compatible${NC}"
    else
        echo
        echo -e "${YELLOW}WARNING: Python $PYTHON_VERSION is installed but Docx2Shelf requires Python 3.11+ (current latest: Python 3.12)${NC}"
        echo
        echo "Your version: Python $PYTHON_VERSION"
        echo "Required: Python 3.11.0 or newer"
        echo
        echo -n "Would you like to continue anyway? (y/N): "
        read -r CONTINUE_ANYWAY
        if [[ ! "$CONTINUE_ANYWAY" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled. Please upgrade Python to 3.11+ and try again."
            echo
            echo "Press any key to continue..."
            read -n 1 -s
            exit 1
        fi
        echo "Continuing with current Python version..."
        echo "Note: Some features may not work correctly with Python $PYTHON_VERSION"
    fi
else
    echo -e "${YELLOW}Warning: Could not determine Python version${NC}"
fi

# Check for Git availability
echo "Checking for Git installation..."
if command -v git &> /dev/null; then
    echo -e "${GREEN}[SUCCESS] Git is available${NC}"
    GIT_AVAILABLE=1
else
    echo -e "${YELLOW}[WARNING] Git not found in PATH${NC}"
    echo "Git is required to install from GitHub repository."
    echo
    echo "Please install Git:"
    if [[ "$OS" == "linux" ]]; then
        echo "  Ubuntu/Debian: sudo apt-get install git"
        echo "  CentOS/RHEL: sudo yum install git"
        echo "  Fedora: sudo dnf install git"
        echo "  Arch: sudo pacman -S git"
    elif [[ "$OS" == "macos" ]]; then
        echo "  Homebrew: brew install git"
        echo "  Xcode: xcode-select --install"
    fi
    echo "  Or download from: https://git-scm.com"
    echo
    GIT_AVAILABLE=0
fi

# Check if pipx is available
echo "Checking for pipx..."
if command -v pipx &> /dev/null; then
    echo -e "${GREEN}pipx is available${NC}"
else
    echo "pipx not found. Installing pipx..."
    $PYTHON_CMD -m pip install --user pipx
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}ERROR: Failed to install pipx${NC}"
        echo
        echo "Press any key to continue..."
        read -n 1 -s
        exit 1
    fi

    # Ensure pipx is on PATH
    $PYTHON_CMD -m pipx ensurepath

    # Add pipx to current session PATH
    PIPX_BIN_DIR=$($PYTHON_CMD -c "import os; print(os.path.join(os.path.expanduser('~'), '.local', 'bin'))" 2>/dev/null)
    if [[ -d "$PIPX_BIN_DIR" ]]; then
        export PATH="$PATH:$PIPX_BIN_DIR"
        echo "Added $PIPX_BIN_DIR to current session PATH"
    fi
fi

# Get latest version information from GitHub
echo
echo "Checking latest version from GitHub..."
get_latest_version
if [[ -n "$LATEST_VERSION" ]]; then
    echo -e "${GREEN}Latest version available: $LATEST_VERSION${NC}"
else
    echo -e "${YELLOW}[Note] Could not determine latest version (continuing anyway)${NC}"
fi

# Check if docx2shelf is already installed and compare versions
echo "Checking current installation..."
check_current_version
if [[ -n "$CURRENT_VERSION" ]]; then
    echo "Current version installed: $CURRENT_VERSION"

    if [[ -n "$LATEST_VERSION" ]]; then
        compare_versions "$CURRENT_VERSION" "$LATEST_VERSION"
        if [[ $VERSION_COMPARISON -eq 0 ]]; then
            echo
            echo -e "${GREEN}[INFO] You already have the latest version ($CURRENT_VERSION) installed.${NC}"
            echo -n "Would you like to reinstall anyway? (y/N): "
            read -r FORCE_REINSTALL
            if [[ ! "$FORCE_REINSTALL" =~ ^[Yy]$ ]]; then
                echo "Installation cancelled - already up to date."
                echo
                echo -n "Delete this installer script? (Y/n): "
                read -r DELETE_SCRIPT
                if [[ ! "$DELETE_SCRIPT" =~ ^[Nn]$ ]]; then
                    echo "Deleting installer script..."
                    rm "$0" 2>/dev/null || echo "Note: Could not delete script automatically"
                fi
                exit 0
            fi
            echo "Proceeding with reinstallation..."
        elif [[ $VERSION_COMPARISON -eq 1 ]]; then
            echo -e "${BLUE}[INFO] Newer version available: $LATEST_VERSION (currently have $CURRENT_VERSION)${NC}"
            echo "Proceeding with upgrade..."
        else
            echo -e "${YELLOW}[INFO] You have a newer version ($CURRENT_VERSION) than the latest release ($LATEST_VERSION)${NC}"
            echo "This may be a development version."
            echo -n "Continue with installation anyway? (y/N): "
            read -r CONTINUE_ANYWAY
            if [[ ! "$CONTINUE_ANYWAY" =~ ^[Yy]$ ]]; then
                echo "Installation cancelled."
                echo
                echo -n "Delete this installer script? (Y/n): "
                read -r DELETE_SCRIPT
                if [[ ! "$DELETE_SCRIPT" =~ ^[Nn]$ ]]; then
                    echo "Deleting installer script..."
                    rm "$0" 2>/dev/null || echo "Note: Could not delete script automatically"
                fi
                exit 0
            fi
        fi
    fi
else
    echo "No current installation detected."
fi

# Install Docx2Shelf with enhanced error handling
echo
echo "Installing Docx2Shelf from GitHub (latest version)..."
echo

if [[ $GIT_AVAILABLE -eq 1 ]]; then
    # Method 1: Try from GitHub (primary source)
    echo "Method 1: Installing from GitHub repository..."
    if [[ -n "$CUSTOM_INSTALL_PATH" ]]; then
        echo "Installing to custom path: $CUSTOM_INSTALL_PATH"
        mkdir -p "$CUSTOM_INSTALL_PATH"
        if $PYTHON_CMD -m pip install --target "$CUSTOM_INSTALL_PATH" git+https://github.com/LightWraith8268/Docx2Shelf.git; then
            echo -e "${GREEN}[SUCCESS] Installation successful to custom path${NC}"
            CUSTOM_INSTALL_SUCCESS=1
            INSTALLATION_SUCCESS=1
        else
            echo -e "${RED}[ERROR] Custom path installation failed${NC}"
        fi
    else
        if $PYTHON_CMD -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git; then
            echo -e "${GREEN}[SUCCESS] Installation successful from GitHub${NC}"
            INSTALLATION_SUCCESS=1
        else
            echo -e "${RED}[ERROR] GitHub installation failed. Trying alternative methods...${NC}"
        fi
    fi

    # Method 2: Try with pipx from GitHub (if primary method failed)
    if [[ -z "$INSTALLATION_SUCCESS" ]]; then
        echo "Method 2: Installing with pipx from GitHub..."
        if pipx install git+https://github.com/LightWraith8268/Docx2Shelf.git --force; then
            echo -e "${GREEN}[SUCCESS] Installation successful with pipx${NC}"
            INSTALLATION_SUCCESS=1
        else
            echo -e "${RED}[ERROR] pipx installation failed. Trying alternative methods...${NC}"
        fi
    fi

    # Method 3: Try installing dependencies separately then from GitHub
    if [[ -z "$INSTALLATION_SUCCESS" ]]; then
        echo "Method 3: Installing dependencies first..."
        echo "Installing core dependencies..."
        if $PYTHON_CMD -m pip install --user ebooklib python-docx lxml; then
            echo "Dependencies installed, now installing docx2shelf..."
            if $PYTHON_CMD -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git --no-deps; then
                echo -e "${GREEN}[SUCCESS] Installation successful with separate dependencies${NC}"
                INSTALLATION_SUCCESS=1
            else
                echo -e "${RED}[ERROR] GitHub install failed even with dependencies${NC}"
            fi
        else
            echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
        fi
    fi

    # Method 4: Try development/editable install from local directory
    if [[ -z "$INSTALLATION_SUCCESS" && -f "pyproject.toml" ]]; then
        echo "Method 4: Checking for local source..."
        echo "Found local source, installing in development mode..."
        if $PYTHON_CMD -m pip install --user -e .; then
            echo -e "${GREEN}[SUCCESS] Installation successful from local source${NC}"
            INSTALLATION_SUCCESS=1
        else
            echo -e "${RED}[ERROR] Local source installation failed${NC}"
        fi
    fi
else
    echo "Method 1: Skipping GitHub installation (Git not available)"
    echo "Method 2: Skipping pipx GitHub install (Git not available)"

    # Method 3: Try installing dependencies separately (Git-free fallback)
    echo "Method 3: Installing core dependencies separately..."
    if $PYTHON_CMD -m pip install --user ebooklib python-docx lxml; then
        echo -e "${YELLOW}[INFO]  Dependencies installed, but cannot install docx2shelf without Git${NC}"
        echo "Please install Git and run the installer again, or install docx2shelf manually"
        show_manual_install_guidance
        exit 1
    else
        echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
    fi

    # Method 4: Try development/editable install from local directory
    if [[ -f "pyproject.toml" ]]; then
        echo "Method 4: Checking for local source..."
        echo "Found local source, installing in development mode..."
        if $PYTHON_CMD -m pip install --user -e .; then
            echo -e "${GREEN}[SUCCESS] Installation successful from local source${NC}"
            INSTALLATION_SUCCESS=1
        else
            echo -e "${RED}[ERROR] Local source installation failed${NC}"
        fi
    fi
fi

# Check if installation was successful
if [[ -z "$INSTALLATION_SUCCESS" ]]; then
    # All methods failed
    if [[ $GIT_AVAILABLE -eq 0 ]]; then
        show_manual_install_guidance
    else
        show_installation_failed_guidance
    fi
    exit 1
fi

# Verify installation and update PATH if needed
echo "Verifying installation..."

if [[ -n "$CUSTOM_INSTALL_SUCCESS" ]]; then
    # For custom installations, add the path and create a launcher script
    echo "Setting up custom installation..."
    DOCX2SHELF_SCRIPT="$CUSTOM_INSTALL_PATH/docx2shelf"

    # Create a launcher script
    cat > "$DOCX2SHELF_SCRIPT" << EOF
#!/bin/bash
$PYTHON_CMD "$CUSTOM_INSTALL_PATH/docx2shelf/cli.py" "\$@"
EOF
    chmod +x "$DOCX2SHELF_SCRIPT"

    # Add custom path to PATH for current session
    export PATH="$PATH:$CUSTOM_INSTALL_PATH"

    # Add to shell configuration files
    SHELL_CONFIG=""
    if [[ -n "$BASH_VERSION" ]]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [[ -n "$ZSH_VERSION" ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    fi

    if [[ -n "$SHELL_CONFIG" && -f "$SHELL_CONFIG" ]]; then
        if ! grep -q "$CUSTOM_INSTALL_PATH" "$SHELL_CONFIG"; then
            echo "export PATH=\"\$PATH:$CUSTOM_INSTALL_PATH\"" >> "$SHELL_CONFIG"
            echo "Added $CUSTOM_INSTALL_PATH to $SHELL_CONFIG"
        fi
    fi

    echo -e "${GREEN}[SUCCESS] Custom installation configured${NC}"
else
    # Standard verification
    if command -v docx2shelf &> /dev/null; then
        echo -e "${GREEN}[SUCCESS] docx2shelf found on PATH${NC}"
    else
        echo "docx2shelf not found on PATH. Attempting to locate and add to PATH..."

        # Find potential paths where docx2shelf might be installed
        FOUND_PATH=""

        # Check user local bin
        USER_LOCAL_BIN="$HOME/.local/bin"
        if [[ -f "$USER_LOCAL_BIN/docx2shelf" ]]; then
            FOUND_PATH="$USER_LOCAL_BIN"
        fi

        # Check pipx bin directory
        if [[ -z "$FOUND_PATH" ]]; then
            PIPX_BIN_DIR=$($PYTHON_CMD -c "import os; print(os.path.join(os.path.expanduser('~'), '.local', 'bin'))" 2>/dev/null)
            if [[ -f "$PIPX_BIN_DIR/docx2shelf" ]]; then
                FOUND_PATH="$PIPX_BIN_DIR"
            fi
        fi

        if [[ -n "$FOUND_PATH" ]]; then
            echo "Found docx2shelf at: $FOUND_PATH"

            # Add to current session
            export PATH="$PATH:$FOUND_PATH"

            # Add to shell configuration files
            SHELL_CONFIG=""
            if [[ -n "$BASH_VERSION" ]]; then
                SHELL_CONFIG="$HOME/.bashrc"
            elif [[ -n "$ZSH_VERSION" ]]; then
                SHELL_CONFIG="$HOME/.zshrc"
            fi

            if [[ -n "$SHELL_CONFIG" && -f "$SHELL_CONFIG" ]]; then
                if ! grep -q "$FOUND_PATH" "$SHELL_CONFIG"; then
                    echo "export PATH=\"\$PATH:$FOUND_PATH\"" >> "$SHELL_CONFIG"
                    echo "Added $FOUND_PATH to $SHELL_CONFIG"
                fi
            fi

            echo -e "${GREEN}PATH updated successfully${NC}"
        else
            echo -e "${YELLOW}WARNING: Could not locate docx2shelf executable${NC}"
            echo "You may need to manually add the installation directory to your PATH"
        fi
    fi
fi

# Final verification
echo
echo "Final verification..."
if command -v docx2shelf &> /dev/null && docx2shelf --help &> /dev/null; then
    VERIFICATION_RESULT=0
    echo -e "${GREEN}[SUCCESS] docx2shelf is working correctly${NC}"
else
    VERIFICATION_RESULT=1
    echo -e "${YELLOW}[WARNING]  docx2shelf command verification failed${NC}"
fi

if [[ $VERIFICATION_RESULT -eq 0 ]]; then
    echo
    echo "========================================"
    echo "    Installation Successful!"
    echo "========================================"
    echo
    echo -e "${GREEN}✅ Docx2Shelf is now installed and available globally.${NC}"
    if [[ -n "$CUSTOM_INSTALL_PATH" ]]; then
        echo -e "${BLUE}📁 Custom installation location: $CUSTOM_INSTALL_PATH${NC}"
    fi
    echo -e "${BLUE}📦 Installation source: GitHub repository${NC}"

    # Ask about installing optional tools
    echo
    echo "========================================"
    echo "    Optional Tools Installation"
    echo "========================================"
    echo
    echo -e "${BLUE}Docx2Shelf works best with these additional tools:${NC}"
    echo
    echo -e "${GREEN}1. PANDOC${NC} - High-quality document conversion (RECOMMENDED)"
    echo "   - Provides superior DOCX to EPUB conversion"
    echo "   - Handles complex formatting and tables"
    echo "   - Essential for professional results"
    echo
    echo -e "${GREEN}2. EPUBCHECK${NC} - Industry-standard EPUB validation"
    echo "   - Validates EPUB files for compliance"
    echo "   - Required for publishing to most stores"
    echo "   - Catches formatting and structure issues"
    echo

    echo -n "Would you like to install these tools? (Y/n): "
    read -r INSTALL_TOOLS
    if [[ ! "$INSTALL_TOOLS" =~ ^[Nn]$ ]]; then
        echo
        echo "Installing optional tools..."
        install_optional_tools
    else
        echo
        echo "Skipping optional tools installation."
        echo "You can install them later using: docx2shelf tools install"
    fi

    # Download uninstall script for future use
    echo
    echo "Downloading uninstall script for future use..."
    if curl -sSL -o uninstall.sh "https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/uninstall.sh" 2>/dev/null; then
        chmod +x uninstall.sh 2>/dev/null
        echo -e "${GREEN}[SUCCESS] Uninstall script downloaded to: uninstall.sh${NC}"
        echo "To uninstall later, simply run: ./uninstall.sh"
    else
        echo -e "${YELLOW}[WARNING] Could not download uninstall script.${NC}"
        echo "You can download it later from: https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/uninstall.sh"
    fi

    # Show installed version
    echo
    echo "Installed version:"
    if command -v docx2shelf &> /dev/null; then
        docx2shelf --version 2>/dev/null || echo "[Note] Version information not available yet"
    else
        echo "[Note] Version command not accessible yet"
    fi

    echo
    echo "========================================"
    echo "    Quick Start Guide"
    echo "========================================"
    echo
    echo -e "${GREEN}** INTERACTIVE MODE (RECOMMENDED) **${NC}"
    echo "  docx2shelf                 - Launch full interactive GUI"
    echo "  docx2shelf interactive     - Launch interactive menu"
    echo "  docx2shelf wizard          - Step-by-step conversion wizard"
    echo
    echo -e "${BLUE}** COMMAND LINE MODE **${NC}"
    echo "  docx2shelf --help          - Show all available commands"
    echo "  docx2shelf build           - Build EPUB from DOCX"
    echo "  docx2shelf doctor          - Environment diagnostics"
    echo "  docx2shelf validate        - Validate EPUB files"
    echo "  docx2shelf quality         - Quality analysis"
    echo "  docx2shelf convert         - Format conversion"
    echo
    echo -e "${YELLOW}** NEW USER? Start with: docx2shelf **${NC}"
    echo
    echo "If you're using a new terminal window and get \"command not found\","
    echo "restart your terminal to refresh the PATH."
    echo
    echo -n "Delete this installer script? (Y/n): "
    read -r DELETE_SCRIPT
    if [[ ! "$DELETE_SCRIPT" =~ ^[Nn]$ ]]; then
        echo "Deleting installer script..."
        echo "Thank you for using Docx2Shelf!"
        rm "$0" 2>/dev/null || echo "Note: Could not delete script automatically"
    fi
    echo
    echo "Press any key to continue..."
    read -n 1 -s
else
    echo
    echo "========================================"
    echo "    Installation Issues Detected"
    echo "========================================"
    echo
    echo "Docx2Shelf was installed but may not be on PATH."
    echo
    echo "Solutions:"
    echo "1. Restart your terminal/shell"
    echo "2. Source your shell config: source ~/.bashrc (or ~/.zshrc)"
    echo "3. Log out and log back in"
    echo
    echo "If issues persist, you can run docx2shelf directly:"
    if [[ -n "$FOUND_PATH" ]]; then
        echo "  \"$FOUND_PATH/docx2shelf\" --help"
    fi
    echo
    echo "Press any key to continue..."
    read -n 1 -s
fi

# Function to install optional tools
install_optional_tools() {
    echo "Installing Pandoc..."
    if docx2shelf tools install pandoc; then
        echo -e "${GREEN}[SUCCESS] Pandoc installed successfully${NC}"
    else
        echo -e "${YELLOW}[WARNING] Pandoc installation failed - you can try again later with: docx2shelf tools install pandoc${NC}"
    fi

    echo
    echo "Installing EPUBCheck..."
    if docx2shelf tools install epubcheck; then
        echo -e "${GREEN}[SUCCESS] EPUBCheck installed successfully${NC}"
    else
        echo -e "${YELLOW}[WARNING] EPUBCheck installation failed - you can try again later with: docx2shelf tools install epubcheck${NC}"
    fi

    echo
    echo "Optional tools installation completed."
}