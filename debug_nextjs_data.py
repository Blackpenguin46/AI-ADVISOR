#!/usr/bin/env python3
"""
Debug Next.js Data Structure

Examine the __NEXT_DATA__ content from Daily.dev to understand
why we're not finding articles.
"""

import requests
import json
import re
from pathlib import Path


def debug_nextjs_data():
    """Debug Next.js data structure from Daily.dev."""
    
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
    
    print("🔍 DEBUG: Next.js Data Structure Analysis")
    print("=" * 60)
    
    # Test main page
    print("\n📡 Fetching Daily.dev main page...")
    try:
        response = session.get("https://app.daily.dev/", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Extract __NEXT_DATA__
            next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">({.+?})</script>'
            matches = re.findall(next_data_pattern, content, re.DOTALL)
            
            if matches:
                print(f"✅ Found __NEXT_DATA__ ({len(matches[0])} characters)")
                
                try:
                    next_data = json.loads(matches[0])
                    print("\n📊 Next.js Data Structure:")
                    print("-" * 40)
                    
                    # Pretty print the structure with limited depth
                    def print_structure(obj, indent=0, max_depth=3):
                        if indent > max_depth:
                            return
                        
                        prefix = "  " * indent
                        
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if isinstance(value, dict):
                                    print(f"{prefix}{key}: {{}} ({len(value)} keys)")
                                    if indent < max_depth:
                                        print_structure(value, indent + 1, max_depth)
                                elif isinstance(value, list):
                                    print(f"{prefix}{key}: [] ({len(value)} items)")
                                    if value and indent < max_depth:
                                        print(f"{prefix}  Sample item:")
                                        print_structure(value[0], indent + 2, max_depth)
                                else:
                                    value_str = str(value)[:50]
                                    if len(str(value)) > 50:
                                        value_str += "..."
                                    print(f"{prefix}{key}: {type(value).__name__} = {value_str}")
                        elif isinstance(obj, list):
                            print(f"{prefix}List with {len(obj)} items")
                            if obj:
                                print(f"{prefix}Sample item:")
                                print_structure(obj[0], indent + 1, max_depth)
                    
                    print_structure(next_data)
                    
                    # Look specifically for potential article data
                    print("\n🔍 Searching for article-like data...")
                    def search_for_articles(obj, path=""):
                        found = []
                        
                        if isinstance(obj, dict):
                            # Check if this looks like an article
                            if ('url' in obj or 'link' in obj) and ('title' in obj or 'headline' in obj):
                                found.append(f"{path}: Article-like object with keys: {list(obj.keys())}")
                            
                            for key, value in obj.items():
                                if isinstance(value, (dict, list)):
                                    found.extend(search_for_articles(value, f"{path}.{key}" if path else key))
                        
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                if isinstance(item, (dict, list)):
                                    found.extend(search_for_articles(item, f"{path}[{i}]" if path else f"[{i}]"))
                        
                        return found
                    
                    article_like = search_for_articles(next_data)
                    
                    if article_like:
                        print("✅ Found potential article data:")
                        for item in article_like:
                            print(f"   {item}")
                    else:
                        print("❌ No article-like data found in Next.js structure")
                    
                    # Save the data for further analysis
                    with open('nextjs_data_sample.json', 'w') as f:
                        json.dump(next_data, f, indent=2)
                    print(f"\n💾 Saved full Next.js data to nextjs_data_sample.json")
                    
                except Exception as e:
                    print(f"❌ Error parsing Next.js data: {e}")
                    print("Raw data sample:")
                    print(matches[0][:500] + "..." if len(matches[0]) > 500 else matches[0])
            else:
                print("❌ No __NEXT_DATA__ found")
                
        else:
            print(f"❌ Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("💡 ANALYSIS COMPLETE")
    print("Check nextjs_data_sample.json for the full data structure")


if __name__ == "__main__":
    debug_nextjs_data()