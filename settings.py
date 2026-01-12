import json
import os
import platform

is_rpi = platform.system() == "Linux" and os.path.exists("/proc/device-tree/model")
is_win = platform.system() == "Windows"

if is_rpi:
    # When running with sudo, use the original user's home directory
    # Check if SUDO_USER environment variable exists (indicates sudo is being used)
    if os.environ.get('SUDO_USER'):
        sudo_user = os.environ.get('SUDO_USER')
        ROOT_DIR = os.path.join('/home', sudo_user, '.nexusrfid')
    else:
        ROOT_DIR = os.path.expanduser("~/.nexusrfid")
elif is_win:
    ROOT_DIR = os.path.expanduser("~/Documents/NexusRFID")

os.makedirs(ROOT_DIR, exist_ok=True)

INIT_SCREEN = "overview"
APP_DIR = os.path.dirname(os.path.realpath(__file__))
CRASH_FILE = os.path.join(ROOT_DIR, "crash.dump")
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
DATABASE_FILE = os.path.join(ROOT_DIR, "database.db")

# Default RFID hosts to try before running arp-scan discovery
DEFAULT_RFID_HOSTS = ["169.254.10.1", "169.254.1.1"]


def get_default_config():
    """Return default configuration values"""
    return {
        "gps_config": {
            "use_external": True,
            "baud_rate": 115200,
            "probe_baud_rate": 115200,
        },
        "rfid_config": {
            "host": "169.254.10.1",
            "port": 5084,
            "report_every_n_tags": 1,
            "antennas": "1",
            "tx_power": 0,
            "tari": 0,
            "session": 1,
            "mode_identifier": None,
            "tag_population": 4,
            "impinj_search_mode": None,
            "impinj_reports": False,
        },
        "api_config": {
            "login_url": "",
            "health_url": "",
            # "auth0_url": "https://auth.nexusyms.com/oauth/token",
            # "record_url": "https://apim-prod-spotlight.azure-api.net/nexus-locate/api/sites/019a020f-8c9a-71df-a735-a75b49d1012d/scans",
            # "client_id": "enc:NLtB_hyxb6WI9y_XmoT8YTmdyki9GB5mlLPaML8rl78=",
            # "client_secret": "enc:NrwV_TLDea6o0UXjrWWbOX6c2oekR3CVGZ4MXNWRjb2QG3QpkXlinPWzN-Jxkbik3LSwmDWbEcZKT2ft10iTGg==",
            "auth0_url": "https://test-auth.nexusyms.com/oauth/token",
            "record_url": "https://apim-test-spotlight.azure-api.net/nexus-locate/api/sites/0198c311-4801-7445-b73a-3a7dce72c6f6/scans",
            "client_id": "enc:Fos_8S--ZaKf0ArsuHXISz607BcGkpBejboEKtkmh7k=",
            "client_secret": "enc:JfsN9TyjX47T7R7Y-Xr6EGjOAIzKQWFkWrsCNtQrbLqRFmlKL2pCaQLPYbySkLegvsGxPFat7sdiRGEp23-uHw==",
            "audience": "https://nexus-locate-api",
            "email": "",
            "password": "",
            "token": "",
            "user_name": "NexusUser",
            "spotter_id": "120",
            # "site_id": "019a020f-8c9a-71df-a735-a75b49d1012d",
            "site_id": "019a9e1e-81ff-75ab-99fc-4115bb92fec6",
            "record_interval_ms": 7000,
            "health_interval_ms": 15000,
            "max_upload_records": 10,
        },
        "database_config": {
            "use_db": True,
            "max_records": 100,
            "duplicate_detection_seconds": 3,
        },
        "filter_config": {
            "speed": {
                "enabled": True,
                "min": 1,
                "max": 20,
            },
            "rssi": {
                "enabled": False,
                "min": -80,
                "max": 0,
            },
            "tag_range": {
                "enabled": False,
                "min": 0,
                "max": 999999999,
            },
        },
        "baud_rate_don": 9600,
        "internet_limit_time": 5,
    }


def load_config():
    """Load configuration from JSON file, or create with defaults if it doesn't exist"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            # Merge with defaults to ensure all keys exist (in case of partial updates)
            default_config = get_default_config()
            merged_config = _deep_merge(default_config, config)
            return merged_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading config file {CONFIG_FILE}: {e}")
            print("Using default configuration and recreating config file...")
            config = get_default_config()
            save_config(config)
            return config
    else:
        # Create config file with defaults
        config = get_default_config()
        save_config(config)
        return config


def _deep_merge(default, override):
    """Deep merge two dictionaries, with override taking precedence"""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        print(f"Error writing config file {CONFIG_FILE}: {e}")


# Load configuration from JSON file
_config = load_config()

# Export configuration values for backward compatibility
GPS_CONFIG = _config["gps_config"]
RFID_CONFIG = _config["rfid_config"]
API_CONFIG = _config["api_config"]
DATABASE_CONFIG = _config["database_config"]
FILTER_CONFIG = _config["filter_config"]
BAUD_RATE_DON = _config["baud_rate_don"]
INTERNET_LIMIT_TIME = _config["internet_limit_time"]


def update_rfid_host(new_host: str):
    """Update the RFID host in the configuration file and reload config"""
    try:
        config = load_config()
        config["rfid_config"]["host"] = new_host
        save_config(config)
        # Reload to update the global RFID_CONFIG
        reload_config()
        return True
    except Exception as e:
        print(f"Error updating RFID host: {e}")
        return False


def reload_config():
    """Reload configuration from JSON file and update all config dictionaries in place"""
    global GPS_CONFIG, RFID_CONFIG, API_CONFIG, DATABASE_CONFIG, FILTER_CONFIG, BAUD_RATE_DON, INTERNET_LIMIT_TIME
    try:
        new_config = load_config()
        # Update dictionaries in place so existing references reflect changes
        GPS_CONFIG.clear()
        GPS_CONFIG.update(new_config["gps_config"])
        
        RFID_CONFIG.clear()
        RFID_CONFIG.update(new_config["rfid_config"])
        
        API_CONFIG.clear()
        API_CONFIG.update(new_config["api_config"])
        
        DATABASE_CONFIG.clear()
        DATABASE_CONFIG.update(new_config["database_config"])
        
        FILTER_CONFIG.clear()
        FILTER_CONFIG.update(new_config["filter_config"])
        
        # Update primitives (need to reassign)
        BAUD_RATE_DON = new_config["baud_rate_don"]
        INTERNET_LIMIT_TIME = new_config["internet_limit_time"]
        
        return True
    except Exception as e:
        print(f"Error reloading config: {e}")
        return False