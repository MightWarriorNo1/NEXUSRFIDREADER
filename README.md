# NexusRFID Reader

A comprehensive RFID and GPS data reading application built with PySide6, featuring automatic restart capabilities for production environments.

## How to Run

### Development Environment

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

### Production Environment

**Linux/Raspberry Pi:**
```bash
# Setup Whole Environment
sudo bash scripts/setup.sh

# Install as systemd service
sudo bash scripts/install_service.sh

# Manage service
systemctl status nexusrfid.service
journalctl -u nexusrfid.service -f
```

## UnitTests

Unit tests live under the `UnitTests/` directory and use Python's built-in `unittest` framework.

### Run Tests

1. **Activate virtual environment:**
   ```bash
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # or CMD
   .\venv\Scripts\activate.bat
   
   # Linux/Raspberry Pi
   source venv/bin/activate
   ```

2. **Run all tests:**
   ```bash
   python -m unittest discover -s UnitTests -p "test_*.py" -v
   ```

3. **Run specific tests:**
   ```bash
   python -m unittest UnitTests.test_api_client -v
   python -m unittest UnitTests.test_common -v
   python -m unittest UnitTests.test_data_storage -v
   python -m unittest UnitTests.test_gps -v
   python -m unittest UnitTests.test_rfid -v
   ```

### Test Coverage

- **test_api_client.py**: API client functionality, Auth0 authentication, token management
- **test_common.py**: Common utilities and helper functions
- **test_data_storage.py**: Database operations and data persistence
- **test_gps.py**: GPS module integration and location tracking
- **test_rfid.py**: RFID reader functionality and tag processing

## Setup

### Configuration

Edit `settings.py` to configure:

- **GPS_CONFIG**: GPS module settings (baud rate, external/internal)
- **RFID_CONFIG**: RFID reader settings (host, port, antennas, power)
- **API_CONFIG**: API endpoints, Auth0 credentials, upload intervals
- **DATABASE_CONFIG**: Database usage settings
- **FILTER_CONFIG**: Data filtering options (speed, RSSI, tag range)

### Hardware Requirements

- **RFID Reader**: Compatible with sllurp library
- **GPS Module**: Serial GPS device (optional)
- **Platform**: Windows, Linux, or Raspberry Pi

### Dependencies

See `requirements.txt` for complete dependency list:
- PySide6 (GUI framework)
- requests (HTTP client)
- pyserial (serial communication)
- geopy (geographic calculations)
- sllurp (RFID reader interface)
- schedule (task scheduling)

### Environment Variables

The application automatically detects the platform:
- **Windows**: Uses `~/Documents` for data storage
- **Linux/Raspberry Pi**: Uses `~/.nexusrfid` for data storage

### Service Management

**Linux/Raspberry Pi:**
```bash
# Check service status
systemctl status nexusrfid.service

# View logs
journalctl -u nexusrfid.service -f

# Stop/start/restart
sudo systemctl stop nexusrfid.service
sudo systemctl start nexusrfid.service
sudo systemctl restart nexusrfid.service

# Uninstall
sudo scripts/uninstall_service.sh
```