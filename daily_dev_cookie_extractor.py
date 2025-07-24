#!/usr/bin/env python3
"""
Daily.dev Cookie Extractor

This script helps extract cookies from your browser for Daily.dev authentication.
Run this script and follow the instructions to get your cookies for the MCP integration.
"""

import json
import os
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import platform


def get_chrome_cookies_path() -> Optional[Path]:
    """Get the path to Chrome's cookies database based on the operating system."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies"
    elif system == "Windows":
        return Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cookies"
    elif system == "Linux":
        return Path.home() / ".config/google-chrome/Default/Cookies"
    else:
        return None


def extract_cookies_from_chrome(domain: str = "daily.dev") -> Dict[str, str]:
    """Extract cookies for a specific domain from Chrome's cookie database."""
    cookies_path = get_chrome_cookies_path()
    
    if not cookies_path or not cookies_path.exists():
        print(f"Chrome cookies database not found at: {cookies_path}")
        return {}
    
    # Create a temporary copy of the cookies database
    temp_cookies_path = cookies_path.parent / "cookies_temp.db"
    try:
        shutil.copy2(cookies_path, temp_cookies_path)
        
        # Connect to the database
        conn = sqlite3.connect(temp_cookies_path)
        cursor = conn.cursor()
        
        # Query cookies for the domain
        query = """
        SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
        FROM cookies 
        WHERE host_key LIKE ?
        """
        
        cursor.execute(query, (f"%{domain}%",))
        rows = cursor.fetchall()
        
        cookies = {}
        for row in rows:
            name, value, host_key, path, expires_utc, is_secure, is_httponly = row
            cookies[name] = value
        
        conn.close()
        return cookies
        
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return {}
    finally:
        # Clean up temporary file
        if temp_cookies_path.exists():
            temp_cookies_path.unlink()


def manual_cookie_input() -> Dict[str, str]:
    """Manually input cookies from user."""
    print("\n" + "="*60)
    print("MANUAL COOKIE INPUT")
    print("="*60)
    print("Please extract cookies manually from your browser:")
    print("1. Open https://app.daily.dev in Chrome")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to Application tab → Storage → Cookies → https://app.daily.dev")
    print("4. Look for these important cookies and enter their values:")
    print()
    
    important_cookies = [
        "__session",
        "session", 
        "auth-token",
        "auth",
        "user-id",
        "uid",
        "_dd_s",
        "dd_user_id"
    ]
    
    cookies = {}
    
    for cookie_name in important_cookies:
        value = input(f"Enter value for '{cookie_name}' (or press Enter to skip): ").strip()
        if value:
            cookies[cookie_name] = value
    
    # Allow user to add additional cookies
    print("\nAdd any additional cookies (press Enter when done):")
    while True:
        name = input("Cookie name (or Enter to finish): ").strip()
        if not name:
            break
        value = input(f"Value for '{name}': ").strip()
        if value:
            cookies[name] = value
    
    return cookies


def save_cookies_config(cookies: Dict[str, str], filename: str = "dailydev_cookies.json"):
    """Save cookies to a configuration file."""
    config = {
        "cookies": cookies,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://app.daily.dev/"
        },
        "sync_interval_hours": 24,
        "max_articles_per_sync": 100
    }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nConfiguration saved to: {filename}")


def test_cookies(cookies: Dict[str, str]) -> bool:
    """Test if the extracted cookies work with Daily.dev."""
    try:
        import requests
        
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://app.daily.dev/'
        })
        
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
        
        response = session.post(
            "https://app.daily.dev/api/graphql",
            json={"query": test_query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'feed' in data['data']:
                print("✅ Cookies are working! Successfully authenticated with Daily.dev")
                return True
            else:
                print("⚠️  Cookies may not be working properly. Got unexpected response.")
                return False
        else:
            print(f"❌ Cookie test failed. Status code: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  Cannot test cookies - requests library not installed")
        print("Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Cookie test failed: {e}")
        return False


def main():
    """Main function to extract and configure Daily.dev cookies."""
    print("Daily.dev Cookie Extractor")
    print("=" * 50)
    print("This script will help you extract cookies for Daily.dev MCP integration.")
    print()
    
    # Try automatic extraction first
    print("Attempting to extract cookies from Chrome...")
    cookies = extract_cookies_from_chrome("daily.dev")
    
    if cookies:
        print(f"✅ Found {len(cookies)} cookies from Chrome!")
        print("Cookies found:", list(cookies.keys()))
        
        # Test the cookies
        if test_cookies(cookies):
            save_cookies_config(cookies)
            print("\n🎉 Setup complete! You can now use the Daily.dev MCP integration.")
            print("\nNext steps:")
            print("1. Load the configuration in your AI Advisor")
            print("2. Initialize the Daily.dev MCP with the saved config")
            print("3. Start syncing articles to your knowledge base!")
            return
        else:
            print("❌ Automatic cookie extraction didn't work properly.")
    else:
        print("❌ Could not automatically extract cookies from Chrome.")
    
    # Fall back to manual input
    print("\nFalling back to manual cookie input...")
    manual_cookies = manual_cookie_input()
    
    if manual_cookies:
        print(f"\n✅ Manually entered {len(manual_cookies)} cookies")
        
        # Test manual cookies
        if test_cookies(manual_cookies):
            save_cookies_config(manual_cookies)
            print("\n🎉 Setup complete! You can now use the Daily.dev MCP integration.")
        else:
            print("⚠️  Manual cookies may not be working properly, but config saved anyway.")
            save_cookies_config(manual_cookies)
    else:
        print("❌ No cookies provided. Cannot proceed with setup.")
        print("\nPlease try again and make sure to:")
        print("1. Be logged into Daily.dev in your browser")
        print("2. Extract cookies from the correct domain (app.daily.dev)")
        print("3. Copy the complete cookie values")


if __name__ == "__main__":
    main()