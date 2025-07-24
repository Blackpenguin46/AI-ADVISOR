#!/usr/bin/env python3
"""
Secure Daily.dev Authentication Setup

This script helps you securely set up authentication for Daily.dev MCP integration.
It encrypts your credentials with a password and stores them securely.
"""

import json
import os
import sys
import getpass
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.dailydev_auth import DailyDevAuth, CredentialManager, create_auth_from_cookies


def print_header():
    """Print setup script header."""
    print("=" * 70)
    print("🔒 SECURE DAILY.DEV AUTHENTICATION SETUP")
    print("=" * 70)
    print("This script will help you securely set up authentication for Daily.dev MCP.")
    print("Your credentials will be encrypted with a password and stored locally.")
    print()


def print_browser_instructions():
    """Print detailed instructions for extracting cookies from different browsers."""
    print("📋 COOKIE EXTRACTION INSTRUCTIONS")
    print("=" * 50)
    print()
    print("You need to extract authentication cookies from your browser where you're")
    print("logged into Daily.dev. Follow the instructions for your browser:")
    print()
    
    print("🌐 CHROME / CHROMIUM:")
    print("1. Open https://app.daily.dev and make sure you're logged in")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to 'Application' tab")
    print("4. In the left sidebar, expand 'Storage' → 'Cookies'")
    print("5. Click on 'https://app.daily.dev'")
    print("6. Look for these important cookies and note their values:")
    print("   • da_sid (session ID)")
    print("   • da_auth (authentication token)")
    print("   • Any other cookies starting with 'da_' or containing 'auth'")
    print()
    
    print("🦊 FIREFOX:")
    print("1. Open https://app.daily.dev and make sure you're logged in")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to 'Storage' tab")
    print("4. Expand 'Cookies' in the left sidebar")
    print("5. Click on 'https://app.daily.dev'")
    print("6. Look for authentication cookies (same as Chrome)")
    print()
    
    print("🧭 SAFARI:")
    print("1. Enable Developer menu: Safari → Preferences → Advanced → Show Develop menu")
    print("2. Open https://app.daily.dev and make sure you're logged in")
    print("3. Develop → Show Web Inspector")
    print("4. Go to 'Storage' tab")
    print("5. Click on 'Cookies' → 'https://app.daily.dev'")
    print("6. Look for authentication cookies")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("• Only extract cookies from a browser where you're actively logged in")
    print("• Cookies are sensitive - treat them like passwords")
    print("• If you're unsure about a cookie, include it (we'll filter important ones)")
    print("• Session cookies may expire - you may need to repeat this process")
    print()


def extract_cookies_manually() -> Dict[str, str]:
    """Manually extract cookies from user input."""
    print("🍪 COOKIE INPUT")
    print("=" * 30)
    print("Please enter your Daily.dev cookies. You can:")
    print("1. Enter cookies one by one (recommended)")
    print("2. Paste all cookies at once (advanced)")
    print()
    
    method = input("Choose method (1 for one-by-one, 2 for paste-all): ").strip()
    
    if method == "2":
        return extract_cookies_bulk()
    else:
        return extract_cookies_individual()


def extract_cookies_individual() -> Dict[str, str]:
    """Extract cookies one by one."""
    print("\n📝 Enter cookies individually:")
    print("(Press Enter without a value to skip a cookie)")
    print()
    
    # Important cookies to look for
    important_cookies = [
        "da_sid",
        "da_auth", 
        "da_user_id",
        "__session",
        "session",
        "auth-token",
        "auth",
        "user-id",
        "uid"
    ]
    
    cookies = {}
    
    # Ask for important cookies first
    print("🔑 Important authentication cookies:")
    for cookie_name in important_cookies:
        value = input(f"  {cookie_name}: ").strip()
        if value:
            cookies[cookie_name] = value
    
    print("\n🔧 Additional cookies (optional):")
    print("Enter any other cookies you found (press Enter when done):")
    
    while True:
        name = input("  Cookie name (or Enter to finish): ").strip()
        if not name:
            break
        value = input(f"  Value for '{name}': ").strip()
        if value:
            cookies[name] = value
    
    return cookies


def extract_cookies_bulk() -> Dict[str, str]:
    """Extract cookies from bulk paste."""
    print("\n📋 Paste all cookies:")
    print("You can paste cookies in various formats:")
    print("• name1=value1; name2=value2; ...")
    print("• JSON format: {\"name1\": \"value1\", \"name2\": \"value2\"}")
    print("• One per line: name1=value1")
    print()
    
    print("Paste your cookies (press Enter twice when done):")
    lines = []
    while True:
        line = input().strip()
        if not line:
            break
        lines.append(line)
    
    cookie_text = " ".join(lines)
    cookies = {}
    
    try:
        # Try JSON format first
        if cookie_text.startswith('{'):
            cookies = json.loads(cookie_text)
        else:
            # Parse cookie string format
            if ';' in cookie_text:
                # Format: name1=value1; name2=value2
                for pair in cookie_text.split(';'):
                    if '=' in pair:
                        name, value = pair.split('=', 1)
                        cookies[name.strip()] = value.strip()
            else:
                # Format: name1=value1 (one per line or space separated)
                for pair in cookie_text.split():
                    if '=' in pair:
                        name, value = pair.split('=', 1)
                        cookies[name.strip()] = value.strip()
    
    except Exception as e:
        print(f"⚠️  Error parsing cookies: {e}")
        print("Please try the individual method instead.")
        return {}
    
    return cookies


def validate_cookies(cookies: Dict[str, str]) -> bool:
    """Validate that we have essential cookies."""
    if not cookies:
        print("❌ No cookies provided.")
        return False
    
    # Check for at least one authentication-related cookie
    auth_cookies = ['da_sid', 'da_auth', 'da_user_id', '__session', 'session', 'auth-token', 'auth']
    has_auth_cookie = any(cookie in cookies for cookie in auth_cookies)
    
    if not has_auth_cookie:
        print("⚠️  Warning: No obvious authentication cookies found.")
        print("Found cookies:", list(cookies.keys()))
        
        proceed = input("Do you want to proceed anyway? (y/n): ").lower().strip()
        return proceed == 'y'
    
    print(f"✅ Found {len(cookies)} cookies including authentication cookies.")
    return True


def test_authentication(auth: DailyDevAuth) -> bool:
    """Test if authentication works with Daily.dev."""
    print("\n🧪 Testing authentication...")
    
    try:
        import requests
        
        session = requests.Session()
        session.cookies.update(auth.get_auth_cookies())
        session.headers.update(auth.get_auth_headers())
        
        # Test with a simple GraphQL query
        test_query = """
        query TestAuth {
          feed(first: 1) {
            edges {
              node {
                id
                title
              }
            }
          }
        }
        """
        
        print("  • Connecting to Daily.dev API...")
        response = session.post(
            "https://app.daily.dev/api/graphql",
            json={"query": test_query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'feed' in data['data']:
                print("  ✅ Authentication successful! Connected to Daily.dev")
                return True
            else:
                print("  ⚠️  Authentication may not be working properly.")
                print("  Got response but data structure is unexpected.")
                return False
        else:
            print(f"  ❌ Authentication test failed. Status code: {response.status_code}")
            if response.status_code == 401:
                print("  This usually means your cookies have expired or are invalid.")
            elif response.status_code == 403:
                print("  This usually means access is forbidden - check your cookies.")
            return False
            
    except ImportError:
        print("  ⚠️  Cannot test authentication - requests library not installed")
        print("  Install with: pip install requests")
        print("  Assuming authentication is correct...")
        return True
    except Exception as e:
        print(f"  ❌ Authentication test failed: {e}")
        return False


def setup_secure_authentication():
    """Set up secure authentication for Daily.dev MCP."""
    print_header()
    
    # Check if credentials already exist
    credential_manager = CredentialManager()
    credentials_exist = credential_manager.credentials_exist()
    
    if credentials_exist:
        print("🔍 EXISTING CREDENTIALS DETECTED")
        print("=" * 40)
        
        cred_info = credential_manager.get_credentials_info()
        if 'created' in cred_info:
            print(f"📅 Created: {cred_info['created']}")
        if 'modified' in cred_info:
            print(f"📝 Modified: {cred_info['modified']}")
        
        print(f"📁 Location: {credential_manager.credentials_path}")
        print()
        
        print("What would you like to do?")
        print("  (u) Use existing credentials")
        print("  (r) Replace with new credentials")
        print("  (d) Delete existing credentials")
        print("  (t) Test existing credentials")
        
        action = input("Choose action [u/r/d/t]: ").lower().strip()
        
        if action == 'd':
            # Delete existing credentials
            credential_manager.clear_credentials()
            print("✅ Credentials deleted successfully")
            return
        
        elif action == 't':
            # Test existing credentials
            password = getpass.getpass("Enter password to decrypt credentials: ")
            auth = DailyDevAuth()
            if auth.login(password=password):
                print("✅ Credentials loaded successfully")
                if test_authentication(auth):
                    print("\n🎉 Authentication is working perfectly!")
                    print_usage_instructions()
                    return
                else:
                    print("\n⚠️  Credentials loaded but authentication test failed.")
                    print("Your cookies may have expired. Consider replacing them.")
            else:
                print("❌ Failed to load credentials. Wrong password?")
            return
        
        elif action == 'u':
            # Use existing credentials
            password = getpass.getpass("Enter password to decrypt credentials: ")
            auth = DailyDevAuth()
            if auth.login(password=password):
                print("✅ Credentials loaded successfully")
                if test_authentication(auth):
                    print("\n🎉 Authentication is working! You're ready to use Daily.dev MCP.")
                    print_usage_instructions()
                    return
                else:
                    print("\n⚠️  Authentication test failed. Consider replacing credentials.")
            else:
                print("❌ Failed to load credentials. Wrong password?")
                replace = input("Do you want to replace the credentials? [y/n]: ").lower()
                if replace != 'y':
                    return
        
        elif action != 'r':
            print("Invalid choice. Exiting.")
            return
    
    # Get cookies from user
    print_browser_instructions()
    cookies = extract_cookies_manually()
    
    if not validate_cookies(cookies):
        print("❌ Cannot proceed without valid cookies.")
        return
    
    # Create headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://app.daily.dev/',
        'Origin': 'https://app.daily.dev'
    }
    
    # Get encryption password
    print("\n🔐 ENCRYPTION SETUP")
    print("=" * 30)
    print("Create a strong password to encrypt your Daily.dev credentials.")
    print("This password will be required each time you use the MCP server.")
    print()
    
    while True:
        password = getpass.getpass("Create encryption password: ")
        if len(password) < 8:
            print("⚠️  Password should be at least 8 characters long.")
            continue
        
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Passwords do not match. Please try again.")
            continue
        
        break
    
    # Create authentication
    print("\n💾 Saving encrypted credentials...")
    auth = create_auth_from_cookies(cookies, headers, password)
    
    if not auth:
        print("❌ Failed to create authentication. Please try again.")
        return
    
    # Test authentication
    if test_authentication(auth):
        print("\n🎉 SETUP COMPLETE!")
        print("=" * 30)
        print("✅ Authentication setup successful!")
        print("✅ Credentials securely encrypted and stored")
        print("✅ Connection to Daily.dev verified")
        print()
        print(f"📁 Credentials stored at: {credential_manager.credentials_path}")
        print(f"🔑 Encryption key stored at: {credential_manager.key_path}")
        print()
        print_usage_instructions()
    else:
        print("\n⚠️  SETUP COMPLETED WITH WARNINGS")
        print("=" * 40)
        print("✅ Credentials have been encrypted and stored")
        print("⚠️  But the authentication test failed")
        print()
        print("This could mean:")
        print("• Your cookies have expired")
        print("• Network connectivity issues")
        print("• Daily.dev API is temporarily unavailable")
        print()
        print("You can try using the MCP server - it might still work.")
        print("If not, run this setup script again with fresh cookies.")
        print()
        print_usage_instructions()


def print_usage_instructions():
    """Print instructions for using the MCP server."""
    print("🚀 USAGE INSTRUCTIONS")
    print("=" * 30)
    print("Now you can use the Daily.dev MCP server in several ways:")
    print()
    print("1️⃣  MCP SERVER (Recommended):")
    print("   python src/integrations/dailydev_mcp.py")
    print("   Then connect your MCP client to use the tools")
    print()
    print("2️⃣  STANDALONE SCRAPER:")
    print("   python secure_dailydev_scraper.py")
    print("   Interactive menu for direct scraping")
    print()
    print("🛠️  AVAILABLE MCP TOOLS:")
    print("   • authenticate_dailydev - Authenticate with your password")
    print("   • sync_dailydev_articles - Sync articles from feeds")
    print("   • search_dailydev - Search and add articles")
    print("   • sync_bookmarks - Sync your bookmarks")
    print("   • get_dailydev_stats - View statistics")
    print("   • test_dailydev_connection - Test connection")
    print()
    print("🔐 AUTHENTICATION:")
    print("   Always authenticate first with:")
    print("   authenticate_dailydev(password='your-encryption-password')")
    print()
    print("📚 For more help, see the documentation or run with --help")


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Secure Daily.dev Authentication Setup")
        print()
        print("This script helps you set up secure authentication for Daily.dev MCP integration.")
        print("It will guide you through extracting cookies from your browser and encrypting them.")
        print()
        print("Usage:")
        print("  python secure_dailydev_setup.py")
        print()
        print("The script will:")
        print("1. Guide you through cookie extraction from your browser")
        print("2. Encrypt your credentials with a password")
        print("3. Test the authentication")
        print("4. Provide usage instructions")
        print()
        print("Your credentials are stored locally and never sent to third parties.")
        return
    
    try:
        setup_secure_authentication()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        print("Run the script again when you're ready to continue.")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        print("Please try running the script again.")
        print("If the problem persists, check your Python environment and dependencies.")


if __name__ == "__main__":
    main()