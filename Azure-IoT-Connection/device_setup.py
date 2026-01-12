#!/usr/bin/env python3
"""
Device Setup Script for Nexus Locate IoT
Generates device-specific configuration from group key and user inputs
"""

import json
import hmac
import hashlib
import base64
import subprocess
from pathlib import Path
import os

CONFIG_PATH = Path("/etc/azureiotpnp/provisioning_config.json")

def load_or_prompt_env():
    """Load env.json if present and complete; otherwise prompt for values and save it.

    Returns a tuple of (env_config, env_path) or (None, None) on failure.
    """
    script_dir = Path(__file__).parent
    env_path_script = script_dir / 'env.json'
    cwd_path = Path.cwd() / 'env.json'
    project_dir_env = os.getenv('NEXUS_PROJECT_DIR')
    project_env_path = Path(project_dir_env) / 'env.json' if project_dir_env else None
    # Default primary save/read path prefers project directory when provided
    env_path = project_env_path or env_path_script

    env_config = {}
    # Prefer env.json in project directory first (if provided), then next to script, then CWD
    candidate_paths = []
    if project_env_path:
        candidate_paths.append(project_env_path)
    if env_path_script not in candidate_paths:
        candidate_paths.append(env_path_script)
    if cwd_path not in candidate_paths:
        candidate_paths.append(cwd_path)

    for candidate in candidate_paths:
        if candidate.exists():
            try:
                with open(candidate, 'r') as f:
                    env_config = json.load(f) or {}
                env_path = candidate  # Use the found file as the primary path
                break
            except json.JSONDecodeError:
                print("Error: Invalid JSON in env.json. We'll recreate it.")
                env_config = {}
            except Exception as e:
                print(f"Error reading env.json: {e}. We'll recreate it.")
                env_config = {}

    if env_config == {} and env_path.exists():
        try:
            with open(env_path, 'r') as f:
                env_config = json.load(f) or {}
        except Exception:
            pass

    def get_value(key, prompt_text, required=False):
        current_value = env_config.get(key)
        if required and (current_value is None or str(current_value).strip() == ""):
            # Keep prompting until a non-empty value is provided
            while True:
                user_input_value = input(f"{prompt_text}: ").strip()
                if user_input_value:
                    env_config[key] = user_input_value
                    break
                print("This value is required. Please enter a non-empty value.")
        else:
            # Optional value: only prompt if key missing
            if current_value is None:
                user_input_value = input(f"{prompt_text} (optional, press Enter to skip): ").strip()
                env_config[key] = user_input_value

        return env_config.get(key)

    # Required values
    get_value('group_key', 'Enter Group Key', required=True)
    get_value('idScope', 'Enter ID Scope', required=True)

    # Required for device updates (blob storage access)
    get_value('storageAccount', 'Enter Storage Account name', required=True)
    get_value('containerName', 'Enter Container Name', required=True)
    get_value('sasToken', 'Enter SAS Token', required=True)

    # Save primarily to project directory if provided; otherwise to script directory
    try:
        with open(env_path, 'w') as f:
            json.dump(env_config, f, indent=2)
        print(f"Saved configuration to {env_path}")
    except Exception as e:
        print(f"Error saving env.json to primary location: {e}")
        return None, None

    # Also save to script directory if different and primary was project directory
    if env_path_script != env_path:
        try:
            with open(env_path_script, 'w') as f:
                json.dump(env_config, f, indent=2)
            print(f"Saved configuration to {env_path_script}")
        except Exception as e:
            print(f"Warning: could not save env.json next to script: {e}")

    # Also save to current working directory if different
    if cwd_path != env_path:
        try:
            with open(cwd_path, 'w') as f:
                json.dump(env_config, f, indent=2)
            print(f"Saved configuration to {cwd_path}")
        except Exception as e:
            print(f"Warning: could not save env.json to current directory: {e}")

    # All required values are guaranteed at this point

    return env_config, env_path

def get_device_serial():
    """Get device serial number"""
    try:
        result = subprocess.run(['cat', '/proc/cpuinfo'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith('Serial'):
                serial = line.split(':')[1].strip().lstrip('0')
                return serial if serial else "unknown"
    except:
        pass
    return "unknown"

def compute_derived_key(group_key, registration_id):
    """Compute device-specific key from group key and registration ID"""
    try:
        key_bytes = base64.b64decode(group_key)
        message = registration_id.encode('utf-8')
        signed_hmac = hmac.new(key_bytes, message, hashlib.sha256)
        derived_key = base64.b64encode(signed_hmac.digest()).decode('utf-8')
        return derived_key
    except Exception as e:
        print(f"Error computing derived key: {e}")
        return None

def get_user_input():
    """Get configuration inputs from user"""
    print("=" * 60)
    print("Nexus Locate IoT Device Setup")
    print("=" * 60)
    
    # Show device serial number
    serial = get_device_serial()
    print(f"\nDevice Serial Number: {serial}")
    print(f"Device ID: {serial}")
    
    # Ensure configuration from env.json or prompt the user to create/update it
    env_config, env_path = load_or_prompt_env()
    if not env_config:
        return None

    group_key = env_config.get('group_key')
    id_scope = env_config.get('idScope')
    storage_account = env_config.get('storageAccount')
    container_name = env_config.get('containerName')
    sas_token = env_config.get('sasToken')
    
    # Set default values
    device_id = serial
    site_name = "Lazer"
    truck_number = serial
    
    print(f"\nConfiguration loaded from env.json:")
    print(f"ID Scope: {id_scope}")
    print(f"Site Name: {site_name}")
    print(f"Truck Number: {truck_number}")
    print(f"Device ID: {device_id}")
    
    return {
        'group_key': group_key,
        'device_id': device_id,
        'id_scope': id_scope,
        'site_name': site_name,
        'truck_number': truck_number,
        'serial': serial,
        'storage_account': storage_account,
        'container_name': container_name,
        'sas_token': sas_token
    }

def save_configuration(inputs):
    """Generate and save device configuration"""
    # Generate device-specific symmetric key
    derived_key = compute_derived_key(inputs['group_key'], inputs['device_id'])
    if not derived_key:
        return False
    
    # Create configuration
    config = {
        "globalEndpoint": "global.azure-devices-provisioning.net",
        "idScope": inputs['id_scope'],
        "group_key": inputs['group_key'],
        "registrationId": inputs['device_id'],
        "symmetricKey": derived_key,
        "tags": {
            "nexusLocate": {
                "siteName": inputs['site_name'],
                "truckNumber": inputs['truck_number'],
                "deviceSerial": inputs['serial']
            }
        },
        "deviceUpdate": {
            # Defaults as requested
            "blobBasePath": "builds",
            "currentVersion": "20250826.1",
            # Values pulled from env.json
            "storageAccount": inputs.get('storage_account') or "",
            "containerName": inputs.get('container_name') or "",
            "sasToken": inputs.get('sas_token') or ""
        }
    }
    
    try:
        # Create directory if it doesn't exist
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
        
        # Set proper permissions
        subprocess.run(['sudo', 'chmod', '600', str(CONFIG_PATH)], check=True)
        
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def main():
    # Check if already configured
    if CONFIG_PATH.exists():
        print("Device is already configured!")
        response = input("Do you want to reconfigure? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Setup cancelled.")
            return
    
    # Get user inputs
    inputs = get_user_input()
    if not inputs:
        print("Setup failed due to missing inputs.")
        return
    
    # Show summary
    print("\n" + "=" * 60)
    print("Configuration Summary:")
    print("=" * 60)
    print(f"Device ID: {inputs['device_id']}")
    print(f"ID Scope: {inputs['id_scope']}")
    print(f"Site Name: {inputs['site_name']}")
    print(f"Truck Number: {inputs['truck_number']}")
    print(f"Device Serial: {inputs['serial']}")
    print("=" * 60)
    
    # Automatically save configuration
    print("\nSaving configuration automatically...")
    
    # Save configuration
    if save_configuration(inputs):
        print(f"\n✓ Configuration saved to {CONFIG_PATH}")
        print("✓ Device setup completed successfully!")
        print("\nNext steps:")
        print("1. Install and start the IoT service")
        print("2. The device will automatically connect to Azure IoT Hub")
    else:
        print("\n✗ Failed to save configuration")

if __name__ == "__main__":
    from datetime import datetime
    main()
