#!/bin/bash

# NexusRFIDReader Autostart Setup Script
# This script sets up desktop integration and autostart for the application

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

# Variables
APP_NAME="NexusRFIDReader"
CURRENT_DIR=$(pwd)
EXECUTABLE_PATH="$CURRENT_DIR/NexusRFIDReader"
ICON_PATH="$CURRENT_DIR/ui/img/icon.ico"
DESKTOP_FILE_NAME="${APP_NAME}.desktop"

echo -e "${CYAN}==============================================================${NC}"
echo -e "${CYAN}        NexusRFIDReader Autostart Setup${NC}"
echo -e "${CYAN}            Desktop Integration${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo ""

# Check if executable exists
if [ ! -f "$EXECUTABLE_PATH" ]; then
    echo -e "${RED}ERROR: Executable not found at $EXECUTABLE_PATH${NC}"
    echo -e "${YELLOW}   Please run this script from the directory containing the NexusRFIDReader executable${NC}"
    exit 1
fi

# Check if icon exists
if [ ! -f "$ICON_PATH" ]; then
    echo -e "${YELLOW}WARNING: Icon not found at $ICON_PATH${NC}"
    echo -e "${YELLOW}   Using default icon${NC}"
    ICON_PATH=""
fi

echo -e "${BLUE}Setup Information:${NC}"
echo -e "   ${WHITE}Application:${NC} $APP_NAME"
echo -e "   ${WHITE}Executable:${NC} $EXECUTABLE_PATH"
echo -e "   ${WHITE}Icon:${NC} ${ICON_PATH:-"Default"}"
echo -e "   ${WHITE}Current User:${NC} $(whoami)"
echo ""

# Step 1: Create the .desktop file content
echo -e "${YELLOW}Step 1: Creating desktop entry content...${NC}"

if [ -n "$ICON_PATH" ]; then
    desktop_file_content="[Desktop Entry]
Version=1.0
Name=${APP_NAME}
Comment=Advanced RFID scanning and GPS tracking system
Exec=${EXECUTABLE_PATH}
Icon=${ICON_PATH}
Type=Application
Terminal=false
Categories=Utility;Office;
Keywords=RFID;GPS;Inventory;Tracking;
StartupNotify=true
StartupWMClass=${APP_NAME}
"
else
    desktop_file_content="[Desktop Entry]
Version=1.0
Name=${APP_NAME}
Comment=Advanced RFID scanning and GPS tracking system
Exec=${EXECUTABLE_PATH}
Type=Application
Terminal=false
Categories=Utility;Office;
Keywords=RFID;GPS;Inventory;Tracking;
StartupNotify=true
StartupWMClass=${APP_NAME}
"
fi

echo -e "   ${GREEN}SUCCESS${NC} Desktop entry content created"

# Step 2: Define paths
echo -e "${YELLOW}Step 2: Setting up directory paths...${NC}"

# Define the location of the .desktop file in the applications directory
desktop_applications_path="$HOME/.local/share/applications/$DESKTOP_FILE_NAME"

# Define the location of the .desktop file in the autostart directory
desktop_autostart_path="$HOME/.config/autostart/$DESKTOP_FILE_NAME"

echo -e "   ${WHITE}Applications path:${NC} $desktop_applications_path"
echo -e "   ${WHITE}Autostart path:${NC} $desktop_autostart_path"

# Step 3: Create applications directory and file
echo -e "${YELLOW}Step 3: Creating application menu entry...${NC}"

# Ensure the applications directory exists
mkdir -p "$HOME/.local/share/applications"

# Write the content to the .desktop file for applications
echo "$desktop_file_content" > "$desktop_applications_path"

# Make the .desktop file executable for applications
chmod +x "$desktop_applications_path"

echo -e "   ${GREEN}SUCCESS${NC} Desktop entry created for application list: $desktop_applications_path"

# Step 4: Create autostart directory and file
echo -e "${YELLOW}Step 4: Creating autostart entry...${NC}"

# Ensure the autostart directory exists
mkdir -p "$HOME/.config/autostart"

# Write the content to the .desktop file for autostart
echo "$desktop_file_content" > "$desktop_autostart_path"

# Make the .desktop file executable for autostart
chmod +x "$desktop_autostart_path"

echo -e "   ${GREEN}SUCCESS${NC} Startup entry created: $desktop_autostart_path"

# Step 5: Create monitoring script for autostart
echo -e "${YELLOW}Step 5: Creating monitoring script...${NC}"

MONITOR_SCRIPT="$HOME/.local/bin/monitor_nexus_rfid.sh"
mkdir -p "$HOME/.local/bin"

cat > "$MONITOR_SCRIPT" <<EOL
#!/bin/bash

# NexusRFIDReader Monitoring Script
# Ensures the application keeps running

APP_NAME="NexusRFIDReader"
APP_PATH="$EXECUTABLE_PATH"
LOG_FILE="$HOME/.local/share/nexusrfid/monitor.log"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> "\$LOG_FILE"
}

log_message "Starting NexusRFIDReader monitor"

while true; do
    if ! pgrep -x "\$APP_NAME" > /dev/null; then
        log_message "\$APP_NAME is not running. Starting..."
        \$APP_PATH &
        sleep 2
        if pgrep -x "\$APP_NAME" > /dev/null; then
            log_message "\$APP_NAME started successfully"
        else
            log_message "Failed to start \$APP_NAME"
        fi
    else
        log_message "\$APP_NAME is running normally"
    fi
    sleep 10
done
EOL

chmod +x "$MONITOR_SCRIPT"
echo -e "   ${GREEN}SUCCESS${NC} Monitoring script created: $MONITOR_SCRIPT"

# Step 6: Update desktop database
echo -e "${YELLOW}Step 6: Updating desktop database...${NC}"

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
    echo -e "   ${GREEN}SUCCESS${NC} Desktop database updated"
else
    echo -e "   ${BLUE}Desktop database update skipped (command not available)${NC}"
fi

# Step 7: Update icon cache
echo -e "${YELLOW}Step 7: Updating icon cache...${NC}"

if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons" 2>/dev/null || true
    echo -e "   ${GREEN}SUCCESS${NC} Icon cache updated"
else
    echo -e "   ${BLUE}Icon cache update skipped (command not available)${NC}"
fi

# Step 8: Create data directory
echo -e "${YELLOW}Step 8: Creating data directory...${NC}"

DATA_DIR="$HOME/.local/share/nexusrfid"
mkdir -p "$DATA_DIR"
echo -e "   ${GREEN}SUCCESS${NC} Data directory created: $DATA_DIR"

echo ""
echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}            AUTOSTART SETUP COMPLETED!${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo ""
echo -e "${CYAN}Created Components:${NC}"
echo -e "   • Application menu entry: $desktop_applications_path"
echo -e "   • Autostart entry: $desktop_autostart_path"
echo -e "   • Monitoring script: $MONITOR_SCRIPT"
echo -e "   • Data directory: $DATA_DIR"
echo -e "   • Log file: $DATA_DIR/monitor.log"
echo ""
echo -e "${PURPLE}Autostart Behavior:${NC}"
echo -e "   • The application will start automatically when you log in"
echo -e "   • A monitoring script ensures it keeps running"
echo -e "   • You can also start it manually from the Applications menu"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "   • You may need to log out and log back in for autostart to take effect"
echo -e "   • The monitoring script will create log files in $DATA_DIR"
echo -e "   • To disable autostart, remove the file: $desktop_autostart_path"
echo ""
echo -e "${BLUE}Manual Start:${NC}"
echo -e "   • From Applications menu: Look for 'Nexus RFID Reader'"
echo -e "   • From terminal: $EXECUTABLE_PATH"
echo ""
echo -e "${GREEN}Desktop integration complete!${NC}"