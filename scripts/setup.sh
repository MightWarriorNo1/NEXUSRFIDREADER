#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}[SETUP]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Get current directory and user info
cur_dir="$(cd "$(dirname "$0")" && pwd)"
project_root="$(cd "${cur_dir}/.." && pwd)"
user="$(id -u -n)"

echo "============================================================"
print_header "Setting up Nexus RFID Reader Application"
echo "============================================================"
print_status "Project root: ${project_root}"
print_status "User: ${user}"
echo "============================================================"

# Update system packages
print_step "Updating system packages..."
sudo apt update -y
print_success "System packages updated"

# Install system dependencies for Qt GUI applications
print_step "Installing Qt and GUI dependencies..."
sudo apt install -y \
    libxcb-cursor0 \
    libxcb-cursor-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    build-essential \
    cmake \
    pkg-config \
    libgl1-mesa-dev \
    libglib2.0-dev
print_success "Qt and GUI dependencies installed"

# Install additional system dependencies for RFID and networking
print_step "Installing RFID and networking dependencies..."
sudo apt install -y \
    libusb-1.0-0-dev \
    libusb-1.0-0 \
    usbutils \
    network-manager \
    dhcpcd5 \
    i2c-tools \
    python3-serial \
    python3-requests \
    python3-numpy
print_success "RFID and networking dependencies installed"

# Install Python dependencies globally (not in venv)
print_step "Installing Python dependencies globally..."
sudo pip3 install --break-system-packages -U pip
print_success "pip updated successfully"

# Install PySide6 first as it's often a dependency for other packages
print_step "Installing PySide6 (Qt for Python)..."
sudo pip3 install --break-system-packages PySide6
print_success "PySide6 installed successfully"

# Install other Python dependencies
print_step "Installing remaining Python dependencies..."
sudo pip3 install --break-system-packages -r "${project_root}/requirements.txt"
print_success "All Python dependencies installed"

# Make scripts executable
print_step "Making scripts executable..."
chmod +x "${project_root}/scripts/run_app.sh"
chmod +x "${project_root}/scripts/install_service.sh"
chmod +x "${project_root}/scripts/uninstall_service.sh"
print_success "Scripts made executable"

# Install the systemd service
print_step "Installing systemd service..."
bash "${project_root}/scripts/install_service.sh"
print_success "Systemd service installed"

# Enable I2C interface (useful for RFID readers)
print_step "Enabling I2C interface..."
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    print_warning "I2C enabled. Reboot required for changes to take effect."
else
    print_success "I2C interface already enabled"
fi

# Disable virtual keyboard (for kiosk mode)
print_step "Disabling virtual keyboard..."
sudo raspi-config nonint do_squeekboard S3 2>/dev/null && print_success "Virtual keyboard disabled" || print_warning "Virtual keyboard already disabled or not available"

# Set up GUI environment for the user
print_step "Setting up GUI environment..."
mkdir -p "/home/${user}/.config"
mkdir -p "/home/${user}/.local/share/applications"

# Create desktop entry for manual launch (optional)
cat > "/home/${user}/.local/share/applications/nexus-rfid.desktop" <<EOL
[Desktop Entry]
Name=Nexus RFID Reader
Comment=Nexus RFID Reader Application
Exec=${project_root}/scripts/run_app.sh
Icon=${project_root}/ui/img/icon.ico
Terminal=false
Type=Application
Categories=Utility;
EOL

# Set proper permissions
chmod +x "/home/${user}/.local/share/applications/nexus-rfid.desktop"
print_success "GUI environment configured"

# Check if service is running
print_step "Checking service status..."
if systemctl is-active --quiet nexusrfid.service; then
    print_success "Nexus RFID service is running"
else
    print_warning "Nexus RFID service is not running. Starting..."
    sudo systemctl start nexusrfid.service
    if systemctl is-active --quiet nexusrfid.service; then
        print_success "Service started successfully"
    else
        print_error "Failed to start service"
    fi
fi

# Display final status
echo ""
echo "============================================================"
print_header "Setup Completed Successfully!"
echo "============================================================"
print_status "Service status:"
sudo systemctl status nexusrfid.service --no-pager -l
echo ""
echo "============================================================"
print_header "Useful Commands:"
echo "============================================================"
print_status "Check logs:      sudo journalctl -u nexusrfid.service -f"
print_status "Restart service: sudo systemctl restart nexusrfid.service"
print_status "Stop service:    sudo systemctl stop nexusrfid.service"
print_status "Uninstall:       bash ${project_root}/scripts/uninstall_service.sh"
echo ""
print_success "Desktop application available in Applications menu"
print_success "The service will automatically start on boot"
echo "============================================================"
