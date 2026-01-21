#!/bin/bash

# NexusRFIDReader Package Creation Script for Raspberry Pi
# This script creates a .deb package for easy installation

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

# Define package variables
PACKAGE_NAME=NexusRFIDReader
PACKAGE_VERSION=1.0
ARCHITECTURE=$(dpkg --print-architecture)
DESCRIPTION="Nexus RFID Reader - Advanced RFID scanning and GPS tracking system"
MAINTAINER="Nexus Systems"
WEBSITE="https://nexusyms.com"

echo -e "${CYAN}==============================================================${NC}"
echo -e "${CYAN}        NexusRFIDReader Package Builder${NC}"
echo -e "${CYAN}              For Raspberry Pi${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "NexusRFIDReader.spec" ]; then
    echo -e "${RED}ERROR: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}   Expected files: main.py, NexusRFIDReader.spec${NC}"
    exit 1
fi

echo -e "${BLUE}Package Information:${NC}"
echo -e "   ${WHITE}Name:${NC} $PACKAGE_NAME"
echo -e "   ${WHITE}Version:${NC} $PACKAGE_VERSION"
echo -e "   ${WHITE}Architecture:${NC} $ARCHITECTURE"
echo -e "   ${WHITE}Description:${NC} $DESCRIPTION"
echo ""

# Step 1: Build PyInstaller executable
echo -e "${YELLOW}Step 1: Building PyInstaller executable...${NC}"
if command -v pyinstaller &> /dev/null; then
    echo -e "   ${GREEN}SUCCESS${NC} PyInstaller found"
    pyinstaller --clean --onefile --icon=ui/img/icon.ico --name=NexusRFIDReader main.py
    echo -e "   ${GREEN}SUCCESS${NC} Executable built successfully"
else
    echo -e "   ${RED}ERROR: PyInstaller not found. Installing...${NC}"
    pip3 install pyinstaller
    pyinstaller --clean --onefile --icon=ui/img/icon.ico --name=NexusRFIDReader main.py
    echo -e "   ${GREEN}SUCCESS${NC} PyInstaller installed and executable built"
fi

# Check if executable was created
if [ ! -f "dist/NexusRFIDReader" ]; then
    echo -e "${RED}ERROR: Executable not created successfully${NC}"
    exit 1
fi

echo ""

# Step 2: Create directory structure
echo -e "${YELLOW}Step 2: Creating package directory structure...${NC}"
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/local/bin
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/share/applications
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/share/icons/hicolor/512x512/apps
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/systemd/system
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/var/lib/nexusrfid
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/netplan
mkdir -p ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/network/interfaces.d
echo -e "   ${GREEN}SUCCESS${NC} Directory structure created"

# Step 3: Copy files to package
echo -e "${YELLOW}Step 3: Copying application files...${NC}"
cp dist/NexusRFIDReader ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/local/bin/
cp ui/img/icon.ico ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/share/icons/hicolor/512x512/apps/${PACKAGE_NAME}.ico
echo -e "   ${GREEN}SUCCESS${NC} Application files copied"

# Step 4: Create systemd service file (with placeholders to be replaced in postinst)
echo -e "${YELLOW}Step 4: Creating systemd service file...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/systemd/system/nexusrfid_production.service <<'EOL'
[Unit]
Description=Nexus RFID Application
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
ExecStartPre=/bin/bash -c '/usr/bin/sudo /sbin/dhclient usb0 || true'
ExecStartPre=/bin/sleep 5
ExecStart=sudo /usr/local/bin/NexusRFIDReader
Restart=always
RestartSec=5
User=__SERVICE_USER__
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=__XAUTHORITY_PATH__
Environment=HOME=__HOME_DIR__
Environment=XDG_RUNTIME_DIR=__XDG_RUNTIME_DIR__
Environment=DBUS_SESSION_BUS_ADDRESS=__DBUS_SESSION_BUS_ADDRESS__

[Install]
WantedBy=graphical.target
EOL
echo -e "   ${GREEN}SUCCESS${NC} Systemd service file created (will be configured during installation)"

# Step 5: Create network configuration files for eth0
echo -e "${YELLOW}Step 5: Creating network configuration for eth0...${NC}"

# Create netplan configuration (for systems using netplan)
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/netplan/99-nexusrfid-eth0.yaml <<'EOL'
# Network configuration for Nexus RFID Reader eth0 interface
# This file will be activated during package installation
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 169.254.0.1/16
      dhcp4: false
      dhcp6: false
EOL

# Create traditional interfaces configuration (for systems using /etc/network/interfaces)
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/etc/network/interfaces.d/nexusrfid-eth0 <<'EOL'
# Network configuration for Nexus RFID Reader eth0 interface
# Auto-configured during package installation
auto eth0
iface eth0 inet static
    address 169.254.0.1
    netmask 255.255.0.0
    broadcast 169.254.255.255
EOL

echo -e "   ${GREEN}SUCCESS${NC} Network configuration files created"

# Step 6: Create .desktop file for application menu
echo -e "${YELLOW}Step 6: Creating desktop application entry...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/usr/share/applications/${PACKAGE_NAME}.desktop <<EOL
[Desktop Entry]
Version=1.0
Name=Nexus RFID Reader
Comment=Advanced RFID scanning and GPS tracking system
Exec=/usr/local/bin/NexusRFIDReader
Icon=${PACKAGE_NAME}
Terminal=false
Type=Application
Categories=Utility;Office;
Keywords=RFID;GPS;Inventory;Tracking;
StartupNotify=true
EOL
echo -e "   ${GREEN}SUCCESS${NC} Desktop entry created"

# Step 7: Create control file
echo -e "${YELLOW}Step 7: Creating package control file...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/control <<EOL
Package: ${PACKAGE_NAME}
Version: ${PACKAGE_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: ${MAINTAINER} <support@nexusyms.com>
Homepage: ${WEBSITE}
Depends: libxcb-xinerama0, libxcb-cursor0, libx11-xcb1, libxcb1, libxfixes3, libxi6, libxrender1, libxcb-render0, libxcb-shape0, libxcb-xfixes0, x11-xserver-utils, python3, python3-pip, systemd, sudo, isc-dhcp-client, sed, arp-scan
Description: ${DESCRIPTION}
 This application provides advanced RFID scanning capabilities with GPS tracking,
 real-time data processing, and cloud synchronization. It's designed for inventory
 management and asset tracking in industrial environments.
 .
 Features:
  * Real-time RFID tag scanning
  * GPS location tracking
  * SQLite database storage
  * Cloud API integration
  * Configurable filtering options
  * Automatic data synchronization
  * User-friendly GUI interface
  * Systemd service for automatic startup and monitoring
EOL
echo -e "   ${GREEN}SUCCESS${NC} Control file created"

# Step 8: Create postinst script
echo -e "${YELLOW}Step 8: Creating post-installation script...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/postinst <<'EOL'
#!/bin/bash

set -e

echo "Setting up NexusRFIDReader environment..."

# Determine the user to run the service
# Priority: 1. User who ran sudo (if available), 2. First user in /home, 3. User 'pi' (common on RPI), 4. Fallback to first non-root user
SERVICE_USER=""

# Try to get the user who ran sudo (if installing interactively)
if [ -n "${SUDO_USER:-}" ]; then
    SERVICE_USER="$SUDO_USER"
    echo "Detected installation user: $SERVICE_USER"
elif [ -n "${USER:-}" ] && [ "$USER" != "root" ]; then
    SERVICE_USER="$USER"
    echo "Detected current user: $SERVICE_USER"
else
    # Find the first user with a home directory
    # Prefer 'pi' user on Raspberry Pi, otherwise use first user in /home
    if [ -d "/home/pi" ] && id "pi" &>/dev/null; then
        SERVICE_USER="pi"
        echo "Detected Raspberry Pi default user: pi"
    else
        # Get first user directory in /home
        for user_dir in /home/*; do
            if [ -d "$user_dir" ]; then
                user_name=$(basename "$user_dir")
                if id "$user_name" &>/dev/null; then
                    SERVICE_USER="$user_name"
                    echo "Detected user from home directory: $SERVICE_USER"
                    break
                fi
            fi
        done
    fi
fi

# Fallback: if still no user found, try to get the user who owns display :0
if [ -z "$SERVICE_USER" ]; then
    # Try to find user from X session
    if command -v who &>/dev/null; then
        DISPLAY_USER=$(who | awk '/\(:0\)/ {print $1; exit}')
        if [ -n "$DISPLAY_USER" ] && id "$DISPLAY_USER" &>/dev/null; then
            SERVICE_USER="$DISPLAY_USER"
            echo "Detected user from X session: $SERVICE_USER"
        fi
    fi
fi

# Final fallback: use first non-root user from /etc/passwd
if [ -z "$SERVICE_USER" ]; then
    SERVICE_USER=$(getent passwd | awk -F: '$3 >= 1000 && $1 != "nobody" {print $1; exit}')
    if [ -n "$SERVICE_USER" ]; then
        echo "Using first non-root user: $SERVICE_USER"
    fi
fi

# Validate user exists
if [ -z "$SERVICE_USER" ] || ! id "$SERVICE_USER" &>/dev/null; then
    echo "ERROR: Could not determine a valid user for the service."
    echo "Please create a user account or specify one manually."
    echo "You can edit /etc/systemd/system/nexusrfid_production.service after installation."
    exit 1
fi

echo "Using user for service: $SERVICE_USER"

# Get user information
SERVICE_UID=$(id -u "$SERVICE_USER")
SERVICE_HOME=$(eval echo ~"$SERVICE_USER")
SERVICE_XAUTHORITY="${SERVICE_HOME}/.Xauthority"
SERVICE_XDG_RUNTIME_DIR="/run/user/${SERVICE_UID}"
SERVICE_DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${SERVICE_UID}/bus"

echo "User UID: $SERVICE_UID"
echo "User home: $SERVICE_HOME"
echo "XDG Runtime Dir: $SERVICE_XDG_RUNTIME_DIR"

# Configure sudo for the service user to run dhclient without password
# Allow both /sbin/dhclient and /usr/sbin/dhclient for compatibility
SUDOERS_FILE="/etc/sudoers.d/nexusrfid"
NEED_SUDO_CONFIG=true

# Check if sudoers file exists and already has the configuration
if [ -f "$SUDOERS_FILE" ]; then
    if grep -q "^${SERVICE_USER}.*NOPASSWD.*dhclient" "$SUDOERS_FILE" 2>/dev/null; then
        NEED_SUDO_CONFIG=false
        echo "Sudo configuration for $SERVICE_USER already exists"
    fi
fi

# Create or update sudoers file if needed
if [ "$NEED_SUDO_CONFIG" = true ]; then
    echo "Configuring sudo permissions for $SERVICE_USER user..."
    {
        echo "${SERVICE_USER} ALL=(ALL) NOPASSWD: /sbin/dhclient"
        echo "${SERVICE_USER} ALL=(ALL) NOPASSWD: /usr/sbin/dhclient"
    } > "$SUDOERS_FILE"
    chmod 0440 "$SUDOERS_FILE"
    echo "Sudo configuration added for dhclient"
fi

# Create data directory with proper permissions
RFID_DATA_DIR=/var/lib/nexusrfid
if [ ! -d "$RFID_DATA_DIR" ]; then
    mkdir -p "$RFID_DATA_DIR"
    echo "Created data directory at $RFID_DATA_DIR"
fi

# Set ownership to service user for data directory
chown "${SERVICE_USER}:${SERVICE_USER}" "$RFID_DATA_DIR"
chmod 755 "$RFID_DATA_DIR"

# Ensure service user has X11 permissions
if [ -d "$SERVICE_HOME" ]; then
    # Ensure Xauthority file exists (will be created by X session if needed)
    if [ ! -f "$SERVICE_XAUTHORITY" ]; then
        touch "$SERVICE_XAUTHORITY" 2>/dev/null || true
    fi
    if [ -f "$SERVICE_XAUTHORITY" ]; then
        chown "${SERVICE_USER}:${SERVICE_USER}" "$SERVICE_XAUTHORITY" 2>/dev/null || true
        chmod 600 "$SERVICE_XAUTHORITY" 2>/dev/null || true
    fi
    
    # Ensure proper permissions on home directory (for data files)
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$SERVICE_HOME" 2>/dev/null || true
fi

# Configure eth0 network interface for RFID reader connection
echo "Configuring eth0 network interface for RFID reader..."
ETH0_IP="169.254.0.1"
ETH0_NETMASK="255.255.0.0"
ETH0_BROADCAST="169.254.255.255"

# Check if eth0 interface exists
if ip link show eth0 &>/dev/null || ifconfig eth0 &>/dev/null; then
    echo "eth0 interface detected"
    
    # Configure eth0 immediately using ip command (preferred)
    if command -v ip &>/dev/null; then
        echo "Configuring eth0 using ip command..."
        ip addr flush dev eth0 2>/dev/null || true
        ip addr add ${ETH0_IP}/16 broadcast ${ETH0_BROADCAST} dev eth0 2>/dev/null || true
        ip link set eth0 up 2>/dev/null || true
        echo "eth0 configured with IP: ${ETH0_IP}"
    # Fallback to ifconfig
    elif command -v ifconfig &>/dev/null; then
        echo "Configuring eth0 using ifconfig command..."
        ifconfig eth0 ${ETH0_IP} netmask ${ETH0_NETMASK} broadcast ${ETH0_BROADCAST} up 2>/dev/null || true
        echo "eth0 configured with IP: ${ETH0_IP}"
    fi
    
    # Configure persistent network settings
    # Try netplan first (Ubuntu 18.04+)
    if [ -d "/etc/netplan" ] && [ -f "/etc/netplan/99-nexusrfid-eth0.yaml" ]; then
        echo "Applying netplan configuration..."
        # Validate netplan config
        if command -v netplan &>/dev/null; then
            netplan try --timeout 2 &>/dev/null || true
            netplan apply 2>/dev/null || true
            echo "Netplan configuration applied"
        fi
    # Fallback to traditional /etc/network/interfaces
    elif [ -f "/etc/network/interfaces.d/nexusrfid-eth0" ]; then
        echo "Traditional interfaces configuration found"
        # The configuration file is already in place, just need to bring up the interface
        if command -v ifup &>/dev/null; then
            ifup eth0 2>/dev/null || true
        fi
    fi
    
    # Verify configuration
    sleep 1
    if ip addr show eth0 | grep -q "${ETH0_IP}" || ifconfig eth0 | grep -q "${ETH0_IP}"; then
        echo "eth0 successfully configured with IP: ${ETH0_IP}"
    else
        echo "WARNING: eth0 configuration may not have taken effect. Please verify manually."
    fi
else
    echo "WARNING: eth0 interface not found. Configuration will be applied when interface becomes available."
fi

# Update the service file with actual user information
SERVICE_FILE="/etc/systemd/system/nexusrfid_production.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "Configuring service file with user information..."
    sed -i "s|__SERVICE_USER__|${SERVICE_USER}|g" "$SERVICE_FILE"
    sed -i "s|__XAUTHORITY_PATH__|${SERVICE_XAUTHORITY}|g" "$SERVICE_FILE"
    sed -i "s|__HOME_DIR__|${SERVICE_HOME}|g" "$SERVICE_FILE"
    sed -i "s|__XDG_RUNTIME_DIR__|${SERVICE_XDG_RUNTIME_DIR}|g" "$SERVICE_FILE"
    sed -i "s|__DBUS_SESSION_BUS_ADDRESS__|${SERVICE_DBUS_SESSION_BUS_ADDRESS}|g" "$SERVICE_FILE"
    echo "Service file configured successfully"
else
    echo "WARNING: Service file not found at $SERVICE_FILE"
fi

# Reload systemd daemon
systemctl daemon-reload
echo "Systemd daemon reloaded"

# Enable the service
systemctl enable nexusrfid_production.service
echo "Service enabled to start on boot"

# Start the service immediately
echo "Starting service..."
if systemctl start nexusrfid_production.service; then
    echo "Service started successfully"
    # Wait a moment and verify it's running
    sleep 2
    if systemctl is-active --quiet nexusrfid_production.service; then
        echo "Service is running"
    else
        echo "WARNING: Service may not have started properly. Check status with: systemctl status nexusrfid_production.service"
    fi
else
    echo "WARNING: Failed to start service. Check status with: systemctl status nexusrfid_production.service"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications
    echo "Updated desktop database"
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
    echo "Updated icon cache"
fi

echo ""
echo "NexusRFIDReader installation completed successfully!"
echo "Service will run as user: $SERVICE_USER"
echo "The service has been enabled and started."
echo "It will also start automatically on boot."
echo ""
echo "To check service status, run: sudo systemctl status nexusrfid_production.service"
echo "To view service logs, run: sudo journalctl -u nexusrfid_production.service -f"
echo "You can also launch the application manually from the Applications menu."

EOL

# Make the postinst script executable
chmod 0755 ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/postinst
echo -e "   ${GREEN}SUCCESS${NC} Post-installation script created"

# Step 9: Create prerm script for clean removal
echo -e "${YELLOW}Step 9: Creating pre-removal script...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/prerm <<'EOL'
#!/bin/bash

echo "Stopping NexusRFIDReader service..."

# Stop and disable the systemd service
if systemctl is-active --quiet nexusrfid_production.service 2>/dev/null; then
    systemctl stop nexusrfid_production.service
    echo "Service stopped"
fi

if systemctl is-enabled --quiet nexusrfid_production.service 2>/dev/null; then
    systemctl disable nexusrfid_production.service
    echo "Service disabled"
fi

# Reload systemd daemon
systemctl daemon-reload

# Kill any remaining processes as fallback
pkill -f "NexusRFIDReader" || true

echo "NexusRFIDReader service stopped and disabled."
EOL

chmod 0755 ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/prerm
echo -e "   ${GREEN}SUCCESS${NC} Pre-removal script created"

# Step 10: Create postrm script for cleanup after removal
echo -e "${YELLOW}Step 10: Creating post-removal script...${NC}"
cat > ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/postrm <<'EOL'
#!/bin/bash

# Clean up sudoers configuration if it exists
# Note: We remove the sudoers file, but we can't determine which user it was for
# since the service file may have been customized. Safe to remove as it only affected dhclient.
if [ -f "/etc/sudoers.d/nexusrfid" ]; then
    rm -f /etc/sudoers.d/nexusrfid
    echo "Removed sudo configuration"
fi

# Clean up network configuration files
if [ -f "/etc/netplan/99-nexusrfid-eth0.yaml" ]; then
    rm -f /etc/netplan/99-nexusrfid-eth0.yaml
    if command -v netplan &>/dev/null; then
        netplan apply 2>/dev/null || true
    fi
    echo "Removed netplan configuration"
fi

if [ -f "/etc/network/interfaces.d/nexusrfid-eth0" ]; then
    rm -f /etc/network/interfaces.d/nexusrfid-eth0
    echo "Removed interfaces configuration"
fi

# Reload systemd daemon
systemctl daemon-reload 2>/dev/null || true

echo "Cleanup completed."
EOL

chmod 0755 ${PACKAGE_NAME}-${PACKAGE_VERSION}/DEBIAN/postrm
echo -e "   ${GREEN}SUCCESS${NC} Post-removal script created"

# Step 11: Build the .deb package
echo -e "${YELLOW}Step 11: Building the .deb package...${NC}"
dpkg-deb --build ${PACKAGE_NAME}-${PACKAGE_VERSION}
echo -e "   ${GREEN}SUCCESS${NC} Package built successfully"

# Step 12: Clean up build directory
echo -e "${YELLOW}Step 12: Cleaning up build files...${NC}"
rm -rf ${PACKAGE_NAME}-${PACKAGE_VERSION}
echo -e "   ${GREEN}SUCCESS${NC} Build files cleaned up"

echo ""
echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}            PACKAGE CREATED SUCCESSFULLY!${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo ""
echo -e "${WHITE}Package File:${NC} ${PACKAGE_NAME}-${PACKAGE_VERSION}.deb"
echo -e "${WHITE}Package Size:${NC} $(du -h ${PACKAGE_NAME}-${PACKAGE_VERSION}.deb | cut -f1)"
echo ""
echo -e "${CYAN}Installation Instructions:${NC}"
echo -e "   ${YELLOW}1.${NC} Install the package:"
echo -e "      ${WHITE}sudo apt install ./${PACKAGE_NAME}-${PACKAGE_VERSION}.deb${NC}"
echo ""
echo -e "   ${YELLOW}2.${NC} Start the service (optional, it will start on boot):"
echo -e "      ${WHITE}sudo systemctl start nexusrfid_production.service${NC}"
echo ""
echo -e "   ${YELLOW}3.${NC} Check service status:"
echo -e "      ${WHITE}sudo systemctl status nexusrfid_production.service${NC}"
echo ""
echo -e "   ${YELLOW}4.${NC} Reboot to activate automatic startup:"
echo -e "      ${WHITE}sudo reboot${NC}"
echo ""
echo -e "   ${YELLOW}5.${NC} The service will start automatically on boot"
echo -e "   ${YELLOW}6.${NC} You can also find the application in the Applications menu"
echo ""
echo -e "${PURPLE}Package Contents:${NC}"
echo -e "   • Executable: /usr/local/bin/NexusRFIDReader"
echo -e "   • Systemd Service: /etc/systemd/system/nexusrfid_production.service"
echo -e "   • Icon: /usr/share/icons/hicolor/512x512/apps/${PACKAGE_NAME}.ico"
echo -e "   • Desktop Entry: /usr/share/applications/${PACKAGE_NAME}.desktop"
echo -e "   • Data Directory: /var/lib/nexusrfid"
echo -e "   • Network Config: /etc/netplan/99-nexusrfid-eth0.yaml (or /etc/network/interfaces.d/nexusrfid-eth0)"
echo -e "   • eth0 configured: 169.254.0.1/16 (for RFID reader connection)"
echo ""
echo -e "${PURPLE}Service Management:${NC}"
echo -e "   • Start: ${WHITE}sudo systemctl start nexusrfid_production.service${NC}"
echo -e "   • Stop: ${WHITE}sudo systemctl stop nexusrfid_production.service${NC}"
echo -e "   • Restart: ${WHITE}sudo systemctl restart nexusrfid_production.service${NC}"
echo -e "   • Status: ${WHITE}sudo systemctl status nexusrfid_production.service${NC}"
echo -e "   • Enable: ${WHITE}sudo systemctl enable nexusrfid_production.service${NC}"
echo -e "   • Disable: ${WHITE}sudo systemctl disable nexusrfid_production.service${NC}"
echo -e "   • Logs: ${WHITE}sudo journalctl -u nexusrfid_production.service -f${NC}"
echo ""
echo -e "${GREEN}Ready for deployment!${NC}"