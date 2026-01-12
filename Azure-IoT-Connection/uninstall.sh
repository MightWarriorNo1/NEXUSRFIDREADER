#!/bin/bash

# Azure IoT Connection Service - Uninstall Script
# This script completely removes the Azure IoT service and cleans up all files

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to stop and disable service
stop_service() {
    print_status "Stopping and disabling Azure IoT service..."
    
    # Stop the service if it's running
    if sudo systemctl is-active --quiet azure-iot.service; then
        print_status "Stopping azure-iot.service..."
        sudo systemctl stop azure-iot.service
        print_success "Service stopped"
    else
        print_status "Service is not running"
    fi
    
    # Disable the service
    if sudo systemctl is-enabled --quiet azure-iot.service; then
        print_status "Disabling azure-iot.service..."
        sudo systemctl disable azure-iot.service
        print_success "Service disabled"
    else
        print_status "Service is not enabled"
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    print_success "Systemd reloaded"
}

# Function to remove systemd service file
remove_service_file() {
    print_status "Removing systemd service file..."
    
    if [[ -f "/etc/systemd/system/azure-iot.service" ]]; then
        rm -f /etc/systemd/system/azure-iot.service
        print_success "Service file removed"
    else
        print_status "Service file not found"
    fi
}

# Function to remove service directories and files
remove_service_files() {
    print_status "Removing service directories and files..."
    
    # Remove service directory
    if [[ -d "/opt/azure-iot" ]]; then
        rm -rf /opt/azure-iot
        print_success "Service directory removed"
    else
        print_status "Service directory not found"
    fi
    
    # Remove configuration directory
    if [[ -d "/etc/azureiotpnp" ]]; then
        rm -rf /etc/azureiotpnp
        print_success "Configuration directory removed"
    else
        print_status "Configuration directory not found"
    fi
}

# Function to remove log files
remove_logs() {
    print_status "Removing log files..."
    
    # Remove service log file
    if [[ -f "/var/log/azure-iot-service.log" ]]; then
        rm -f /var/log/azure-iot-service.log
        print_success "Service log file removed"
    else
        print_status "Service log file not found"
    fi
    
    # Remove systemd journal entries (optional)
    print_status "Cleaning systemd journal entries..."
    sudo journalctl --vacuum-time=1s --unit=azure-iot.service > /dev/null 2>&1 || true
    print_success "Systemd journal cleaned"
}

# Function to remove Python dependencies
remove_python_dependencies() {
    print_status "Checking Python dependencies..."
    
    # Ask user if they want to remove Python dependencies
    echo
    echo "============================================================"
    echo "Python Dependencies Removal"
    echo "============================================================"
    echo "The following Python packages were installed for this service:"
    echo "• azure-iot-device"
    echo
    echo "Do you want to remove these packages? (y/N)"
    echo "Note: This may affect other services that use these packages."
    echo "============================================================"
    
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Removing Azure IoT Device SDK..."
        pip3 uninstall -y azure-iot-device --break-system-packages || true
        print_success "Python dependencies removed"
    else
        print_status "Keeping Python dependencies (as requested)"
    fi
}

# Function to verify removal
verify_removal() {
    print_status "Verifying removal..."
    
    local all_removed=true
    
    # Check if service file is removed
    if [[ -f "/etc/systemd/system/azure-iot.service" ]]; then
        print_warning "Service file still exists"
        all_removed=false
    fi
    
    # Check if service directory is removed
    if [[ -d "/opt/azure-iot" ]]; then
        print_warning "Service directory still exists"
        all_removed=false
    fi
    
    # Check if configuration directory is removed
    if [[ -d "/etc/azureiotpnp" ]]; then
        print_warning "Configuration directory still exists"
        all_removed=false
    fi
    
    # Check if log file is removed
    if [[ -f "/var/log/azure-iot-service.log" ]]; then
        print_warning "Log file still exists"
        all_removed=false
    fi
    
    # Check if service is still enabled
    if sudo systemctl is-enabled --quiet azure-iot.service 2>/dev/null; then
        print_warning "Service is still enabled"
        all_removed=false
    fi
    
    if [[ "$all_removed" == true ]]; then
        print_success "All service files and configurations have been removed"
    else
        print_warning "Some files may still exist. You may need to remove them manually."
    fi
    
    return $([[ "$all_removed" == true ]] && echo 0 || echo 1)
}

# Function to show final summary
show_final_summary() {
    echo
    echo "============================================================"
    echo "Uninstall Complete!"
    echo "============================================================"
    echo "The Azure IoT service has been removed from your system."
    echo
    echo "What was removed:"
    echo "• Systemd service file"
    echo "• Service scripts and files"
    echo "• Configuration files"
    echo "• Log files"
    echo "• Systemd journal entries"
    echo "• Update scripts and files"
    echo
    echo "What was NOT removed (by default):"
    echo "• Python packages (unless you chose to remove them)"
    echo "• System packages (python3, pip3)"
    echo
    echo "If you want to completely clean up Python packages, run:"
    echo "  sudo pip3 uninstall -y azure-iot-device azure-storage-blob --break-system-packages"
    echo "============================================================"
}

# Function to confirm uninstall
confirm_uninstall() {
    echo
    echo "============================================================"
    echo "Azure IoT Service Uninstall"
    echo "============================================================"
    echo "This script will completely remove the Azure IoT service from your system."
    echo
    echo "The following will be removed:"
    echo "• Azure IoT service (stopped and disabled)"
    echo "• All service files and scripts"
    echo "• Configuration files"
    echo "• Log files"
    echo "• Systemd service configuration"
    echo
    echo "WARNING: This action cannot be undone!"
    echo "============================================================"
    echo
    echo "Are you sure you want to continue? (yes/no): "
    
    read -r response
    if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Uninstall cancelled."
        exit 0
    fi
    
    echo
    echo "Proceeding with uninstall..."
}

# Main execution
main() {
    echo "============================================================"
    echo "Azure IoT Connection Service - Uninstall"
    echo "============================================================"
    echo "This script will completely remove your Azure IoT service."
    echo "============================================================"
    
    # Check if running as root
    check_root
    
    # Confirm uninstall
    confirm_uninstall
    
    # Stop and disable service
    stop_service
    
    # Remove systemd service file
    remove_service_file
    
    # Remove service files and directories
    remove_service_files
    
    # Remove log files
    remove_logs
    
    # Remove Python dependencies (optional)
    remove_python_dependencies
    
    # Verify removal
    verify_removal
    
    # Show final summary
    show_final_summary
}

# Run main function
main "$@"
