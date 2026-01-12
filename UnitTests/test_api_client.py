import unittest
from unittest import mock
import time


class TestApiClient(unittest.TestCase):
    def setUp(self):
        from utils import api_client as api_module
        self.api = api_module

    def test_init_defaults(self):
        with mock.patch.object(self.api, 'API_CONFIG', {}):
            client = self.api.ApiClient()
            self.assertIsNone(client.token)
            self.assertEqual(client.token_expires_at, 0)
            self.assertIsNone(client.auth0_url)
            self.assertIsNone(client.client_id)
            self.assertIsNone(client.client_secret)
            self.assertIsNone(client.audience)
            self.assertIsNone(client.health_url)
            self.assertIsNone(client.record_url)
            self.assertEqual(client.user_name, 'Unknown')

    def test_session_created_with_retry(self):
        client = self.api.ApiClient()
        with mock.patch('utils.api_client.requests.Session') as mock_sess, \
             mock.patch('utils.api_client.HTTPAdapter') as mock_adapter, \
             mock.patch('utils.api_client.Retry') as mock_retry:
            s = mock.MagicMock()
            mock_sess.return_value = s
            session = client._session()
            self.assertIs(session, s)
            mock_retry.assert_called()
            mock_adapter.assert_called()
            s.mount.assert_called()


    def test_refresh_token_success(self):
        client = self.api.ApiClient()
        client.auth0_url = 'https://example.auth0.com/oauth/token'
        client.client_id = 'test_client_id'
        client.client_secret = 'test_client_secret'
        client.audience = 'test_audience'
        with mock.patch.object(client, '_session') as ms:
            sess = mock.MagicMock()
            ms.return_value = sess
            resp = mock.MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                'access_token': 'test_token',
                'expires_in': 3600
            }
            sess.post.return_value = resp
            ok = client.refresh_token()
            self.assertTrue(ok)
            self.assertEqual(client.token, 'test_token')
            self.assertGreater(client.token_expires_at, time.time())
            sess.close.assert_called()

    def test_refresh_token_failure_and_no_url(self):
        client = self.api.ApiClient()
        client.auth0_url = 'https://example.auth0.com/oauth/token'
        client.client_id = 'test_client_id'
        client.client_secret = 'test_client_secret'
        client.audience = 'test_audience'
        with mock.patch.object(client, '_session') as ms:
            sess = mock.MagicMock()
            ms.return_value = sess
            resp = mock.MagicMock()
            resp.status_code = 400
            resp.raise_for_status.side_effect = Exception('Bad request')
            sess.post.return_value = resp
            self.assertFalse(client.refresh_token())
        client.auth0_url = None
        self.assertFalse(client.refresh_token())

    def test_upload_health_success_and_failure(self):
        client = self.api.ApiClient()
        client.health_url = 'https://example/health'
        client.user_name = 'User'
        with mock.patch.object(client, '_session') as ms, \
             mock.patch.object(client, '_headers', return_value={'Authorization': 'x'}):
            sess = mock.MagicMock()
            ms.return_value = sess
            # Test new API format success
            ok_resp = mock.MagicMock()
            ok_resp.json.return_value = {'isSuccess': True, 'status': 'Ok'}
            sess.post.return_value = ok_resp
            self.assertTrue(client.upload_health(True, 'Connected', 1.0, 2.0))
            # Test legacy API format success
            legacy_resp = mock.MagicMock()
            legacy_resp.json.return_value = {'metadata': {'code': '200'}}
            sess.post.return_value = legacy_resp
            self.assertTrue(client.upload_health(True, 'Connected', 1.0, 2.0))
            # Test failure
            bad_resp = mock.MagicMock()
            bad_resp.json.return_value = {'isSuccess': False, 'status': 'Error'}
            sess.post.return_value = bad_resp
            self.assertFalse(client.upload_health(True, 'Connected', 1.0, 2.0))
        client.health_url = None
        self.assertFalse(client.upload_health(True, 'Connected', 1.0, 2.0))

    def test_upload_records_success_failure_exception(self):
        client = self.api.ApiClient()
        client.record_url = 'https://example/rec'
        # New API format - array of records
        payload = [
            {
                "rfidTag": "019817e3-daa8-76e0-a844-c639ed12ac32",
                "latitude": 33.00652,
                "longitude": -96.6927,
                "speed": 15,
                "deviceId": "1234-er45-65d5-86gh",
                "siteId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "isProcessed": False,
                "antenna": 1
            }
        ]
        with mock.patch.object(client, '_session') as ms, \
             mock.patch.object(client, '_headers', return_value={'Authorization': 'x'}):
            sess = mock.MagicMock()
            ms.return_value = sess
            # Test new API format success
            ok_resp = mock.MagicMock()
            ok_resp.json.return_value = {'isSuccess': True, 'status': 'Ok'}
            sess.post.return_value = ok_resp
            self.assertTrue(client.upload_records(payload))
            # Test legacy API format success
            legacy_resp = mock.MagicMock()
            legacy_resp.json.return_value = {'metadata': {'code': '200'}}
            sess.post.return_value = legacy_resp
            self.assertTrue(client.upload_records(payload))
            # Test failure
            bad_resp = mock.MagicMock()
            bad_resp.json.return_value = {'isSuccess': False, 'status': 'Error'}
            sess.post.return_value = bad_resp
            self.assertFalse(client.upload_records(payload))
        with mock.patch.object(client, '_session') as ms:
            sess = mock.MagicMock()
            ms.return_value = sess
            sess.post.side_effect = Exception('net')
            self.assertFalse(client.upload_records(payload))
        client.record_url = None
        self.assertFalse(client.upload_records(payload))

    def test_decrypt_config_value(self):
        client = self.api.ApiClient()
        # Test non-encrypted value
        result = client._decrypt_config_value("plain_text")
        self.assertEqual(result, "plain_text")
        
        # Test None value
        result = client._decrypt_config_value(None)
        self.assertIsNone(result)
        
        # Test empty string
        result = client._decrypt_config_value("")
        self.assertEqual(result, "")
        
        # Test encrypted value (this would need a real encrypted string to test properly)
        # For now, just test that it handles the prefix correctly
        result = client._decrypt_config_value("enc:invalid_base64")
        self.assertEqual(result, "enc:invalid_base64")  # Should return as-is on error

    def test_headers_with_token_expiration(self):
        client = self.api.ApiClient()
        client.token = 'test_token'
        client.token_expires_at = time.time() + 3600  # Valid for 1 hour
        
        with mock.patch.object(client, 'refresh_token', return_value=True) as mock_refresh:
            headers = client._headers()
            self.assertEqual(headers['Authorization'], 'Bearer test_token')
            mock_refresh.assert_not_called()  # Should not refresh if token is valid
            
        # Test token expiration
        client.token_expires_at = time.time() - 1  # Expired
        with mock.patch.object(client, 'refresh_token', return_value=True) as mock_refresh:
            headers = client._headers()
            mock_refresh.assert_called_once()
            
        # Test refresh failure - the method doesn't clear the token, just logs a warning
        client.token_expires_at = time.time() - 1  # Expired
        with mock.patch.object(client, 'refresh_token', return_value=False) as mock_refresh:
            headers = client._headers()
            # The token is not cleared on refresh failure, so Authorization header should still be present
            self.assertEqual(headers['Authorization'], 'Bearer test_token')

    def test_headers_without_token(self):
        client = self.api.ApiClient()
        client.token = None
        with mock.patch.object(client, 'refresh_token', return_value=False) as mock_refresh:
            headers = client._headers()
            self.assertEqual(headers['Content-Type'], 'application/json')
            self.assertEqual(headers['accept'], 'application/json')
            self.assertEqual(headers['idempotency-Key'], '1')
            self.assertNotIn('Authorization', headers)
            mock_refresh.assert_called_once()


if __name__ == '__main__':
    unittest.main()


