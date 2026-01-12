#!/bin/bash

# NexusRFIDReader Uninstall Script for Raspberry Pi
# This script completely removes the NexusRFIDReader package and all associated files

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

# Debian package name (must be lowercase)
PACKAGE_NAME_DEB=nexusrfidreader
# App artifact names/paths (mixed case as installed by create script)
PACKAGE_EXECUTABLE="NexusRFIDReader"
APP_NAME="NexusRFIDReader"
SERVICE_NAME="nexusrfid_production.service"

echo -e "${CYAN}==============================================================${NC}"
echo -e "${CYAN}            NexusRFIDReader Uninstaller${NC}"
echo -e "${CYAN}              For Raspberry Pi${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will completely remove NexusRFIDReader and all its data!${NC}"
echo -e "${YELLOW}This action cannot be undone.${NC}"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Uninstall cancelled.${NC}"
    exit 0
fi

echo ""

# Step 1: Stop and disable systemd service
echo -e "${YELLOW}Step 1: Stopping systemd service...${NC}"
if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    systemctl stop "${SERVICE_NAME}"
    echo -e "   ${GREEN}SUCCESS${NC} Service stopped"
else
    echo -e "   ${BLUE}Service was not running${NC}"
fi

if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
    systemctl disable "${SERVICE_NAME}"
    echo -e "   ${GREEN}SUCCESS${NC} Service disabled"
else
    echo -e "   ${BLUE}Service was not enabled${NC}"
fi

# Wait a moment for processes to stop
sleep 2

# Force kill any remaining processes as fallback
pkill -f "NexusRFIDReader" 2>/dev/null || true

echo -e "   ${GREEN}SUCCESS${NC} Service stopped and disabled"

# Step 2: Remove and purge the package
echo -e "${YELLOW}Step 2: Removing package and configuration files...${NC}"
if dpkg -l | grep -q "^ii.*${PACKAGE_NAME_DEB}\|^rc.*${PACKAGE_NAME_DEB}"; then
    # Package is installed or partially removed, purge it
    apt-get purge -y ${PACKAGE_NAME_DEB} 2>/dev/null || {
        echo -e "   ${YELLOW}WARNING: Package removal had issues, continuing with manual cleanup...${NC}"
        # Try dpkg remove as fallback
        dpkg --remove ${PACKAGE_NAME_DEB} 2>/dev/null || true
    }
    echo -e "   ${GREEN}SUCCESS${NC} Package removed and purged"
else
    echo -e "   ${BLUE}Package not found in dpkg database, continuing with manual cleanup...${NC}"
fi

# Step 3: Remove systemd service file
echo -e "${YELLOW}Step 3: Removing systemd service file...${NC}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
if [ -f "$SERVICE_FILE" ]; then
    rm -f "$SERVICE_FILE"
    echo -e "   ${GREEN}SUCCESS${NC} Removed service file: $SERVICE_FILE"
    # Reload systemd daemon
    systemctl daemon-reload 2>/dev/null || true
    echo -e "   ${GREEN}SUCCESS${NC} Systemd daemon reloaded"
else
    echo -e "   ${BLUE}Service file not found: $SERVICE_FILE${NC}"
fi

# Step 4: Remove application files
echo -e "${YELLOW}Step 4: Removing application files...${NC}"

# Remove executable
if [ -f "/usr/local/bin/${PACKAGE_EXECUTABLE}" ]; then
    rm -f "/usr/local/bin/${PACKAGE_EXECUTABLE}"
    echo -e "   ${GREEN}SUCCESS${NC} Removed executable: /usr/local/bin/${PACKAGE_EXECUTABLE}"
fi

# Remove desktop entry
if [ -f "/usr/share/applications/${APP_NAME}.desktop" ]; then
    rm -f "/usr/share/applications/${APP_NAME}.desktop"
    echo -e "   ${GREEN}SUCCESS${NC} Removed desktop entry: /usr/share/applications/${APP_NAME}.desktop"
else
    echo -e "   ${BLUE}Desktop entry not found${NC}"
fi

# Remove icon
if [ -f "/usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico" ]; then
    rm -f "/usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico"
    echo -e "   ${GREEN}SUCCESS${NC} Removed icon: /usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico"
else
    echo -e "   ${BLUE}Icon not found${NC}"
fi

# Step 5: Remove sudoers configuration
echo -e "${YELLOW}Step 5: Removing sudoers configuration...${NC}"
SUDOERS_FILE="/etc/sudoers.d/nexusrfid"
if [ -f "$SUDOERS_FILE" ]; then
    rm -f "$SUDOERS_FILE"
    echo -e "   ${GREEN}SUCCESS${NC} Removed sudoers file: $SUDOERS_FILE"
else
    echo -e "   ${BLUE}Sudoers file not found${NC}"
fi

# Step 6: Remove data directories
echo -e "${YELLOW}Step 6: Removing data directories...${NC}"

# Remove main data directory
RFID_DATA_DIR=/var/lib/nexusrfid
if [ -d "$RFID_DATA_DIR" ]; then
    echo -e "   ${WHITE}Found data directory: $RFID_DATA_DIR${NC}"
    echo -e "   ${YELLOW}WARNING: This directory may contain important data!${NC}"
    read -p "   Remove data directory? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$RFID_DATA_DIR"
        echo -e "   ${GREEN}SUCCESS${NC} Removed data directory: $RFID_DATA_DIR"
    else
        echo -e "   ${BLUE}Data directory preserved: $RFID_DATA_DIR${NC}"
    fi
else
    echo -e "   ${BLUE}No data directory found${NC}"
fi

# Step 7: Update system databases
echo -e "${YELLOW}Step 7: Updating system databases...${NC}"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
    echo -e "   ${GREEN}SUCCESS${NC} Updated desktop database"
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
    echo -e "   ${GREEN}SUCCESS${NC} Updated icon cache"
fi

# Step 8: Clean up package cache
echo -e "${YELLOW}Step 8: Cleaning up package cache...${NC}"
apt-get autoremove -y 2>/dev/null || true
apt-get autoclean 2>/dev/null || true
echo -e "   ${GREEN}SUCCESS${NC} Package cache cleaned"

# Step 9: Final verification
echo -e "${YELLOW}Step 9: Final verification...${NC}"
REMAINING_FILES=0

# Check for remaining files
if [ -f "/usr/local/bin/${PACKAGE_EXECUTABLE}" ] || \
   [ -f "/etc/systemd/system/${SERVICE_NAME}" ] || \
   [ -f "/usr/share/applications/${APP_NAME}.desktop" ] || \
   [ -f "/usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico" ] || \
   [ -f "/etc/sudoers.d/nexusrfid" ]; then
    REMAINING_FILES=1
fi

if [ $REMAINING_FILES -eq 0 ]; then
    echo -e "   ${GREEN}SUCCESS${NC} All application files removed successfully"
else
    echo -e "   ${YELLOW}WARNING: Some files may still remain${NC}"
    echo -e "   ${WHITE}Remaining files:${NC}"
    [ -f "/usr/local/bin/${PACKAGE_EXECUTABLE}" ] && echo -e "      • /usr/local/bin/${PACKAGE_EXECUTABLE}"
    [ -f "/etc/systemd/system/${SERVICE_NAME}" ] && echo -e "      • /etc/systemd/system/${SERVICE_NAME}"
    [ -f "/usr/share/applications/${APP_NAME}.desktop" ] && echo -e "      • /usr/share/applications/${APP_NAME}.desktop"
    [ -f "/usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico" ] && echo -e "      • /usr/share/icons/hicolor/512x512/apps/${APP_NAME}.ico"
    [ -f "/etc/sudoers.d/nexusrfid" ] && echo -e "      • /etc/sudoers.d/nexusrfid"
fi

echo ""
echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}            UNINSTALLATION COMPLETED!${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo ""
echo -e "${CYAN}Summary of removed components:${NC}"
echo -e "   • Systemd service (${SERVICE_NAME})"
echo -e "   • Application executable"
echo -e "   • Desktop entry"
echo -e "   • Application icon"
echo -e "   • Sudoers configuration"
echo -e "   • Package database entries"
echo ""
echo -e "${PURPLE}Preserved components (if you chose to keep them):${NC}"
echo -e "   • Data directory: /var/lib/nexusrfid"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "   • The systemd service has been stopped and disabled"
echo -e "   • Service file has been removed from /etc/systemd/system/"
echo -e "   • Systemd daemon has been reloaded"
echo ""
echo -e "${BLUE}Note:${NC}"
echo -e "   • You may need to reboot for all changes to take full effect"
echo -e "   • If you want to reinstall, install the package again:"
echo -e "     ${WHITE}sudo apt install ./NexusRFIDReader-1.0.deb${NC}"
echo ""
echo -e "${GREEN}NexusRFIDReader has been completely removed!${NC}"
