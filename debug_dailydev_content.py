#!/usr/bin/env python3
"""
Debug Daily.dev Content

Check what content we're actually getting from Daily.dev.
"""

import requests
import json
from pathlib import Path


def debug_dailydev_content():
    """Debug what we get from Daily.dev."""
    
    # Load cookies
    cookie_file = Path('daily_dev_cookies.json')
    if not cookie_file.exists():
        print("❌ No cookies found")
        return
    
    with open(cookie_file, 'r') as f:
        cookie_data = json.load(f)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Add cookies
    cookies = cookie_data.get('cookies', {})
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.daily.dev')
    
    print("🔍 DEBUG: Daily.dev Content Analysis")
    print("=" * 50)
    print(f"Using {len(cookies)} cookies for authentication")
    
    # Test main page
    print("\n📡 Testing main page...")
    try:
        response = session.get("https://app.daily.dev/", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for authentication indicators
            auth_indicators = ['logout', 'profile', 'settings', 'sign out']
            found_auth = [indicator for indicator in auth_indicators if indicator in content.lower()]
            
            if found_auth:
                print(f"✅ Authentication indicators found: {found_auth}")
            else:
                print("⚠️  No clear authentication indicators")
            
            # Look for article-related content
            article_indicators = ['article', 'post', 'link', 'title', 'url']
            article_count = sum(content.lower().count(indicator) for indicator in article_indicators)
            print(f"📰 Article-related content count: {article_count}")
            
            # Look for JSON data
            import re
            json_patterns = [
                r'window\.__INITIAL_STATE__',
                r'window\.__PRELOADED_STATE__', 
                r'__NEXT_DATA__',
                r'"articles"',
                r'"posts"',
                r'"feed"'
            ]
            
            found_json = []
            for pattern in json_patterns:
                if re.search(pattern, content):
                    found_json.append(pattern)
            
            if found_json:
                print(f"✅ JSON data patterns found: {found_json}")
            else:
                print("❌ No JSON data patterns found")
            
            # Show first 1000 chars for analysis
            print(f"\n📄 First 1000 characters of content:")
            print("-" * 50)
            print(content[:1000])
            
            # Look for specific Daily.dev elements
            dailydev_elements = ['daily-dev', 'daily.dev', 'feed', 'trending']
            found_elements = [elem for elem in dailydev_elements if elem in content.lower()]
            
            if found_elements:
                print(f"\n✅ Daily.dev elements found: {found_elements}")
            else:
                print("\n❌ No Daily.dev specific elements found")
                
        else:
            print(f"❌ Failed to access Daily.dev: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("💡 ANALYSIS:")
    print("If you see minimal content or no JSON patterns,")
    print("it suggests Daily.dev is a single-page app that")
    print("loads content dynamically via JavaScript.")
    print("\nThis means we need to use their API endpoints")
    print("instead of scraping HTML content.")


if __name__ == "__main__":
    debug_dailydev_content()