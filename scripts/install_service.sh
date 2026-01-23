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
    echo -e "${PURPLE}[INSTALL]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Service configuration
SERVICE_NAME="nexusrfid"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
HOME_DIR="$(cd -- "${PROJECT_ROOT}/.." && pwd)"
RUN_SCRIPT="${PROJECT_ROOT}/scripts/run_app.sh"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "============================================================"
print_header "Installing Nexus RFID Service"
echo "============================================================"
print_status "Service name: ${SERVICE_NAME}"
print_status "Project root: ${PROJECT_ROOT}"
print_status "Run script: ${RUN_SCRIPT}"
print_status "Unit file: ${UNIT_PATH}"
print_status "Home directory: ${HOME_DIR}"
echo "============================================================"

# Ensure systemd is available and target directory exists
print_step "Checking system compatibility..."
if ! command -v systemctl >/dev/null 2>&1; then
  print_error "systemd (systemctl) is not available on this system"
  exit 1
fi
print_success "systemd detected"

print_step "Creating systemd directory..."
sudo install -d -m 755 /etc/systemd/system
print_success "systemd directory ready"

print_step "Checking run script permissions..."
if [ ! -x "${RUN_SCRIPT}" ]; then
  print_warning "Run script not executable. Making executable..."
  chmod +x "${RUN_SCRIPT}"
  print_success "Run script made executable"
else
  print_success "Run script already executable"
fi

print_step "Creating systemd service unit file..."
sudo bash -c "cat > '${UNIT_PATH}'" <<UNIT
[Unit]
Description=Nexus RFID Application
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_ROOT}
# Setup internet connection via usb0 FIRST, before anything else
# This runs before network-online.target since we're setting up the connection ourselves
ExecStartPre=/bin/bash -c '/usr/bin/sudo /sbin/dhclient usb0 || true'
ExecStartPre=/bin/sleep 5
ExecStart=${RUN_SCRIPT}
Restart=always
RestartSec=5
User=${SUDO_USER:-$(whoami)}
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=${HOME_DIR}/.Xauthority
Environment=HOME=${HOME_DIR}
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

[Install]
WantedBy=graphical.target
UNIT

if [ -f "${UNIT_PATH}" ]; then
    print_success "Service unit file created successfully"
else
    print_error "Failed to create service unit file"
    exit 1
fi

print_step "Reloading systemd daemon..."
sudo systemctl daemon-reload
if [ $? -eq 0 ]; then
    print_success "systemd daemon reloaded"
else
    print_error "Failed to reload systemd daemon"
    exit 1
fi

print_step "Enabling service for automatic startup..."
sudo systemctl enable "${SERVICE_NAME}.service"
if systemctl is-enabled --quiet "${SERVICE_NAME}.service"; then
    print_success "Service enabled for startup"
else
    print_error "Failed to enable service"
    exit 1
fi

print_step "Starting service..."
sudo systemctl restart "${SERVICE_NAME}.service"

# Wait a moment for the service to start
sleep 2

# Verify service is running
if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
    print_success "Service started successfully"
else
    print_warning "Service may not have started properly"
    print_status "Check service status with: systemctl status ${SERVICE_NAME}.service"
fi

# Display final status
echo ""
echo "============================================================"
print_header "Installation Complete!"
echo "============================================================"
print_success "Service ${SERVICE_NAME}.service installed and configured"

# Show current service status
print_step "Current service status:"
sudo systemctl status "${SERVICE_NAME}.service" --no-pager -l

echo ""
echo "============================================================"
print_header "Service Management Commands:"
echo "============================================================"
print_status "Check status:    sudo systemctl status ${SERVICE_NAME}.service"
print_status "View logs:       sudo journalctl -u ${SERVICE_NAME}.service -f"
print_status "Restart service: sudo systemctl restart ${SERVICE_NAME}.service"
print_status "Stop service:    sudo systemctl stop ${SERVICE_NAME}.service"
print_status "Disable service: sudo systemctl disable ${SERVICE_NAME}.service"
echo ""
print_success "Service will automatically start on system boot"
echo "============================================================"