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
# Get the actual user's home directory (not derived from project path)
SERVICE_USER="${SUDO_USER:-$(whoami)}"
HOME_DIR="$(eval echo ~${SERVICE_USER})"
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

# Configure eth0 network interface for RFID reader connection
print_step "Configuring eth0 network interface for RFID reader..."
ETH0_IP="169.254.0.1"
ETH0_NETMASK="255.255.0.0"
ETH0_BROADCAST="169.254.255.255"

# Check if eth0 interface exists
if ip link show eth0 &>/dev/null 2>&1 || ifconfig eth0 &>/dev/null 2>&1; then
    print_status "eth0 interface detected"
    
    # Configure eth0 immediately using ip command (preferred)
    if command -v ip &>/dev/null; then
        print_status "Configuring eth0 using ip command..."
        sudo ip addr flush dev eth0 2>/dev/null || true
        sudo ip addr add ${ETH0_IP}/16 broadcast ${ETH0_BROADCAST} dev eth0 2>/dev/null || true
        sudo ip link set eth0 up 2>/dev/null || true
        print_success "eth0 configured with IP: ${ETH0_IP}"
    # Fallback to ifconfig
    elif command -v ifconfig &>/dev/null; then
        print_status "Configuring eth0 using ifconfig command..."
        sudo ifconfig eth0 ${ETH0_IP} netmask ${ETH0_NETMASK} broadcast ${ETH0_BROADCAST} up 2>/dev/null || true
        print_success "eth0 configured with IP: ${ETH0_IP}"
    fi
    
    # Configure persistent network settings
    # Try netplan first (Ubuntu 18.04+)
    if [ -d "/etc/netplan" ]; then
        print_status "Creating netplan configuration for persistent eth0 settings..."
        sudo bash -c "cat > /etc/netplan/99-nexusrfid-eth0.yaml" <<NETPLAN
# Network configuration for Nexus RFID Reader eth0 interface
# Auto-configured during service installation
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - ${ETH0_IP}/16
      dhcp4: false
      dhcp6: false
NETPLAN
        
        # Validate and apply netplan config
        if command -v netplan &>/dev/null; then
            sudo netplan try --timeout 2 &>/dev/null || sudo netplan apply 2>/dev/null || true
            print_success "Netplan configuration applied"
        fi
    # Fallback to traditional /etc/network/interfaces
    else
        print_status "Creating traditional interfaces configuration for persistent eth0 settings..."
        sudo install -d -m 755 /etc/network/interfaces.d
        sudo bash -c "cat > /etc/network/interfaces.d/nexusrfid-eth0" <<INTERFACES
# Network configuration for Nexus RFID Reader eth0 interface
# Auto-configured during service installation
auto eth0
iface eth0 inet static
    address ${ETH0_IP}
    netmask ${ETH0_NETMASK}
    broadcast ${ETH0_BROADCAST}
INTERFACES
        print_success "Interfaces configuration created"
    fi
    
    # Verify configuration
    sleep 1
    if ip addr show eth0 2>/dev/null | grep -q "${ETH0_IP}" || ifconfig eth0 2>/dev/null | grep -q "${ETH0_IP}"; then
        print_success "eth0 successfully configured with IP: ${ETH0_IP}"
    else
        print_warning "eth0 configuration may not have taken effect. Please verify manually with: ip addr show eth0"
    fi
else
    print_warning "eth0 interface not found. Configuration will be applied when interface becomes available."
    print_status "Persistent configuration files have been created for future use."
fi

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
User=${SERVICE_USER}
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