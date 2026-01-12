#!/bin/bash

# Azure IoT Connection Service - Automated Setup Script
# This script automates the complete setup of the Azure IoT service on Raspberry Pi

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

# Function to check system requirements
check_system() {
    print_status "Checking system requirements..."
    
    # Check if running on Raspberry Pi or compatible system
    if ! grep -q "Raspberry Pi\|raspberrypi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This script is designed for Raspberry Pi. Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_status "Setup cancelled."
            exit 0
        fi
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python version: $python_version"
}

# Function to update system packages
update_system() {
    print_status "Updating system packages..."
    
    # Remove problematic Microsoft repository if it exists
    if [[ -f "/etc/apt/sources.list.d/azurecore.list" ]]; then
        print_status "Removing problematic Microsoft repository..."
        sudo rm -f /etc/apt/sources.list.d/azurecore.list
    fi
    
    # Update packages, ignoring repository errors
    sudo apt update -y || {
        print_warning "Some repositories failed to update (this is normal)"
        print_status "Continuing with setup..."
    }
    print_success "System packages updated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python and Azure IoT dependencies..."
    
    # Install Python pip if not present
    if ! command -v pip3 &> /dev/null; then
        print_status "Installing python3-pip..."
        sudo apt install -y python3-pip
    fi
    
    # Install Azure IoT Device SDK
    print_status "Installing Azure IoT Device SDK..."
    sudo pip3 install --break-system-packages azure-iot-device
    
    # Install Azure Storage Blob SDK (required for updates)
    print_status "Installing Azure Storage Blob SDK..."
    sudo pip3 install --break-system-packages azure-storage-blob
    
    print_success "Dependencies installed successfully"
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    sudo mkdir -p /opt/azure-iot
    sudo mkdir -p /etc/azureiotpnp
    sudo mkdir -p /var/log
    
    print_success "Directories created"
}

# Function to copy service files
copy_service_files() {
    print_status "Copying service files..."
    
    # Copy the main service script
    if [[ -f "iot_service.py" ]]; then
        sudo cp iot_service.py /opt/azure-iot/
        sudo chmod +x /opt/azure-iot/iot_service.py
        print_success "IoT service script copied"
    else
        print_error "iot_service.py not found in current directory"
        exit 1
    fi
    
    # Copy the device setup script
    if [[ -f "device_setup.py" ]]; then
        sudo cp device_setup.py /opt/azure-iot/
        sudo chmod +x /opt/azure-iot/device_setup.py
        print_success "Device setup script copied"
    else
        print_error "device_setup.py not found in current directory"
        exit 1
    fi
    
    # Copy the download script
    if [[ -f "download.py" ]]; then
        sudo cp download.py /opt/azure-iot/
        sudo chmod +x /opt/azure-iot/download.py
        print_success "Download script copied"
    else
        print_error "download.py not found in current directory"
        exit 1
    fi
    
    # Copy env.json if present; otherwise device_setup will prompt and create it
    if [[ -f "env.json" ]]; then
        sudo cp env.json /opt/azure-iot/
        sudo chmod 600 /opt/azure-iot/env.json
        print_success "Environment configuration copied"
    else
        print_warning "env.json not found; device_setup.py will prompt and create it."
    fi
    
    # Copy the systemd service file
    if [[ -f "azure-iot.service" ]]; then
        sudo cp azure-iot.service /etc/systemd/system/
        print_success "Systemd service file copied"
    else
        print_error "azure-iot.service not found in current directory"
        exit 1
    fi
}

# Function to create log file
setup_logging() {
    print_status "Setting up logging..."
    
    sudo touch /var/log/azure-iot-service.log
    sudo chmod 644 /var/log/azure-iot-service.log
    
    print_success "Logging setup complete"
}

# Function to run device setup interactively
run_device_setup() {
    print_status "Running device setup..."
    echo
    echo "============================================================"
    echo "Nexus Locate IoT Device Setup"
    echo "============================================================"
    echo "You will now be prompted to enter your Azure IoT configuration."
    echo "Please have the following information ready:"
    echo "- Group Primary Key (from Azure Portal)"
    echo "- DPS ID Scope (from Azure Portal)"
    echo "- Site Name (e.g., Warehouse_A)"
    echo "- Truck Number (e.g., Truck_001)"
    echo "============================================================"
    echo
    
    # Run the device setup script
    export NEXUS_PROJECT_DIR="$(pwd)"
    cd /opt/azure-iot
    python3 device_setup.py
    
    if [[ $? -eq 0 ]]; then
        print_success "Device setup completed successfully"
    else
        print_error "Device setup failed"
        exit 1
    fi
}

# Function to setup and start systemd service
setup_service() {
    print_status "Setting up systemd service..."
    
    # Reload systemd to recognize new service
    sudo systemctl daemon-reload
    
    # Enable service to start on boot
    sudo systemctl enable azure-iot.service
    
    # Start the service
    sudo systemctl start azure-iot.service
    
    # Wait a moment for service to start
    sleep 3
    
    # Check service status
    if sudo systemctl is-active --quiet azure-iot.service; then
        print_success "Service started successfully"
    else
        print_warning "Service may not have started properly. Check status with: systemctl status azure-iot.service"
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check if configuration file exists
    if [[ -f "/etc/azureiotpnp/provisioning_config.json" ]]; then
        print_success "Configuration file created"
    else
        print_error "Configuration file not found"
        return 1
    fi
    
    # Check if service files exist
    if [[ -f "/opt/azure-iot/iot_service.py" ]] && [[ -f "/opt/azure-iot/device_setup.py" ]] && [[ -f "/opt/azure-iot/download.py" ]]; then
        print_success "Service files installed"
    else
        print_error "Service files not found"
        return 1
    fi
    
    # Check if env.json exists (optional)
    if [[ -f "/opt/azure-iot/env.json" ]]; then
        print_success "Environment configuration present"
    else
        print_warning "Environment configuration not found; it will be created by device_setup.py if needed"
    fi
    
    # Check if systemd service is enabled
    if sudo systemctl is-enabled --quiet azure-iot.service; then
        print_success "Systemd service enabled"
    else
        print_error "Systemd service not enabled"
        return 1
    fi
    
    # Check if service is running
    if sudo systemctl is-active --quiet azure-iot.service; then
        print_success "Service is running"
    else
        print_warning "Service is not running. Check status with: systemctl status azure-iot.service"
    fi
    
    return 0
}

# Function to display final instructions
show_final_instructions() {
    echo
    echo "============================================================"
    echo "Setup Complete!"
    echo "============================================================"
    echo "Your Azure IoT service has been installed and configured."
    echo
    echo "Useful commands:"
    echo "  Check service status: sudo systemctl status azure-iot.service"
    echo "  View service logs:   sudo journalctl -u azure-iot.service -f"
    echo "  Restart service:     sudo systemctl restart azure-iot.service"
    echo "  Stop service:        sudo systemctl stop azure-iot.service"
    echo
    echo "The service will automatically start on boot and maintain"
    echo "connection to Azure IoT Hub with heartbeat monitoring."
    echo "============================================================"
}

# Main execution
main() {
    echo "============================================================"
    echo "Azure IoT Connection Service - Automated Setup"
    echo "============================================================"
    echo "This script will automatically set up your Azure IoT service."
    echo "Please ensure you have your Azure IoT credentials ready."
    echo "============================================================"
    echo
    
    # Check if running as root
    check_root
    
    # Check system requirements
    check_system
    
    # Update system packages
    update_system
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Copy service files
    copy_service_files
    
    # Setup logging
    setup_logging
    
    # Run device setup
    run_device_setup
    
    # Setup and start service
    setup_service
    
    # Verify installation
    if verify_installation; then
        print_success "Installation verified successfully"
    else
        print_warning "Installation verification failed. Please check the service manually."
    fi
    
    # Show final instructions
    show_final_instructions
}

# Run main function
main "$@"
