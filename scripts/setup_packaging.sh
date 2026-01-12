#!/bin/bash

# NexusRFIDReader Packaging Setup Script
# This script sets up the packaging environment and makes all scripts executable

set -e  # Exit on any error

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}==============================================================${NC}"
echo -e "${CYAN}        NexusRFIDReader Packaging Setup${NC}"
echo -e "${CYAN}            Environment Setup${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Setup Information:${NC}"
echo -e "   ${WHITE}Script Directory:${NC} $SCRIPT_DIR"
echo -e "   ${WHITE}Project Root:${NC} $PROJECT_ROOT"
echo -e "   ${WHITE}Current User:${NC} $(whoami)"
echo ""

# Step 1: Make all scripts executable
echo -e "${YELLOW}Step 1: Making scripts executable...${NC}"

SCRIPTS=(
    "install_python.sh"
    "create_pkg_rpi.sh"
    "uninstall_pkg_rpi.sh"
    "autostart.sh"
    "setup_packaging.sh"
)

for script in "${SCRIPTS[@]}"; do
    script_path="$SCRIPT_DIR/$script"
    if [ -f "$script_path" ]; then
        chmod +x "$script_path"
        echo -e "   ${GREEN}SUCCESS${NC} Made executable: $script"
    else
        echo -e "   ${RED}ERROR${NC} Script not found: $script"
    fi
done

# Step 2: Verify required files exist
echo -e "${YELLOW}Step 2: Verifying required files...${NC}"

REQUIRED_FILES=(
    "main.py"
    "NexusRFIDReader.spec"
    "requirements.txt"
    "ui/img/icon.ico"
    "settings.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    file_path="$PROJECT_ROOT/$file"
    if [ -f "$file_path" ]; then
        echo -e "   ${GREEN}SUCCESS${NC} Found: $file"
    else
        echo -e "   ${RED}ERROR${NC} Missing: $file"
    fi
done

# Step 3: Check Python installation
echo -e "${YELLOW}Step 3: Checking Python installation...${NC}"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "   ${GREEN}SUCCESS${NC} Python found: $PYTHON_VERSION"
    
    # Check if Python 3.9+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo -e "   ${GREEN}SUCCESS${NC} Python version is compatible (3.9+)"
    else
        echo -e "   ${YELLOW}WARNING: Python version may need upgrade (3.9+ recommended)${NC}"
    fi
else
    echo -e "   ${RED}ERROR${NC} Python3 not found"
fi

# Step 4: Check PyInstaller
echo -e "${YELLOW}Step 4: Checking PyInstaller...${NC}"

if command -v pyinstaller &> /dev/null; then
    PYINSTALLER_VERSION=$(pyinstaller --version 2>&1)
    echo -e "   ${GREEN}SUCCESS${NC} PyInstaller found: $PYINSTALLER_VERSION"
else
    echo -e "   ${YELLOW}WARNING: PyInstaller not found - will be installed during packaging${NC}"
fi

# Step 5: Check system dependencies
echo -e "${YELLOW}Step 5: Checking system dependencies...${NC}"

SYSTEM_DEPS=(
    "dpkg-deb"
    "apt"
    "git"
    "curl"
    "wget"
)

for dep in "${SYSTEM_DEPS[@]}"; do
    if command -v "$dep" &> /dev/null; then
        echo -e "   ${GREEN}SUCCESS${NC} $dep found"
    else
        echo -e "   ${RED}ERROR${NC} $dep not found"
    fi
done

echo ""
echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}            SETUP COMPLETED!${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo -e "   ${YELLOW}1.${NC} Install Python and dependencies:"
echo -e "      ${WHITE}bash scripts/install_python.sh${NC}"
echo ""
echo -e "   ${YELLOW}2.${NC} Create the package:"
echo -e "      ${WHITE}bash scripts/create_pkg_rpi.sh${NC}"
echo ""
echo -e "   ${YELLOW}3.${NC} Install the package:"
echo -e "      ${WHITE}sudo apt install ./NexusRFIDReader-1.0.deb${NC}"
echo ""
echo -e "   ${YELLOW}4.${NC} Reboot to activate:"
echo -e "      ${WHITE}sudo reboot${NC}"
echo ""
echo -e "${PURPLE}Available Scripts:${NC}"
echo -e "   • ${WHITE}install_python.sh${NC} - Install Python and dependencies"
echo -e "   • ${WHITE}create_pkg_rpi.sh${NC} - Build the .deb package"
echo -e "   • ${WHITE}uninstall_pkg_rpi.sh${NC} - Remove the application"
echo -e "   • ${WHITE}autostart.sh${NC} - Setup desktop integration"
echo -e "   • ${WHITE}setup_packaging.sh${NC} - This setup script"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "   • ${WHITE}PACKAGING_README.md${NC} - Comprehensive packaging guide"
echo -e "   • ${WHITE}README.md${NC} - Main project documentation"
echo ""
echo -e "${GREEN}Ready to package!${NC}"
