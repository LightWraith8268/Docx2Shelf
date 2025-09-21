#!/bin/bash

# docx2shelf Universal Uninstaller
# Compatible with Linux, macOS, and other Unix-like systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_info() {
    print_status "$BLUE" "[INFO] $1"
}

print_success() {
    print_status "$GREEN" "[SUCCESS] $1"
}

print_warning() {
    print_status "$YELLOW" "[WARNING] $1"
}

print_error() {
    print_status "$RED" "[ERROR] $1"
}

print_skip() {
    print_status "$YELLOW" "[SKIP] $1"
}

echo "========================================"
echo "     docx2shelf Universal Uninstaller"
echo "========================================"
echo
echo "This script will remove docx2shelf from your system."
echo "It will attempt to uninstall from all possible installation methods."
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_info "Running with root privileges."
else
    print_info "Running as regular user. Some system-wide installations may require sudo."
fi
echo

print_info "Starting uninstall process..."
echo

# Method 1: Try pip uninstall
echo "[STEP 1] Attempting pip uninstall..."
if command -v pip >/dev/null 2>&1; then
    if pip uninstall docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via pip"
    else
        print_skip "Not installed via pip"
    fi
else
    print_skip "pip not available"
fi

# Method 2: Try pip3 uninstall
echo "[STEP 2] Attempting pip3 uninstall..."
if command -v pip3 >/dev/null 2>&1; then
    if pip3 uninstall docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via pip3"
    else
        print_skip "Not installed via pip3"
    fi
else
    print_skip "pip3 not available"
fi

# Method 3: Try pipx uninstall
echo "[STEP 3] Attempting pipx uninstall..."
if command -v pipx >/dev/null 2>&1; then
    if pipx uninstall docx2shelf >/dev/null 2>&1; then
        print_success "Removed via pipx"
    else
        print_skip "Not installed via pipx"
    fi
else
    print_skip "pipx not available"
fi

# Method 4: Try conda uninstall
echo "[STEP 4] Attempting conda uninstall..."
if command -v conda >/dev/null 2>&1; then
    if conda uninstall docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via conda"
    else
        print_skip "Not installed via conda"
    fi
else
    print_skip "conda not available"
fi

# Method 5: Try apt uninstall (Debian/Ubuntu)
echo "[STEP 5] Attempting apt uninstall..."
if command -v apt >/dev/null 2>&1; then
    if sudo apt remove python3-docx2shelf -y >/dev/null 2>&1 || sudo apt remove docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via apt"
    else
        print_skip "Not installed via apt"
    fi
else
    print_skip "apt not available"
fi

# Method 6: Try yum/dnf uninstall (RedHat/Fedora)
echo "[STEP 6] Attempting yum/dnf uninstall..."
if command -v dnf >/dev/null 2>&1; then
    if sudo dnf remove python3-docx2shelf -y >/dev/null 2>&1 || sudo dnf remove docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via dnf"
    else
        print_skip "Not installed via dnf"
    fi
elif command -v yum >/dev/null 2>&1; then
    if sudo yum remove python3-docx2shelf -y >/dev/null 2>&1 || sudo yum remove docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via yum"
    else
        print_skip "Not installed via yum"
    fi
else
    print_skip "yum/dnf not available"
fi

# Method 7: Try pacman uninstall (Arch Linux)
echo "[STEP 7] Attempting pacman uninstall..."
if command -v pacman >/dev/null 2>&1; then
    if sudo pacman -R python-docx2shelf --noconfirm >/dev/null 2>&1 || sudo pacman -R docx2shelf --noconfirm >/dev/null 2>&1; then
        print_success "Removed via pacman"
    else
        print_skip "Not installed via pacman"
    fi
else
    print_skip "pacman not available"
fi

# Method 8: Try zypper uninstall (openSUSE)
echo "[STEP 8] Attempting zypper uninstall..."
if command -v zypper >/dev/null 2>&1; then
    if sudo zypper remove python3-docx2shelf -y >/dev/null 2>&1 || sudo zypper remove docx2shelf -y >/dev/null 2>&1; then
        print_success "Removed via zypper"
    else
        print_skip "Not installed via zypper"
    fi
else
    print_skip "zypper not available"
fi

# Method 9: Try brew uninstall (macOS)
echo "[STEP 9] Attempting brew uninstall..."
if command -v brew >/dev/null 2>&1; then
    if brew uninstall docx2shelf >/dev/null 2>&1; then
        print_success "Removed via brew"
    else
        print_skip "Not installed via brew"
    fi
else
    print_skip "brew not available"
fi

# Method 10: Try MacPorts uninstall (macOS)
echo "[STEP 10] Attempting MacPorts uninstall..."
if command -v port >/dev/null 2>&1; then
    if sudo port uninstall docx2shelf >/dev/null 2>&1; then
        print_success "Removed via MacPorts"
    else
        print_skip "Not installed via MacPorts"
    fi
else
    print_skip "MacPorts not available"
fi

echo
print_info "Checking for remaining installations..."

# Check if docx2shelf command is still available
if command -v docx2shelf >/dev/null 2>&1; then
    print_warning "docx2shelf command is still available in PATH"
    print_info "This may indicate:"
    echo "  - Installation in a virtual environment that's currently active"
    echo "  - Manual installation that requires manual removal"
    echo "  - Installation via a method not covered by this script"
    echo
    print_info "To find the installation location, run:"
    echo "  which docx2shelf"
    echo "  python3 -c \"import docx2shelf; print(docx2shelf.__file__)\""
else
    print_success "docx2shelf command is no longer available"
fi

echo
print_info "Cleaning up user data directories..."

# Remove user data directories
declare -a user_dirs=(
    "$HOME/.docx2shelf"
    "$HOME/.local/share/docx2shelf"
    "$HOME/.config/docx2shelf"
    "$HOME/.cache/docx2shelf"
    "$HOME/Library/Application Support/docx2shelf"  # macOS
    "$HOME/Library/Caches/docx2shelf"              # macOS
)

for dir in "${user_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        if rm -rf "$dir" 2>/dev/null; then
            print_success "Removed user data from $dir"
        else
            print_warning "Could not remove user data from $dir"
        fi
    fi
done

echo
print_info "Checking for tools installed by docx2shelf..."

# Check for tools that may have been installed by docx2shelf
declare -a tool_dirs=(
    "$HOME/.local/share/docx2shelf-tools"
    "$HOME/.docx2shelf-tools"
    "/opt/docx2shelf-tools"
    "/usr/local/share/docx2shelf-tools"
)

for dir in "${tool_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        if rm -rf "$dir" 2>/dev/null; then
            print_success "Removed tools directory: $dir"
        else
            print_warning "Could not remove tools directory: $dir"
        fi
    fi
done

echo
echo "========================================"
echo "         Uninstall Complete"
echo "========================================"
echo
echo "Summary:"
echo "- Attempted removal via all common package managers"
echo "- Cleaned user data directories"
echo "- Removed associated tools"
echo
echo "If docx2shelf is still available, you may need to:"
echo "1. Deactivate any virtual environments"
echo "2. Manually remove from custom installation locations"
echo "3. Run this script with sudo for system-wide installations"
echo
echo "Thank you for using docx2shelf!"
echo