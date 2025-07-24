#!/usr/bin/env python3
"""
Secure GitHub Authentication for Daily.dev

This module securely handles GitHub OAuth to authenticate with Daily.dev,
then maintains the session for comprehensive scraping.
"""

import os
import json
import time
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import base64
from cryptography.fernet import Fernet


class SecureCredentialManager:
    """Secure storage for GitHub credentials using encryption."""
    
    def __init__(self, credentials_file: str = ".github_creds.enc"):
        self.credentials_file = Path(credentials_file)
        self.key_file = Path(".auth_key")
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Make key file readable only by owner
            os.chmod(self.key_file, 0o600)
            return key
    
    def store_credentials(self, github_username: str, github_password: str):
        """Securely store GitHub credentials."""
        key = self._get_or_create_key()
        fernet = Fernet(key)
        
        credentials = {
            'github_username': github_username,
            'github_password': github_password,
            'stored_at': datetime.now().isoformat()
        }
        
        encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
        
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)
        
        # Make credentials file readable only by owner
        os.chmod(self.credentials_file, 0o600)
        print("✅ GitHub credentials stored securely")
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load and decrypt GitHub credentials."""
        if not self.credentials_file.exists() or not self.key_file.exists():
            return None
        
        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            return credentials
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def credentials_exist(self) -> bool:
        """Check if credentials are stored."""
        return self.credentials_file.exists() and self.key_file.exists()


class GitHubDailyDevAuthenticator:
    """Authenticates with Daily.dev using GitHub OAuth."""
    
    def __init__(self):
        self.credential_manager = SecureCredentialManager()
        self.session = requests.Session()
        self.driver = None
        self.authenticated_session_file = Path("authenticated_dailydev_session.json")
        
    def setup_chrome_driver(self) -> webdriver.Chrome:
        """Set up Chrome driver for authentication."""
        print("🔧 Setting up Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # Remove headless for interactive login
        # chrome_options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return driver
    
    def setup_credentials(self):
        """Interactive setup of GitHub credentials."""
        print("🔐 SECURE GITHUB CREDENTIALS SETUP")
        print("=" * 50)
        print("Your GitHub credentials will be encrypted and stored locally.")
        print("They will only be used to authenticate with Daily.dev.")
        print()
        
        github_username = input("GitHub username/email: ").strip()
        github_password = getpass.getpass("GitHub password: ").strip()
        
        if not github_username or not github_password:
            print("❌ Both username and password are required")
            return False
        
        self.credential_manager.store_credentials(github_username, github_password)
        return True
    
    def authenticate_with_dailydev(self) -> bool:
        """Authenticate with Daily.dev using GitHub OAuth."""
        print("🔐 Authenticating with Daily.dev using GitHub...")
        
        # Load credentials
        credentials = self.credential_manager.load_credentials()
        if not credentials:
            print("❌ No stored credentials found. Run setup first.")
            return False
        
        try:
            # Set up Chrome driver
            self.driver = self.setup_chrome_driver()
            
            print("🌐 Opening Daily.dev login page...")
            self.driver.get("https://app.daily.dev/")
            
            # Wait for page to load and look for login button
            wait = WebDriverWait(self.driver, 20)
            
            try:
                # Look for login/sign-in button
                login_selectors = [
                    "button[data-testid='login-button']",
                    "a[href*='login']",
                    "button:contains('Sign in')",
                    ".login-button",
                    "[data-testid*='login']",
                    "button[aria-label*='login']"
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if not login_button:
                    # Try to find any button with login-related text
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if any(text in button.text.lower() for text in ['sign in', 'login', 'log in']):
                            login_button = button
                            break
                
                if login_button:
                    print("🖱️  Clicking login button...")
                    login_button.click()
                else:
                    print("⚠️  No login button found, proceeding to GitHub auth...")
                
            except Exception as e:
                print(f"⚠️  Login button detection issue: {e}")
            
            time.sleep(3)
            
            # Look for GitHub login option
            print("🔍 Looking for GitHub authentication option...")
            
            github_selectors = [
                "button[data-testid*='github']",
                "a[href*='github']",
                "button:contains('GitHub')",
                ".github-login",
                "[data-provider='github']"
            ]
            
            github_button = None
            for selector in github_selectors:
                try:
                    github_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            if not github_button:
                # Look for buttons/links containing "GitHub"
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'GitHub') or contains(text(), 'github')]")
                for element in elements:
                    if element.tag_name in ['button', 'a'] and element.is_enabled():
                        github_button = element
                        break
            
            if not github_button:
                print("❌ Could not find GitHub authentication option")
                print("🔍 Available elements on page:")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, button in enumerate(buttons[:10]):  # Show first 10 buttons
                    print(f"   Button {i+1}: '{button.text}' (classes: {button.get_attribute('class')})")
                return False
            
            print("🖱️  Clicking GitHub authentication...")
            github_button.click()
            
            # Wait for GitHub login page
            print("⏳ Waiting for GitHub login page...")
            wait.until(lambda driver: "github.com" in driver.current_url)
            
            print("📝 Entering GitHub credentials...")
            
            # Enter username
            username_field = wait.until(EC.presence_of_element_located((By.ID, "login_field")))
            username_field.clear()
            username_field.send_keys(credentials['github_username'])
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(credentials['github_password'])
            
            # Click sign in
            sign_in_button = self.driver.find_element(By.NAME, "commit")
            sign_in_button.click()
            
            print("🔐 Submitted GitHub credentials...")
            
            # Wait for redirect back to Daily.dev or handle 2FA
            time.sleep(5)
            
            # Check if we need to handle 2FA
            current_url = self.driver.current_url
            if "github.com" in current_url and ("two-factor" in current_url or "sessions/two-factor" in current_url):
                print("🔐 Two-factor authentication required!")
                print("Please complete 2FA in the browser window...")
                
                # Wait for user to complete 2FA (up to 2 minutes)
                for i in range(120):
                    time.sleep(1)
                    if "daily.dev" in self.driver.current_url:
                        break
                    if i % 10 == 0:
                        print(f"   Waiting for 2FA completion... ({120-i}s remaining)")
                
                if "github.com" in self.driver.current_url:
                    print("❌ 2FA not completed in time")
                    return False
            
            # Wait for redirect back to Daily.dev
            print("⏳ Waiting for redirect to Daily.dev...")
            for i in range(30):
                if "daily.dev" in self.driver.current_url:
                    break
                time.sleep(1)
            
            if "daily.dev" not in self.driver.current_url:
                print(f"❌ Not redirected to Daily.dev. Current URL: {self.driver.current_url}")
                return False
            
            print("✅ Successfully redirected to Daily.dev!")
            
            # Wait for page to fully load
            time.sleep(5)
            
            # Extract authentication cookies and session info
            print("🍪 Extracting authentication session...")
            cookies = self.driver.get_cookies()
            
            if not cookies:
                print("❌ No cookies found")
                return False
            
            # Save authenticated session
            session_data = {
                'cookies': {cookie['name']: cookie['value'] for cookie in cookies},
                'url': self.driver.current_url,
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'authenticated_at': datetime.now().isoformat(),
                'expires_estimate': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            with open(self.authenticated_session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"✅ Authentication successful! Saved {len(cookies)} cookies")
            print(f"💾 Session saved to {self.authenticated_session_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def load_authenticated_session(self) -> Optional[Dict[str, Any]]:
        """Load previously authenticated session."""
        if not self.authenticated_session_file.exists():
            return None
        
        try:
            with open(self.authenticated_session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is still valid
            expires_at = datetime.fromisoformat(session_data['expires_estimate'])
            if datetime.now() > expires_at:
                print("⏰ Stored session has expired")
                return None
            
            return session_data
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid authenticated session."""
        session = self.load_authenticated_session()
        return session is not None


def main():
    """Main function to set up GitHub authentication for Daily.dev."""
    print("🚀 SECURE GITHUB → DAILY.DEV AUTHENTICATION SETUP")
    print("=" * 60)
    print("This will securely authenticate your GitHub account with Daily.dev")
    print("to enable comprehensive scraping of your personalized content.")
    print()
    
    authenticator = GitHubDailyDevAuthenticator()
    
    # Check if already authenticated
    if authenticator.is_authenticated():
        print("✅ You already have a valid Daily.dev session!")
        session = authenticator.load_authenticated_session()
        print(f"   Authenticated at: {session['authenticated_at']}")
        print(f"   Expires around: {session['expires_estimate']}")
        
        choice = input("\nDo you want to re-authenticate? (y/N): ").strip().lower()
        if choice != 'y':
            print("👍 Using existing session. You can now run the comprehensive scraper!")
            return
    
    # Set up credentials if needed
    if not authenticator.credential_manager.credentials_exist():
        print("🔐 First time setup - storing your GitHub credentials securely...")
        if not authenticator.setup_credentials():
            print("❌ Credential setup failed")
            return
    else:
        print("🔐 Using stored GitHub credentials...")
    
    # Authenticate
    if authenticator.authenticate_with_dailydev():
        print("\n🎉 SUCCESS! GitHub authentication complete!")
        print("✅ You can now run comprehensive Daily.dev scraping")
        print("\nNext steps:")
        print("   python comprehensive_dailydev_scraper.py --target 5000")
    else:
        print("\n❌ Authentication failed!")
        print("Please check your GitHub credentials and try again.")


if __name__ == "__main__":
    main()