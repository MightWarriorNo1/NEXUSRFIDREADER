#!/bin/bash

# NexusRFIDReader Global Python Installation Script for Raspberry Pi
# This script installs Python 3.9+ and all required dependencies globally
# for running the NexusRFIDReader application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}==============================================================${NC}"
echo -e "${CYAN}        NexusRFIDReader Global Python Installer${NC}"
echo -e "${CYAN}              For Raspberry Pi${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root for global installation${NC}"
    echo -e "${YELLOW}Run: sudo bash scripts/install_python.sh${NC}"
    exit 1
fi

echo -e "${GREEN}Running as root - proceeding with global installation${NC}"
echo ""

# Detect system information
echo -e "${BLUE}System Information:${NC}"
echo -e "   ${WHITE}OS:${NC} $(lsb_release -d | cut -f2)"
echo -e "   ${WHITE}Architecture:${NC} $(uname -m)"
echo -e "   ${WHITE}Kernel:${NC} $(uname -r)"
echo ""

# Step 1: Update package lists
echo -e "${YELLOW}Step 1: Updating package lists...${NC}"
apt update
echo -e "   ${GREEN}SUCCESS${NC} Package lists updated"

# Step 2: Install system dependencies
echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    libbz2-dev \
    libreadline-dev \
    libncursesw5-dev \
    libsqlite3-dev \
    libgdbm-dev \
    liblzma-dev \
    libc6-dev \
    libx11-dev \
    libxrender-dev \
    libxtst-dev \
    libxi-dev \
    libxt-dev \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libx11-xcb1 \
    libxcb1 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    x11-xserver-utils \
    pkg-config \
    tk-dev \
    git \
    curl \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0

echo -e "   ${GREEN}SUCCESS${NC} System dependencies installed"

# Step 3: Check Python version
echo -e "${YELLOW}Step 3: Checking Python installation...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "   ${WHITE}Current Python version:${NC} $PYTHON_VERSION"

# Check if Python 3.9+ is available
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    echo -e "   ${GREEN}SUCCESS${NC} Python 3.9+ is available"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    echo -e "   ${YELLOW}WARNING: Python 3.9+ not found. Installing Python 3.9...${NC}"
    
    # Install Python 3.9 from deadsnakes PPA (for Ubuntu/Debian)
    if command -v add-apt-repository &> /dev/null; then
        add-apt-repository -y ppa:deadsnakes/ppa
        apt update
        apt install -y python3.9 python3.9-dev python3.9-venv python3.9-distutils
        apt install -y python3.9-pip || {
            # If python3.9-pip is not available, install pip manually
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3.9 get-pip.py
            rm get-pip.py
        }
        PYTHON_CMD="python3.9"
        PIP_CMD="python3.9 -m pip"
    else
        echo -e "   ${RED}ERROR: Cannot install Python 3.9. Please install manually.${NC}"
        exit 1
    fi
    echo -e "   ${GREEN}SUCCESS${NC} Python 3.9 installed"
fi

# Step 4: Install PyInstaller
echo -e "${YELLOW}Step 4: Installing PyInstaller...${NC}"

# Check if we need to use --break-system-packages flag for newer Python versions
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo -e "   ${YELLOW}WARNING: Python 3.11+ detected - using --break-system-packages flag${NC}"
    $PIP_CMD install --upgrade pip --break-system-packages
    $PIP_CMD install pyinstaller --break-system-packages
else
    $PIP_CMD install --upgrade pip
    $PIP_CMD install pyinstaller
fi
echo -e "   ${GREEN}SUCCESS${NC} PyInstaller installed"

# Step 5: Install project dependencies
echo -e "${YELLOW}Step 5: Installing project dependencies...${NC}"

# Use the same flag logic for dependencies
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    PIP_FLAG="--break-system-packages"
else
    PIP_FLAG=""
fi

if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt $PIP_FLAG
    echo -e "   ${GREEN}SUCCESS${NC} Project dependencies installed from requirements.txt"
else
    echo -e "   ${YELLOW}WARNING: requirements.txt not found. Installing common dependencies...${NC}"
    $PIP_CMD install $PIP_FLAG \
        PySide6 \
        requests \
        urllib3 \
        pyserial \
        geopy \
        geographiclib \
        pynmea2 \
        sllurp \
        schedule \
        ping3 \
        numpy
    echo -e "   ${GREEN}SUCCESS${NC} Common dependencies installed"
fi

# Step 6: Verify installation
echo -e "${YELLOW}Step 6: Verifying installation...${NC}"
echo -e "   ${WHITE}Python version:${NC} $($PYTHON_CMD --version)"
echo -e "   ${WHITE}Pip version:${NC} $($PIP_CMD --version)"
echo -e "   ${WHITE}PyInstaller version:${NC} $($PIP_CMD show pyinstaller | grep Version | cut -d' ' -f2)"

# Test PyInstaller
if $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    echo -e "   ${GREEN}SUCCESS${NC} PyInstaller import test passed"
else
    echo -e "   ${RED}ERROR: PyInstaller import test failed${NC}"
    exit 1
fi

# Test PySide6
if $PYTHON_CMD -c "import PySide6" 2>/dev/null; then
    echo -e "   ${GREEN}SUCCESS${NC} PySide6 import test passed"
else
    echo -e "   ${RED}ERROR: PySide6 import test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}            INSTALLATION COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo -e "   ${YELLOW}1.${NC} Create the package:"
echo -e "      ${WHITE}bash scripts/create_pkg_rpi.sh${NC}"
echo ""
echo -e "   ${YELLOW}2.${NC} Install the package:"
echo -e "      ${WHITE}sudo apt install ./NexusRFIDReader-1.0.deb${NC}"
echo ""
echo -e "   ${YELLOW}3.${NC} Reboot to activate:"
echo -e "      ${WHITE}sudo reboot${NC}"
echo ""
echo -e "${PURPLE}Installed Components:${NC}"
echo -e "   - Python $($PYTHON_CMD --version | cut -d' ' -f2)"
echo -e "   - PyInstaller $($PIP_CMD show pyinstaller | grep Version | cut -d' ' -f2)"
echo -e "   - All project dependencies"
echo -e "   - System libraries for GUI applications"
echo ""
echo -e "${GREEN}Ready to build the package!${NC}"
