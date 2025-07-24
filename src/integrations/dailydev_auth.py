"""
Secure authentication module for Daily.dev MCP integration.

This module provides secure methods for authenticating with Daily.dev,
including encrypted credential storage and token management.
"""

import json
import os
import base64
import time
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
import getpass

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("Warning: cryptography library not available. Credentials will be stored with minimal protection.")
    print("Install with: pip install cryptography")


class CredentialManager:
    """Secure credential manager for Daily.dev authentication."""
    
    def __init__(self, credentials_path: str = None):
        """Initialize credential manager."""
        self.credentials_path = credentials_path or str(Path.home() / ".dailydev" / "credentials.enc")
        self.key_path = str(Path.home() / ".dailydev" / "key.bin")
        self.encryption_key = None
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure credential directories exist with secure permissions."""
        credential_dir = os.path.dirname(self.credentials_path)
        os.makedirs(credential_dir, mode=0o700, exist_ok=True)
        
        # Set secure permissions on the directory
        try:
            os.chmod(credential_dir, 0o700)
        except OSError:
            print("Warning: Could not set secure permissions on credential directory")
    
    def _generate_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Generate encryption key from password using PBKDF2."""
        if not ENCRYPTION_AVAILABLE:
            # Simple fallback if cryptography not available
            key = (password.encode() * 4)[:32]  # Not secure, just a fallback
            salt = salt or os.urandom(16)
            return key, salt
        
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # 100,000 iterations for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def _get_encryption_key(self, password: Optional[str] = None) -> bytes:
        """Get or create encryption key."""
        if self.encryption_key:
            return self.encryption_key
        
        # Try to load existing key
        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, 'rb') as f:
                    salt = f.read(16)
                    if password is None:
                        password = getpass.getpass("Enter password to decrypt Daily.dev credentials: ")
                    key, _ = self._generate_key(password, salt)
                    self.encryption_key = key
                    return key
            except Exception as e:
                print(f"Error loading encryption key: {e}")
                raise ValueError("Failed to load encryption key. Wrong password?")
        
        # Create new key
        if password is None:
            password = getpass.getpass("Create password to encrypt Daily.dev credentials: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                raise ValueError("Passwords do not match")
        
        key, salt = self._generate_key(password)
        
        # Save salt with secure permissions
        with open(self.key_path, 'wb') as f:
            f.write(salt)
        
        # Set secure file permissions
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            print("Warning: Could not set secure permissions on key file")
        
        self.encryption_key = key
        return key
    
    def encrypt_credentials(self, credentials: Dict[str, Any], password: Optional[str] = None) -> None:
        """Encrypt and save credentials."""
        key = self._get_encryption_key(password)
        
        if not ENCRYPTION_AVAILABLE:
            # Simple obfuscation if cryptography not available
            print("Warning: Using fallback encryption. Install 'cryptography' for better security.")
            encoded = base64.b64encode(json.dumps(credentials).encode()).decode()
            with open(self.credentials_path, 'w') as f:
                f.write(encoded)
            
            # Set secure file permissions
            try:
                os.chmod(self.credentials_path, 0o600)
            except OSError:
                print("Warning: Could not set secure permissions on credentials file")
            return
        
        # Encrypt with Fernet (AES-256)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(json.dumps(credentials).encode())
        
        with open(self.credentials_path, 'wb') as f:
            f.write(encrypted)
        
        # Set secure file permissions
        try:
            os.chmod(self.credentials_path, 0o600)
        except OSError:
            print("Warning: Could not set secure permissions on credentials file")
    
    def decrypt_credentials(self, password: Optional[str] = None) -> Dict[str, Any]:
        """Decrypt and load credentials."""
        if not os.path.exists(self.credentials_path):
            return {}
        
        try:
            # Clear cached key to force password validation
            if password is not None:
                self.encryption_key = None
                
            key = self._get_encryption_key(password)
            
            if not ENCRYPTION_AVAILABLE:
                # Simple deobfuscation
                with open(self.credentials_path, 'r') as f:
                    encoded = f.read()
                return json.loads(base64.b64decode(encoded).decode())
            
            # Decrypt with Fernet
            with open(self.credentials_path, 'rb') as f:
                encrypted = f.read()
            
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted).decode()
            return json.loads(decrypted)
            
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            # Clear cached key on error
            self.encryption_key = None
            return {}
    
    def clear_credentials(self) -> None:
        """Securely delete stored credentials and keys."""
        files_to_delete = [self.credentials_path, self.key_path]
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    # Overwrite file with random data before deletion (basic secure delete)
                    file_size = os.path.getsize(file_path)
                    with open(file_path, 'wb') as f:
                        f.write(os.urandom(file_size))
                    
                    # Delete the file
                    os.remove(file_path)
                    print(f"Securely deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        # Clear encryption key from memory
        self.encryption_key = None
    
    def validate_credentials_format(self, credentials: Dict[str, Any]) -> bool:
        """Validate credential format and required fields."""
        required_fields = ['cookies', 'headers', 'timestamp']
        
        if not isinstance(credentials, dict):
            return False
        
        for field in required_fields:
            if field not in credentials:
                return False
        
        # Validate cookies is a dict
        if not isinstance(credentials['cookies'], dict):
            return False
        
        # Validate headers is a dict
        if not isinstance(credentials['headers'], dict):
            return False
        
        # Validate timestamp is a number
        if not isinstance(credentials['timestamp'], (int, float)):
            return False
        
        return True
    
    def credentials_exist(self) -> bool:
        """Check if credentials file exists."""
        return os.path.exists(self.credentials_path)
    
    def get_credentials_info(self) -> Dict[str, Any]:
        """Get information about stored credentials without decrypting."""
        if not self.credentials_exist():
            return {"exists": False}
        
        try:
            stat = os.stat(self.credentials_path)
            return {
                "exists": True,
                "created": time.ctime(stat.st_ctime),
                "modified": time.ctime(stat.st_mtime),
                "size": stat.st_size,
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}


class DailyDevAuth:
    """Authentication handler for Daily.dev."""
    
    def __init__(self):
        """Initialize authentication handler."""
        self.credential_manager = CredentialManager()
        self.credentials = {}
        self.session_valid_until = 0
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Log in to Daily.dev using stored credentials."""
        try:
            self.credentials = self.credential_manager.decrypt_credentials(password)
            
            if not self.credentials:
                print("No stored credentials found.")
                return False
            
            # Validate credential format
            if not self.credential_manager.validate_credentials_format(self.credentials):
                print("Invalid credential format found.")
                return False
            
            # Check if we have necessary authentication data
            if 'cookies' not in self.credentials or not self.credentials['cookies']:
                print("No authentication cookies found in credentials.")
                return False
            
            # Set session validity (24 hours by default)
            self.session_valid_until = time.time() + 86400
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return bool(self.credentials.get('cookies')) and time.time() < self.session_valid_until
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return self.credentials.get('headers', {})
    
    def get_auth_cookies(self) -> Dict[str, str]:
        """Get authentication cookies."""
        return self.credentials.get('cookies', {})
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get full authentication configuration."""
        return self.credentials
    
    def store_credentials(self, credentials: Dict[str, Any], password: Optional[str] = None) -> bool:
        """Store authentication credentials securely."""
        try:
            # Validate credentials before storing
            if not self.credential_manager.validate_credentials_format(credentials):
                print("Invalid credential format provided.")
                return False
            
            self.credential_manager.encrypt_credentials(credentials, password)
            self.credentials = credentials
            self.session_valid_until = time.time() + 86400
            return True
        except Exception as e:
            print(f"Failed to store credentials: {e}")
            return False
    
    def clear_credentials(self) -> None:
        """Clear stored credentials."""
        self.credential_manager.clear_credentials()
        self.credentials = {}
        self.session_valid_until = 0
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information and status."""
        return {
            "authenticated": self.is_authenticated(),
            "session_valid_until": self.session_valid_until,
            "time_remaining": max(0, self.session_valid_until - time.time()),
            "has_cookies": bool(self.credentials.get('cookies')),
            "has_headers": bool(self.credentials.get('headers')),
            "credential_timestamp": self.credentials.get('timestamp', 0)
        }


def create_auth_from_cookies(cookies: Dict[str, str], headers: Optional[Dict[str, str]] = None, 
                           password: Optional[str] = None) -> DailyDevAuth:
    """Create authenticated session from cookies."""
    auth = DailyDevAuth()
    
    credentials = {
        'cookies': cookies,
        'headers': headers or {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://app.daily.dev/'
        },
        'timestamp': time.time()
    }
    
    if auth.store_credentials(credentials, password):
        return auth
    else:
        return None


def get_auth_from_stored(password: Optional[str] = None) -> Optional[DailyDevAuth]:
    """Get authentication from stored credentials."""
    auth = DailyDevAuth()
    success = auth.login(password=password)
    return auth if success else None