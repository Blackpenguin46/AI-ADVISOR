"""
Unit tests for Daily.dev authentication and credential management.
"""

import os
import tempfile
import shutil
import json
import time
from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrations.dailydev_auth import CredentialManager, DailyDevAuth, create_auth_from_cookies, get_auth_from_stored


class TestCredentialManager(TestCase):
    """Test cases for CredentialManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.credentials_path = os.path.join(self.test_dir, "credentials.enc")
        self.key_path = os.path.join(self.test_dir, "key.bin")
        self.manager = CredentialManager(self.credentials_path)
        self.manager.key_path = self.key_path
        
        # Test credentials
        self.test_credentials = {
            'cookies': {'session': 'test_session', 'auth': 'test_auth'},
            'headers': {'User-Agent': 'test_agent'},
            'timestamp': time.time()
        }
        self.test_password = "test_password_123"
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_ensure_directories(self):
        """Test directory creation with secure permissions."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
        
        # Create new manager (should create directories)
        manager = CredentialManager(self.credentials_path)
        manager.key_path = self.key_path
        
        # Check directory exists
        self.assertTrue(os.path.exists(os.path.dirname(self.credentials_path)))
        
        # Check permissions (if supported)
        if hasattr(os, 'chmod'):
            stat = os.stat(os.path.dirname(self.credentials_path))
            # Check that directory has restrictive permissions
            self.assertEqual(oct(stat.st_mode)[-3:], '700')
    
    def test_generate_key_with_cryptography(self):
        """Test key generation with cryptography library."""
        password = "test_password"
        key, salt = self.manager._generate_key(password)
        
        # Check key and salt properties
        self.assertEqual(len(salt), 16)  # Salt should be 16 bytes
        self.assertIsInstance(key, bytes)
        self.assertGreater(len(key), 0)
        
        # Test that same password + salt generates same key
        key2, _ = self.manager._generate_key(password, salt)
        self.assertEqual(key, key2)
        
        # Test that different passwords generate different keys
        key3, _ = self.manager._generate_key("different_password", salt)
        self.assertNotEqual(key, key3)
    
    def test_encrypt_decrypt_credentials(self):
        """Test credential encryption and decryption."""
        # Encrypt credentials
        self.manager.encrypt_credentials(self.test_credentials, self.test_password)
        
        # Check files were created
        self.assertTrue(os.path.exists(self.credentials_path))
        self.assertTrue(os.path.exists(self.key_path))
        
        # Check file permissions
        if hasattr(os, 'chmod'):
            cred_stat = os.stat(self.credentials_path)
            key_stat = os.stat(self.key_path)
            self.assertEqual(oct(cred_stat.st_mode)[-3:], '600')
            self.assertEqual(oct(key_stat.st_mode)[-3:], '600')
        
        # Decrypt credentials
        decrypted = self.manager.decrypt_credentials(self.test_password)
        
        # Verify decrypted data matches original
        self.assertEqual(decrypted, self.test_credentials)
    
    def test_decrypt_with_wrong_password(self):
        """Test decryption with wrong password."""
        # Encrypt with correct password
        self.manager.encrypt_credentials(self.test_credentials, self.test_password)
        
        # Try to decrypt with wrong password
        decrypted = self.manager.decrypt_credentials("wrong_password")
        
        # Should return empty dict on failure
        self.assertEqual(decrypted, {})
    
    def test_decrypt_nonexistent_credentials(self):
        """Test decryption when no credentials exist."""
        decrypted = self.manager.decrypt_credentials(self.test_password)
        self.assertEqual(decrypted, {})
    
    def test_clear_credentials(self):
        """Test secure credential deletion."""
        # Create credentials
        self.manager.encrypt_credentials(self.test_credentials, self.test_password)
        
        # Verify files exist
        self.assertTrue(os.path.exists(self.credentials_path))
        self.assertTrue(os.path.exists(self.key_path))
        
        # Clear credentials
        self.manager.clear_credentials()
        
        # Verify files are deleted
        self.assertFalse(os.path.exists(self.credentials_path))
        self.assertFalse(os.path.exists(self.key_path))
        
        # Verify encryption key is cleared from memory
        self.assertIsNone(self.manager.encryption_key)
    
    def test_validate_credentials_format(self):
        """Test credential format validation."""
        # Valid credentials
        valid_creds = {
            'cookies': {'session': 'test'},
            'headers': {'User-Agent': 'test'},
            'timestamp': time.time()
        }
        self.assertTrue(self.manager.validate_credentials_format(valid_creds))
        
        # Invalid credentials - missing field
        invalid_creds1 = {
            'cookies': {'session': 'test'},
            'headers': {'User-Agent': 'test'}
            # Missing timestamp
        }
        self.assertFalse(self.manager.validate_credentials_format(invalid_creds1))
        
        # Invalid credentials - wrong type
        invalid_creds2 = {
            'cookies': "not_a_dict",
            'headers': {'User-Agent': 'test'},
            'timestamp': time.time()
        }
        self.assertFalse(self.manager.validate_credentials_format(invalid_creds2))
        
        # Invalid credentials - not a dict
        self.assertFalse(self.manager.validate_credentials_format("not_a_dict"))
    
    def test_credentials_exist(self):
        """Test credential existence check."""
        # Initially no credentials
        self.assertFalse(self.manager.credentials_exist())
        
        # Create credentials
        self.manager.encrypt_credentials(self.test_credentials, self.test_password)
        
        # Now credentials exist
        self.assertTrue(self.manager.credentials_exist())
    
    def test_get_credentials_info(self):
        """Test credential information retrieval."""
        # No credentials initially
        info = self.manager.get_credentials_info()
        self.assertFalse(info['exists'])
        
        # Create credentials
        self.manager.encrypt_credentials(self.test_credentials, self.test_password)
        
        # Get info
        info = self.manager.get_credentials_info()
        self.assertTrue(info['exists'])
        self.assertIn('created', info)
        self.assertIn('modified', info)
        self.assertIn('size', info)
        self.assertIn('permissions', info)
        self.assertGreater(info['size'], 0)
    
    @patch('integrations.dailydev_auth.ENCRYPTION_AVAILABLE', False)
    def test_fallback_encryption(self):
        """Test fallback encryption when cryptography is unavailable."""
        # Create new manager with fallback
        manager = CredentialManager(self.credentials_path)
        manager.key_path = self.key_path
        
        # Encrypt and decrypt
        manager.encrypt_credentials(self.test_credentials, self.test_password)
        decrypted = manager.decrypt_credentials(self.test_password)
        
        # Should still work with fallback
        self.assertEqual(decrypted, self.test_credentials)


class TestDailyDevAuth(TestCase):
    """Test cases for DailyDevAuth class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create auth instance with test directory
        self.auth = DailyDevAuth()
        self.auth.credential_manager.credentials_path = os.path.join(self.test_dir, "credentials.enc")
        self.auth.credential_manager.key_path = os.path.join(self.test_dir, "key.bin")
        
        # Test data
        self.test_credentials = {
            'cookies': {'session': 'test_session', 'auth': 'test_auth'},
            'headers': {'User-Agent': 'test_agent'},
            'timestamp': time.time()
        }
        self.test_password = "test_password_123"
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_store_and_login(self):
        """Test credential storage and login."""
        # Store credentials
        success = self.auth.store_credentials(self.test_credentials, self.test_password)
        self.assertTrue(success)
        
        # Check authentication status
        self.assertTrue(self.auth.is_authenticated())
        
        # Create new auth instance and login
        new_auth = DailyDevAuth()
        new_auth.credential_manager.credentials_path = self.auth.credential_manager.credentials_path
        new_auth.credential_manager.key_path = self.auth.credential_manager.key_path
        
        login_success = new_auth.login(password=self.test_password)
        self.assertTrue(login_success)
        self.assertTrue(new_auth.is_authenticated())
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credential format."""
        # Store invalid credentials
        invalid_creds = {'invalid': 'format'}
        
        # Should fail validation
        success = self.auth.store_credentials(invalid_creds, self.test_password)
        self.assertFalse(success)
    
    def test_login_no_credentials(self):
        """Test login when no credentials exist."""
        success = self.auth.login(password=self.test_password)
        self.assertFalse(success)
        self.assertFalse(self.auth.is_authenticated())
    
    def test_get_auth_data(self):
        """Test authentication data retrieval."""
        # Store credentials
        self.auth.store_credentials(self.test_credentials, self.test_password)
        
        # Get auth data
        headers = self.auth.get_auth_headers()
        cookies = self.auth.get_auth_cookies()
        config = self.auth.get_auth_config()
        
        self.assertEqual(headers, self.test_credentials['headers'])
        self.assertEqual(cookies, self.test_credentials['cookies'])
        self.assertEqual(config, self.test_credentials)
    
    def test_session_expiration(self):
        """Test session expiration handling."""
        # Store credentials
        self.auth.store_credentials(self.test_credentials, self.test_password)
        
        # Should be authenticated
        self.assertTrue(self.auth.is_authenticated())
        
        # Manually expire session
        self.auth.session_valid_until = time.time() - 1
        
        # Should no longer be authenticated
        self.assertFalse(self.auth.is_authenticated())
    
    def test_clear_credentials(self):
        """Test credential clearing."""
        # Store credentials
        self.auth.store_credentials(self.test_credentials, self.test_password)
        self.assertTrue(self.auth.is_authenticated())
        
        # Clear credentials
        self.auth.clear_credentials()
        
        # Should no longer be authenticated
        self.assertFalse(self.auth.is_authenticated())
        self.assertEqual(self.auth.credentials, {})
        self.assertEqual(self.auth.session_valid_until, 0)
    
    def test_get_session_info(self):
        """Test session information retrieval."""
        # Initially not authenticated
        info = self.auth.get_session_info()
        self.assertFalse(info['authenticated'])
        self.assertEqual(info['time_remaining'], 0)
        
        # Store credentials
        self.auth.store_credentials(self.test_credentials, self.test_password)
        
        # Get session info
        info = self.auth.get_session_info()
        self.assertTrue(info['authenticated'])
        self.assertGreater(info['time_remaining'], 0)
        self.assertTrue(info['has_cookies'])
        self.assertTrue(info['has_headers'])
        self.assertGreater(info['credential_timestamp'], 0)


class TestHelperFunctions(TestCase):
    """Test cases for helper functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_cookies = {'session': 'test_session', 'auth': 'test_auth'}
        self.test_headers = {'User-Agent': 'test_agent'}
        self.test_password = "test_password_123"
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('integrations.dailydev_auth.Path.home')
    def test_create_auth_from_cookies(self, mock_home):
        """Test creating auth from cookies."""
        mock_home.return_value = Path(self.test_dir)
        
        # Create auth from cookies
        auth = create_auth_from_cookies(
            self.test_cookies, 
            self.test_headers, 
            self.test_password
        )
        
        self.assertIsNotNone(auth)
        self.assertTrue(auth.is_authenticated())
        self.assertEqual(auth.get_auth_cookies(), self.test_cookies)
        self.assertEqual(auth.get_auth_headers(), self.test_headers)
    
    @patch('integrations.dailydev_auth.Path.home')
    def test_create_auth_from_cookies_default_headers(self, mock_home):
        """Test creating auth from cookies with default headers."""
        mock_home.return_value = Path(self.test_dir)
        
        # Create auth without custom headers
        auth = create_auth_from_cookies(self.test_cookies, password=self.test_password)
        
        self.assertIsNotNone(auth)
        headers = auth.get_auth_headers()
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Referer', headers)
    
    @patch('integrations.dailydev_auth.Path.home')
    def test_get_auth_from_stored(self, mock_home):
        """Test getting auth from stored credentials."""
        mock_home.return_value = Path(self.test_dir)
        
        # First create and store credentials
        auth1 = create_auth_from_cookies(self.test_cookies, password=self.test_password)
        self.assertIsNotNone(auth1)
        
        # Now try to load from stored
        auth2 = get_auth_from_stored(self.test_password)
        self.assertIsNotNone(auth2)
        self.assertTrue(auth2.is_authenticated())
        self.assertEqual(auth2.get_auth_cookies(), self.test_cookies)
    
    @patch('integrations.dailydev_auth.Path.home')
    def test_get_auth_from_stored_no_credentials(self, mock_home):
        """Test getting auth when no credentials are stored."""
        mock_home.return_value = Path(self.test_dir)
        
        # Try to load when no credentials exist
        auth = get_auth_from_stored(self.test_password)
        self.assertIsNone(auth)


if __name__ == '__main__':
    import unittest
    unittest.main()