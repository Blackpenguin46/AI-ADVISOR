#!/usr/bin/env python3
"""
Debug Daily.dev API Endpoints
"""

import requests
import json
from pathlib import Path

def debug_dailydev_api():
    """Debug Daily.dev API endpoints."""
    
    # Load cookies
    cookie_file = Path('daily_dev_cookies.json')
    if not cookie_file.exists():
        print("❌ No cookies found")
        return False
    
    with open(cookie_file, 'r') as f:
        cookie_data = json.load(f)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://app.daily.dev',
        'Referer': 'https://app.daily.dev/',
    })
    
    # Add cookies
    cookies = cookie_data.get('cookies', {})
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.daily.dev')
    
    print("🔍 DEBUG: Daily.dev API Analysis")
    print("=" * 50)
    print(f"Using {len(cookies)} cookies")
    
    # Test GraphQL API
    print("\n📡 Testing GraphQL API...")
    graphql_url = "https://api.daily.dev/graphql"
    
    query = {
        "query": """
        query AnonymousFeed($first: Int, $after: String) {
          page: anonymousFeed(first: $first, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                url
                title
                summary
                createdAt
                source {
                  name
                }
              }
            }
          }
        }
        """,
        "variables": {"first": 10, "after": None}
    }
    
    try:
        response = session.post(graphql_url, json=query, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ Errors: {data['errors']}")
                return False
            
            if 'data' in data and 'page' in data['data']:
                edges = data['data']['page']['edges']
                print(f"✅ Success: Got {len(edges)} articles")
                
                if edges:
                    sample = edges[0]['node']
                    print("📄 Sample:")
                    print(f"   Title: {sample.get('title', 'N/A')}")
                    print(f"   URL: {sample.get('url', 'N/A')}")
                    print(f"   Source: {sample.get('source', {}).get('name', 'N/A')}")
                
                return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    debug_dailydev_api()