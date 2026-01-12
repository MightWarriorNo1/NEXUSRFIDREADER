#!/bin/bash

# Azure IoT Connection Service - Test Setup Script
# This script tests and validates your Azure IoT service setup

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

# Function to test configuration files
test_configuration() {
    print_status "Testing configuration files..."
    
    # Check if configuration file exists
    if [[ -f "/etc/azureiotpnp/provisioning_config.json" ]]; then
        print_success "Configuration file exists"
        
        # Test JSON syntax
        if python3 -m json.tool "/etc/azureiotpnp/provisioning_config.json" > /dev/null 2>&1; then
            print_success "Configuration file has valid JSON syntax"
        else
            print_error "Configuration file has invalid JSON syntax"
            return 1
        fi
        
        # Check file permissions
        perms=$(stat -c "%a" "/etc/azureiotpnp/provisioning_config.json")
        if [[ "$perms" == "600" ]]; then
            print_success "Configuration file has correct permissions (600)"
        else
            print_warning "Configuration file permissions are $perms (should be 600)"
        fi
        
        # Display configuration summary (without sensitive data)
        print_status "Configuration summary:"
        config_data=$(python3 -c "
import json
with open('/etc/azureiotpnp/provisioning_config.json', 'r') as f:
    config = json.load(f)
print(f'  ID Scope: {config.get(\"idScope\", \"N/A\")}')
print(f'  Registration ID: {config.get(\"registrationId\", \"N/A\")}')
print(f'  Global Endpoint: {config.get(\"globalEndpoint\", \"N/A\")}')
if 'tags' in config and 'nexusLocate' in config['tags']:
    tags = config['tags']['nexusLocate']
    print(f'  Site Name: {tags.get(\"siteName\", \"N/A\")}')
    print(f'  Truck Number: {tags.get(\"truckNumber\", \"N/A\")}')
    print(f'  Device Serial: {tags.get(\"deviceSerial\", \"N/A\")}')
")
        echo "$config_data"
        
    else
        print_error "Configuration file not found"
        return 1
    fi
    
    return 0
}

# Function to test service files
test_service_files() {
    print_status "Testing service files..."
    
    # Check if service directory exists
    if [[ -d "/opt/azure-iot" ]]; then
        print_success "Service directory exists"
    else
        print_error "Service directory not found"
        return 1
    fi
    
    # Check if main service script exists and is executable
    if [[ -f "/opt/azure-iot/iot_service.py" ]]; then
        print_success "IoT service script exists"
        if [[ -x "/opt/azure-iot/iot_service.py" ]]; then
            print_success "IoT service script is executable"
        else
            print_warning "IoT service script is not executable"
        fi
    else
        print_error "IoT service script not found"
        return 1
    fi
    
    # Check if device setup script exists and is executable
    if [[ -f "/opt/azure-iot/device_setup.py" ]]; then
        print_success "Device setup script exists"
        if [[ -x "/opt/azure-iot/device_setup.py" ]]; then
            print_success "Device setup script is executable"
        else
            print_warning "Device setup script is not executable"
        fi
    else
        print_error "Device setup script not found"
        return 1
    fi
    
    # Check if download script exists and is executable
    if [[ -f "/opt/azure-iot/download.py" ]]; then
        print_success "Download script exists"
        if [[ -x "/opt/azure-iot/download.py" ]]; then
            print_success "Download script is executable"
        else
            print_warning "Download script is not executable"
        fi
    else
        print_error "Download script not found"
        return 1
    fi
    
    return 0
}

# Function to test systemd service
test_systemd_service() {
    print_status "Testing systemd service..."
    
    # Check if service file exists
    if [[ -f "/etc/systemd/system/azure-iot.service" ]]; then
        print_success "Systemd service file exists"
    else
        print_error "Systemd service file not found"
        return 1
    fi
    
    # Check if service is enabled
    if sudo systemctl is-enabled --quiet azure-iot.service; then
        print_success "Service is enabled (will start on boot)"
    else
        print_warning "Service is not enabled"
    fi
    
    # Check if service is active
    if sudo systemctl is-active --quiet azure-iot.service; then
        print_success "Service is running"
    else
        print_warning "Service is not running"
    fi
    
    # Check service status
    print_status "Service status:"
    sudo systemctl status azure-iot.service --no-pager -l
    
    return 0
}

# Function to test Python dependencies
test_python_dependencies() {
    print_status "Testing Python dependencies..."
    
    # Check if Python 3 is available
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version)
        print_success "Python 3 available: $python_version"
    else
        print_error "Python 3 not found"
        return 1
    fi
    
    # Check if pip3 is available
    if command -v pip3 &> /dev/null; then
        print_success "pip3 available"
    else
        print_error "pip3 not found"
        return 1
    fi
    
    # Check Azure IoT Device SDK
    if python3 -c "import azure.iot.device" 2>/dev/null; then
        print_success "Azure IoT Device SDK is installed"
        
        # Get version info
        sdk_version=$(python3 -c "import azure.iot.device; print(azure.iot.device.__version__)" 2>/dev/null || echo "Unknown")
        print_status "Azure IoT Device SDK version: $sdk_version"
    else
        print_error "Azure IoT Device SDK is not installed"
        return 1
    fi
    
    # Check Azure Storage Blob SDK
    if python3 -c "import azure.storage.blob" 2>/dev/null; then
        print_success "Azure Storage Blob SDK is installed"
    else
        print_warning "Azure Storage Blob SDK is not installed (required for updates)"
    fi
    
    return 0
}

# Function to test log files
test_logging() {
    print_status "Testing logging setup..."
    
    # Check if log file exists
    if [[ -f "/var/log/azure-iot-service.log" ]]; then
        print_success "Log file exists"
        
        # Check file permissions
        perms=$(stat -c "%a" "/var/log/azure-iot-service.log")
        if [[ "$perms" == "644" ]]; then
            print_success "Log file has correct permissions (644)"
        else
            print_warning "Log file permissions are $perms (should be 644)"
        fi
        
        # Check file size
        size=$(stat -c "%s" "/var/log/azure-iot-service.log")
        if [[ $size -gt 0 ]]; then
            print_success "Log file has content ($size bytes)"
            
            # Show last few log entries
            print_status "Last 5 log entries:"
            tail -5 "/var/log/azure-iot-service.log" 2>/dev/null || echo "  (No readable log entries)"
        else
            print_warning "Log file is empty"
        fi
        
    else
        print_warning "Log file not found"
    fi
    
    # Check systemd journal
    print_status "Checking systemd journal for service logs..."
    journal_count=$(sudo journalctl -u azure-iot.service --no-pager | wc -l)
    if [[ $journal_count -gt 1 ]]; then
        print_success "Service logs found in systemd journal ($journal_count lines)"
        
        # Show last few journal entries
        print_status "Last 5 journal entries:"
        sudo journalctl -u azure-iot.service --no-pager -n 5
    else
        print_warning "No service logs found in systemd journal"
    fi
    
    return 0
}

# Function to test network connectivity
test_network() {
    print_status "Testing network connectivity..."
    
    # Test basic internet connectivity
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        print_success "Basic internet connectivity OK"
    else
        print_warning "Basic internet connectivity failed"
    fi
    
    # Test Azure DPS endpoint
    if ping -c 1 global.azure-devices-provisioning.net > /dev/null 2>&1; then
        print_success "Azure DPS endpoint reachable"
    else
        print_warning "Azure DPS endpoint not reachable"
    fi
    
    # Test DNS resolution
    if nslookup global.azure-devices-provisioning.net > /dev/null 2>&1; then
        print_success "DNS resolution working"
    else
        print_warning "DNS resolution issues detected"
    fi
    
    return 0
}

# Function to analyze service logs
analyze_logs() {
    print_status "Analyzing service logs for errors..."
    
    # Check for errors in systemd journal
    error_count=$(journalctl -u azure-iot.service --no-pager | grep -i "error\|fail\|exception" | wc -l)
    if [[ $error_count -gt 0 ]]; then
        print_warning "Found $error_count potential errors in service logs"
        print_status "Recent errors:"
        sudo journalctl -u azure-iot.service --no-pager | grep -i "error\|fail\|exception" | tail -5
    else
        print_success "No errors found in service logs"
    fi
    
    # Check for connection issues
    connection_issues=$(sudo journalctl -u azure-iot.service --no-pager | grep -i "connect\|connection\|timeout" | wc -l)
    if [[ $connection_issues -gt 0 ]]; then
        print_status "Connection-related messages found:"
        sudo journalctl -u azure-iot.service --no-pager | grep -i "connect\|connection\|timeout" | tail -3
    fi
    
    # Check for update-related issues
    update_issues=$(sudo journalctl -u azure-iot.service --no-pager | grep -i "download\|update\|blob\|storage" | wc -l)
    if [[ $update_issues -gt 0 ]]; then
        print_status "Update-related messages found:"
        sudo journalctl -u azure-iot.service --no-pager | grep -i "download\|update\|blob\|storage" | tail -3
    fi
    
    return 0
}

# Function to provide recommendations
provide_recommendations() {
    print_status "Providing recommendations..."
    
    echo
    echo "============================================================"
    echo "Recommendations:"
    echo "============================================================"
    
    # Check if service is running
    if ! sudo systemctl is-active --quiet azure-iot.service; then
        echo "• Start the service: sudo systemctl start azure-iot.service"
    fi
    
    # Check if service is enabled
    if ! sudo systemctl is-enabled --quiet azure-iot.service; then
        echo "• Enable service auto-start: sudo systemctl enable azure-iot.service"
    fi
    
    # Check for common issues
    if ! ping -c 1 global.azure-devices-provisioning.net > /dev/null 2>&1; then
        echo "• Check network connectivity and firewall settings"
    fi
    
    if [[ ! -f "/etc/azureiotpnp/provisioning_config.json" ]]; then
        echo "• Run device setup: sudo python3 /opt/azure-iot/device_setup.py"
    fi
    
    if [[ ! -f "/opt/azure-iot/download.py" ]]; then
        echo "• Ensure download.py is present for automatic updates"
    fi
    
    echo
    echo "For detailed troubleshooting:"
    echo "• View service logs: sudo journalctl -u azure-iot.service -f"
    echo "• Check service status: sudo systemctl status azure-iot.service"
    echo "• View configuration: sudo cat /etc/azureiotpnp/provisioning_config.json"
    echo "============================================================"
}

# Function to run all tests
run_all_tests() {
    local overall_success=true
    
    echo "============================================================"
    echo "Azure IoT Service - Setup Test Results"
    echo "============================================================"
    echo
    
    # Run all test functions
    test_configuration || overall_success=false
    echo
    
    test_service_files || overall_success=false
    echo
    
    test_systemd_service || overall_success=false
    echo
    
    test_python_dependencies || overall_success=false
    echo
    
    test_logging || overall_success=false
    echo
    
    test_network || overall_success=false
    echo
    
    analyze_logs || overall_success=false
    echo
    
    # Provide recommendations
    provide_recommendations
    
    # Final summary
    echo
    echo "============================================================"
    if [[ "$overall_success" == true ]]; then
        print_success "All tests completed successfully!"
        echo "Your Azure IoT service appears to be properly configured."
    else
        print_warning "Some tests failed. Please review the recommendations above."
        echo "Your Azure IoT service may need additional configuration."
    fi
    echo "============================================================"
    
    return $([[ "$overall_success" == true ]] && echo 0 || echo 1)
}

# Main execution
main() {
    echo "============================================================"
    echo "Azure IoT Connection Service - Test Setup"
    echo "============================================================"
    echo "This script will test and validate your Azure IoT service setup."
    echo "============================================================"
    echo
    
    # Check if running as root
    check_root
    
    # Run all tests
    run_all_tests
}

# Run main function
main "$@"
