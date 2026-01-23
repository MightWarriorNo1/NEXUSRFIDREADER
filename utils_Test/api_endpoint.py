#!/usr/bin/env python3
"""
Comprehensive API Endpoint Test Script
Tests the complete API flow from authentication to data upload
"""

import sys
import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import project modules
from settings import API_CONFIG
from utils.logger import logger


class ApiEndpointTester:
    """Comprehensive API endpoint tester"""
    
    def __init__(self):
        # self.auth0_url = "https://dev-0m8cx6xlg7z8zy6j.us.auth0.com/oauth/token"
        # self.client_id = "dC1zM4ghLvr8eipSOlmRhAelHRXdtvNC"
        # self.client_secret = "M__OTtIL7Pw754RBKIEEOCrXsxTef61vWny57keAXqwNN6mvylhg5Yc4XNtajqk4"
        # self.record_url = "http://test-api-locate.nexusyms.com/api/sites/0198c311-4801-7445-b73a-3a7dce72c6f6/scans"
        self.auth0_url = "https://test-auth.nexusyms.com/oauth/token"
        self.client_id = "pBwSiPtKmklfuqgZ7KUE05GPYkmySNiT"
        self.client_secret = "C2AOzwrW1HxJ4t1gAUa8tdvZnhomVINUNDzj6hLtPxK_KTq5JIt4pHRMgl2m3-dd"
        self.record_url = "https://apim-test-spotlight.azure-api.net/nexus-locate/api/sites/0198c311-4801-7445-b73a-3a7dce72c6f6/scans"
        self.audience = "https://nexus-locate-api"
        self.health_url = API_CONFIG.get('health_url')
        self.user_name = API_CONFIG.get('user_name', 'TestUser')
        self.site_id = API_CONFIG.get('site_id', 'NexusLocate')
        
        self.token = None
        self.token_expires_at = 0
        self.test_results = {
            'auth_test': False,
            'health_upload_test': False,
            'record_upload_test': False,
            'error_details': []
        }
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def test_auth0_authentication(self) -> bool:
        """Test Auth0 authentication flow"""
        print("Testing Auth0 Authentication...")
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience,
            "grant_type": "client_credentials",
            "scope": "create:scans"
        }
        
        headers = {
            'content-type': 'application/json'
        }
        
        session = self._create_session()
        try:
            print(f"Sending request to: {self.auth0_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = session.post(
                self.auth0_url, 
                headers=headers, 
                json=payload, 
                timeout=15
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Authentication successful!")
                print(f"Token received: {data.get('access_token', 'N/A')}")
                print(f"Expires in: {data.get('expires_in', 'N/A')} seconds")
                print(f"Token type: {data.get('token_type', 'N/A')}")
                print(f"Scope: {data.get('scope', 'N/A')}")
                
                self.token = data['access_token']
                expires_in = data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in - 60
                
                self.test_results['auth_test'] = True
                return True
            else:
                print(f"Authentication failed!")
                print(f"Response: {response.text}")
                self.test_results['error_details'].append(f"Auth failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            self.test_results['error_details'].append(f"Auth error: {str(e)}")
            return False
        finally:
            session.close()
    
    def test_health_endpoint(self) -> bool:
        """Test health data upload endpoint"""
        print("\nTesting Health Data Upload...")
        
        if not self.health_url:
            print("Health URL not configured in settings")
            self.test_results['error_details'].append("Health URL not configured")
            return False
        
        if not self.token:
            print("No authentication token available")
            return False
        
        # Generate test health data
        mac_address = '-'.join(('%012X' % uuid.getnode())[i:i + 2] for i in range(0, 12, 2))
        payload = {
            "userName": self.user_name,
            "rfidStatus": "Connected",
            "gpsStatus": "Connected",
            "macAddress": mac_address,
            "lat": 33.00652,
            "lng": -96.6927,
            "dateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "idempotency-Key": "1",
            "Authorization": f"Bearer {self.token}"
        }
        
        session = self._create_session()
        try:
            print(f"Sending request to: {self.health_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Using token: {self.token}")
            
            response = session.post(
                self.health_url, 
                headers=headers, 
                json=payload, 
                timeout=10
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check for new API response format
                    if data.get('isSuccess') == True and data.get('status') == 'Ok':
                        print("Health data upload successful!")
                        self.test_results['health_upload_test'] = True
                        return True
                    # Fallback to old format
                    elif data.get('metadata', {}).get('code') == '200':
                        print("Health data upload successful!")
                        self.test_results['health_upload_test'] = True
                        return True
                    else:
                        print(f"Health upload failed: {data}")
                        self.test_results['error_details'].append(f"Health upload failed: {data}")
                        return False
                except json.JSONDecodeError:
                    print("Invalid JSON response")
                    self.test_results['error_details'].append("Invalid JSON response from health endpoint")
                    return False
            else:
                print(f"Health upload failed with status: {response.status_code}")
                self.test_results['error_details'].append(f"Health upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Health upload error: {str(e)}")
            self.test_results['error_details'].append(f"Health upload error: {str(e)}")
            return False
        finally:
            session.close()
    
    def test_record_upload_endpoint(self) -> bool:
        """Test RFID record upload endpoint"""
        print("\nTesting RFID Record Upload...")
        
        if not self.record_url:
            print("Record URL not configured in settings")
            self.test_results['error_details'].append("Record URL not configured")
            return False
        
        if not self.token:
            print("No authentication token available")
            return False
        
        # Generate test record data
        device_id = str(uuid.uuid4())
        mac_address = '-'.join(('%012X' % uuid.getnode())[i:i + 2] for i in range(0, 12, 2))
        
        payload = [
            {
                "siteId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "tagName": str(uuid.uuid4()),
                "latitude": 33.00652,
                "longitude": -96.6927,
                "speed": 15,
                "deviceId": device_id,
                "barrier": "90",
                "antenna": 1,
                "isProcess": True
            },
            {
                "siteId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "tagName": str(uuid.uuid4()),
                "latitude": 33.00655,
                "longitude": -96.6928,
                "speed": 12,
                "deviceId": device_id,
                "barrier": "90",
                "antenna": 2,
                "isProcess": True
            }
        ]
        
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "idempotency-Key": "1",
            "Authorization": f"Bearer {self.token}"
        }
        
        session = self._create_session()
        try:
            print(f"Sending request to: {self.record_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Using token: {self.token}")
            
            response = session.post(
                self.record_url, 
                headers=headers, 
                json=payload, 
                timeout=10
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response Analysis:")
                    print(f"  - isSuccess: {data.get('isSuccess')}")
                    print(f"  - status: {data.get('status')}")
                    print(f"  - value: {data.get('value')}")
                    print(f"  - errors: {data.get('errors', [])}")
                    print(f"  - validationErrors: {data.get('validationErrors', [])}")
                    
                    # Check for new API response format
                    if data.get('isSuccess') == True and data.get('status') == 'Ok':
                        print("Record upload successful!")
                        self.test_results['record_upload_test'] = True
                        return True
                    # Fallback to old format
                    elif data.get('metadata', {}).get('code') == '200':
                        print("Record upload successful!")
                        self.test_results['record_upload_test'] = True
                        return True
                    else:
                        print(f"Record upload failed: {data}")
                        self.test_results['error_details'].append(f"Record upload failed: {data}")
                        return False
                except json.JSONDecodeError:
                    print("Invalid JSON response")
                    self.test_results['error_details'].append("Invalid JSON response from record endpoint")
                    return False
            else:
                print(f"Record upload failed with status: {response.status_code}")
                self.test_results['error_details'].append(f"Record upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Record upload error: {str(e)}")
            self.test_results['error_details'].append(f"Record upload error: {str(e)}")
            return False
        finally:
            session.close()
    
    def test_token_refresh(self) -> bool:
        """Test token refresh functionality"""
        print("\nTesting Token Refresh...")
        
        if not self.token:
            print("No token to refresh")
            return False
        
        # Store original token for comparison
        original_token = self.token
        original_expires_at = self.token_expires_at
        
        # Force refresh by setting expiration to past
        self.token_expires_at = time.time() - 1
        
        # Add small delay to ensure different timestamp
        time.sleep(1)
        
        success = self.test_auth0_authentication()
        
        # Check if we got a new token (different content or different expiration)
        if success and (self.token != original_token or self.token_expires_at != original_expires_at):
            print("Token refresh successful!")
            print(f"Original token expires at: {original_expires_at}")
            print(f"New token expires at: {self.token_expires_at}")
            return True
        else:
            print("Token refresh failed!")
            print("Note: Tokens may be identical due to caching or same timestamp")
            return False
    
    def test_network_connectivity(self) -> bool:
        """Test basic network connectivity"""
        print("\nTesting Network Connectivity...")
        
        test_urls = [
            "https://httpbin.org/get",
            "https://test-auth.nexusyms.com/oauth/token",
            "https://apim-test-spotlight.azure-api.net/nexus-locate/api/sites/0198c311-4801-7445-b73a-3a7dce72c6f6/scans"
        ]
        
        session = self._create_session()
        connectivity_ok = True
        
        for url in test_urls:
            try:
                print(f"Testing: {url}")
                response = session.get(url, timeout=5)
                if response.status_code in [200, 404, 405]:  # 404/405 are OK for some endpoints
                    print(f"{url} - OK ({response.status_code})")
                else:
                    print(f"{url} - Status {response.status_code}")
            except Exception as e:
                print(f"{url} - Error: {str(e)}")
                connectivity_ok = False
        
        session.close()
        return connectivity_ok
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all API tests in sequence"""
        print("Starting Comprehensive API Endpoint Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Network connectivity
        network_ok = self.test_network_connectivity()
        
        # Test 2: Authentication
        auth_ok = self.test_auth0_authentication()
        
        # Test 3: Health endpoint (if configured)
        health_ok = True
        if self.health_url:
            health_ok = self.test_health_endpoint()
        else:
            print("\nSkipping Health Endpoint Test (not configured)")
        
        # Test 4: Record upload endpoint
        record_ok = self.test_record_upload_endpoint()
        
        # Test 5: Token refresh
        refresh_ok = self.test_token_refresh()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Duration: {duration:.2f} seconds")
        print(f"Network Connectivity: {'PASS' if network_ok else 'FAIL'}")
        print(f"Authentication: {'PASS' if auth_ok else 'FAIL'}")
        print(f"Health Upload: {'PASS' if health_ok else 'FAIL' if self.health_url else 'SKIPPED'}")
        print(f"Record Upload: {'PASS' if record_ok else 'FAIL'}")
        print(f"Token Refresh: {'PASS' if refresh_ok else 'FAIL'}")
        
        # Overall result
        all_tests_passed = network_ok and auth_ok and health_ok and record_ok and refresh_ok
        print(f"\nOverall Result: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")
        
        if self.test_results['error_details']:
            print("\nError Details:")
            for i, error in enumerate(self.test_results['error_details'], 1):
                print(f"   {i}. {error}")
        
        return {
            'overall_success': all_tests_passed,
            'network_ok': network_ok,
            'auth_ok': auth_ok,
            'health_ok': health_ok,
            'record_ok': record_ok,
            'refresh_ok': refresh_ok,
            'duration': duration,
            'errors': self.test_results['error_details']
        }


def main():
    """Main test execution"""
    print("NexusRFID API Endpoint Test Suite")
    print("=" * 60)
    
    # Initialize tester
    tester = ApiEndpointTester()
    
    # Display configuration
    print("Configuration:")
    print(f"   Auth0 URL: {tester.auth0_url}")
    print(f"   Client ID: {tester.client_id[:10]}...")
    print(f"   Audience: {tester.audience}")
    print(f"   Record URL: {tester.record_url}")
    print(f"   Health URL: {tester.health_url}")
    print(f"   User Name: {tester.user_name}")
    print(f"   Site ID: {tester.site_id}")
    print()
    
    # Run tests
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)


if __name__ == "__main__":
    main()
