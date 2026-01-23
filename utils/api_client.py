import time
import uuid
import json
import os
import base64
import hashlib
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from settings import API_CONFIG
from utils.logger import logger


class ApiClient:

    def __init__(self):
        self.token = None
        self.token_expires_at = 0
        self._update_config_values()

    def _update_config_values(self):
        """Update cached config values from API_CONFIG"""
        self.auth0_url = API_CONFIG.get('auth0_url')
        
        # Decrypt credentials when needed
        self.client_id = self._decrypt_config_value(API_CONFIG.get('client_id'))
        self.client_secret = self._decrypt_config_value(API_CONFIG.get('client_secret'))
        
        self.audience = API_CONFIG.get('audience')
        self.health_url = API_CONFIG.get('health_url')
        self.record_url = API_CONFIG.get('record_url')
        self.user_name = API_CONFIG.get('user_name', 'Unknown')

    def update_config(self):
        """Update config values when configuration is reloaded"""
        self._update_config_values()
        logger.debug("API client config values updated")

    def _session(self):
        retry_strategy = Retry(total=1, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])  # type: ignore
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)
        return http

    def _decrypt_config_value(self, value: str | None) -> str | None:
        """Decrypt a config value using a static, in-code obfuscation scheme.

        Requirements satisfied:
        - No external store, no env vars.
        - Same app bundle works on many devices.
        - Only values explicitly marked as encrypted are processed.

        Format: "enc:" + base64-url(payload_bytes)
        Where payload_bytes are produced from plaintext as:
            c[i] = (p[i] ^ k[i]) + i mod 256
        k[i] comes from a simple LCG-based byte stream seeded with a constant.
        """
        if value is None or value == "":
            return value

        prefix = "enc:"
        if not value.startswith(prefix):
            return value

        try:
            encoded = value[len(prefix):]
            data = base64.urlsafe_b64decode(encoded.encode("utf-8"))

            # LCG parameters (Numerical Recipes): state = (a*state + c) mod 2^32
            a = 1664525
            c = 1013904223
            mod = 2 ** 32
            state = 0xA3C59AC3  # embedded seed

            def next_key_byte() -> int:
                nonlocal state
                state = (a * state + c) % mod
                return (state >> 24) & 0xFF

            out = bytearray(len(data))
            for i, b in enumerate(data):
                k = next_key_byte()
                out[i] = ((b - (i % 256)) & 0xFF) ^ k
            return out.decode("utf-8")
        except Exception as exc:
            logger.warning(f"Failed to decrypt config value (static), using as-is: {exc}")
            return value

    def refresh_token(self):
        """Get Auth0 access token using client credentials flow"""
        payload = json.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience,
            "grant_type": "client_credentials",
            "scope": "create:scans"
        })
        headers = {
            'content-type': 'application/json'
        }
        
        http = self._session()
        try:
            response = http.post(self.auth0_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    # Set expiration time (default to 1 hour if not provided)
                    expires_in = data.get('expires_in', 3600)
                    self.token_expires_at = time.time() + expires_in - 60  # Refresh 1 minute early
                    logger.debug('Received Auth0 token successfully!')
                    return True
        except Exception as e:
            logger.error(f"Auth0 token refresh failed: {e}")
        finally:
            http.close()
        return False

    def _headers(self):
        # Check if token needs refresh (refresh 2 minutes early to avoid blocking during upload)
        if not self.token or time.time() >= (self.token_expires_at - 120):
            if not self.refresh_token():
                logger.warning("Failed to refresh token, proceeding without authentication")
        
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "idempotency-Key": "1"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def upload_health(self, rfid_status: bool, gps_status_text: str, lat: float, lon: float):
        if not self.health_url:
            return False
        payload = {
            "userName": self.user_name,
            "rfidStatus": "Connected" if rfid_status else "Disconnected",
            "gpsStatus": gps_status_text,
            "macAddress": '-'.join(('%012X' % uuid.getnode())[i:i + 2] for i in range(0, 12, 2)),
            "lat": lat,
            "lng": lon,
            "dateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        http = self._session()
        try:
            response = http.post(self.health_url, headers=self._headers(), json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Check for new API response format
            if data.get('isSuccess') == True and data.get('status') == 'Ok':
                logger.debug(f"Health data uploaded successfully: {payload['userName']} - RFID: {payload['rfidStatus']}, GPS: {payload['gpsStatus']}")
                return True
            # Fallback to old format
            success = data.get('metadata', {}).get('code') == '200'
            if success:
                logger.debug(f"Health data uploaded successfully (legacy format): {payload['userName']} - RFID: {payload['rfidStatus']}, GPS: {payload['gpsStatus']}")
            else:
                logger.warning(f"Health upload failed: isSuccess={data.get('isSuccess')}, status={data.get('status')}, errors={data.get('errors', [])}")
            return success
        except requests.exceptions.HTTPError as e:
            # HTTP error (4xx, 5xx)
            try:
                error_body = e.response.text if e.response else "No response body"
                logger.error(f"Uploading health data failed: HTTP {e.response.status_code if e.response else 'Unknown'} - {error_body}")
            except:
                logger.error(f"Uploading health data failed: HTTP error - {str(e)}")
        except requests.exceptions.RequestException as e:
            # Network errors, timeouts, etc.
            logger.error(f"Uploading health data failed: Request error - {str(e)}")
        except json.JSONDecodeError as e:
            # Invalid JSON response
            logger.error(f"Uploading health data failed: Invalid JSON response - {str(e)}")
        except Exception as e:
            # Any other unexpected error
            logger.error(f"Uploading health data failed: Unexpected error - {type(e).__name__}: {str(e)}")
        finally:
            http.close()
        return False

    def upload_records(self, payload):
        if not self.record_url:
            return False
        
        # Calculate record count and payload size for logging
        record_count = len(payload) if isinstance(payload, list) else 1
        payload_size = len(json.dumps(payload).encode('utf-8'))
        
        # Use longer timeout for large payloads: base 15s + 2s per 50 records, max 60s
        # This accounts for slow upload speeds on networks
        timeout_seconds = min(60, max(15, 15 + (record_count // 50) * 2))
        
        logger.debug(f"Uploading {record_count} record(s), payload size: {payload_size / 1024:.2f} KB, timeout: {timeout_seconds}s")
        
        http = self._session()
        try:
            response = http.post(
                self.record_url, 
                headers=self._headers(), 
                json=payload, 
                timeout=timeout_seconds
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for new API response format
            if data.get('isSuccess') == True and data.get('status') == 'Ok':
                logger.debug(f"Records uploaded successfully: {record_count} record(s) for user {self.user_name}")
                return True
            # Fallback to old format
            success = data.get('metadata', {}).get('code') == '200'
            if success:
                logger.debug(f"Records uploaded successfully (legacy format): {record_count} record(s) for user {self.user_name}")
            else:
                logger.warning(f"Record upload failed: isSuccess={data.get('isSuccess')}, status={data.get('status')}, errors={data.get('errors', [])}, validationErrors={data.get('validationErrors', [])}")
            return success
        except requests.exceptions.Timeout as e:
            # Specific handling for timeout errors with payload details
            logger.error(f"Uploading records failed: Timeout after {timeout_seconds}s - {record_count} record(s), payload size: {payload_size / 1024:.2f} KB - {str(e)}")
        except requests.exceptions.HTTPError as e:
            # HTTP error (4xx, 5xx)
            try:
                error_body = e.response.text if e.response else "No response body"
                logger.error(f"Uploading records failed: HTTP {e.response.status_code if e.response else 'Unknown'} - {error_body}")
            except:
                logger.error(f"Uploading records failed: HTTP error - {str(e)}")
        except requests.exceptions.RequestException as e:
            # Network errors, timeouts, etc.
            logger.error(f"Uploading records failed: Request error - {record_count} record(s), payload size: {payload_size / 1024:.2f} KB - {str(e)}")
        except json.JSONDecodeError as e:
            # Invalid JSON response
            logger.error(f"Uploading records failed: Invalid JSON response - {str(e)}")
        except Exception as e:
            # Any other unexpected error
            logger.error(f"Uploading records failed: Unexpected error - {type(e).__name__}: {str(e)}")
        finally:
            http.close()
        return False


