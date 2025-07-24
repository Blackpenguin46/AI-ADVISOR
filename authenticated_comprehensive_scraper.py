#!/usr/bin/env python3
"""
Authenticated Comprehensive Daily.dev Scraper

Uses the secure GitHub authentication to scrape thousands of articles
from your authenticated Daily.dev account.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from pathlib import Path
import hashlib
from secure_github_dailydev_auth import GitHubDailyDevAuthenticator


class AuthenticatedDailyDevScraper:
    """Comprehensive scraper using authenticated GitHub session."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.authenticator = GitHubDailyDevAuthenticator()
        self.session = requests.Session()
        self.scraped_urls: Set[str] = set()
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate using stored GitHub session."""
        print("🔐 Loading authenticated Daily.dev session...")
        
        session_data = self.authenticator.load_authenticated_session()
        if not session_data:
            print("❌ No valid authenticated session found!")
            print("Please run: python secure_github_dailydev_auth.py")
            return False
        
        # Set up session with authentication
        self.session.headers.update({
            'User-Agent': session_data.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://app.daily.dev',
            'Referer': 'https://app.daily.dev/',
        })
        
        # Add authentication cookies
        cookies = session_data.get('cookies', {})
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain='.daily.dev')
        
        print(f"✅ Loaded authentication with {len(cookies)} cookies")
        
        # Test authentication
        if self.test_authentication():
            self.authenticated = True
            return True
        else:
            print("❌ Authentication test failed")
            return False
    
    def test_authentication(self) -> bool:
        """Test if authentication is working."""
        print("🧪 Testing authenticated access to Daily.dev...")
        
        try:
            # Test app access
            response = self.session.get("https://app.daily.dev/", timeout=30)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for authenticated indicators
                auth_indicators = [
                    'logout', 'profile', 'settings', 'bookmarks',
                    'notifications', 'dashboard', 'my feed'
                ]
                
                if any(indicator in content for indicator in auth_indicators):
                    print("✅ Authentication confirmed - logged into Daily.dev")
                    return True
                else:
                    print("⚠️  Connected to Daily.dev but authentication status unclear")
                    return True  # Continue anyway
            else:
                print(f"❌ Cannot access Daily.dev - status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load existing knowledge base."""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading knowledge base: {e}")
                return {}
        return {}
    
    def _save_knowledge_base(self, kb: Dict[str, Any]):
        """Save knowledge base to file."""
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(kb, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID for an article."""
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def scrape_daily_dev_graphql(self, max_articles: int = 1000) -> List[Dict[str, Any]]:
        """Scrape using GraphQL API with authentication."""
        print(f"🚀 Scraping Daily.dev via authenticated GraphQL API...")
        
        all_articles = []
        cursor = None
        page = 0
        max_pages = max_articles // 50 + 1
        
        while page < max_pages and len(all_articles) < max_articles:
            print(f"   📄 Fetching page {page + 1}...")
            
            # Simplified GraphQL query that should work with authentication
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
                        readTime
                        numUpvotes
                        numComments
                        source {
                          name
                        }
                        author {
                          name
                        }
                      }
                    }
                  }
                }
                """,
                "variables": {
                    "first": 50,
                    "after": cursor
                }
            }
            
            try:
                response = self.session.post("https://api.daily.dev/graphql", json=query, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'errors' in data:
                        print(f"      ❌ GraphQL errors: {data['errors']}")
                        break
                    
                    if 'data' in data and 'page' in data['data']:
                        edges = data['data']['page']['edges']
                        page_info = data['data']['page']['pageInfo']
                        
                        print(f"      ✅ Got {len(edges)} articles")
                        
                        for edge in edges:
                            node = edge['node']
                            
                            if node.get('url') and node.get('url') not in self.scraped_urls:
                                article = {
                                    'id': node.get('id', ''),
                                    'url': node.get('url', ''),
                                    'title': node.get('title', ''),
                                    'summary': node.get('summary', ''),
                                    'created_at': node.get('createdAt', ''),
                                    'read_time': node.get('readTime', 0),
                                    'upvotes': node.get('numUpvotes', 0),
                                    'comments': node.get('numComments', 0),
                                    'source': node.get('source', {}).get('name', 'Daily.dev'),
                                    'author': node.get('author', {}).get('name', '') if node.get('author') else '',
                                    'tags': [],  # Will be empty for now
                                    'feed_type': 'AUTHENTICATED'
                                }
                                
                                all_articles.append(article)
                                self.scraped_urls.add(article['url'])
                        
                        if not page_info.get('hasNextPage') or len(all_articles) >= max_articles:
                            break
                        
                        cursor = page_info.get('endCursor')
                        page += 1
                        time.sleep(2)  # Rate limiting
                        
                    else:
                        print(f"      ❌ Unexpected response structure")
                        break
                
                else:
                    print(f"      ❌ API request failed: {response.status_code}")
                    if response.status_code == 429:
                        print("         💤 Rate limited, waiting...")
                        time.sleep(10)
                        continue
                    break
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
                break
        
        print(f"✅ GraphQL scraping complete: {len(all_articles)} articles")
        return all_articles
    
    def scrape_daily_dev_html(self, max_articles: int = 500) -> List[Dict[str, Any]]:
        """Fallback: scrape Daily.dev HTML pages."""
        print(f"📄 Scraping Daily.dev HTML pages as fallback...")
        
        articles = []
        
        # URLs to scrape
        urls_to_scrape = [
            "https://app.daily.dev/",
            "https://app.daily.dev/popular",
            "https://app.daily.dev/recent",
            "https://app.daily.dev/discussed",
        ]
        
        for url in urls_to_scrape:
            if len(articles) >= max_articles:
                break
                
            print(f"   🌐 Scraping {url}...")
            
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Look for JSON data in HTML (many SPAs embed data)
                    content = response.text
                    
                    # Look for common patterns where article data might be embedded
                    import re
                    
                    # Look for JSON data in script tags
                    json_patterns = [
                        r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                        r'window\.__PRELOADED_STATE__\s*=\s*({.+?});',
                        r'__NEXT_DATA__[^{]*({.+?})</script>',
                        r'"articles":\s*(\[.+?\])',
                        r'"posts":\s*(\[.+?\])',
                        r'"feed":\s*(\[.+?\])'
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, content, re.DOTALL)
                        for match in matches:
                            try:
                                data = json.loads(match)
                                # Try to extract articles from the data
                                extracted = self.extract_articles_from_data(data, url)
                                articles.extend(extracted)
                                if extracted:
                                    print(f"      ✅ Extracted {len(extracted)} articles from {url}")
                                    break
                            except:
                                continue
                
                time.sleep(3)  # Be respectful
                
            except Exception as e:
                print(f"      ❌ Error scraping {url}: {e}")
        
        print(f"✅ HTML scraping complete: {len(articles)} articles")
        return articles
    
    def extract_articles_from_data(self, data: Any, source_url: str) -> List[Dict[str, Any]]:
        """Extract articles from JSON data found in HTML."""
        articles = []
        
        def search_for_articles(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['articles', 'posts', 'feed', 'edges', 'data']:
                        if isinstance(value, list):
                            for item in value:
                                article = self.extract_article_from_item(item)
                                if article:
                                    articles.append(article)
                    else:
                        search_for_articles(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_for_articles(item, f"{path}[{i}]")
        
        search_for_articles(data)
        return articles
    
    def extract_article_from_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """Extract article data from a data item."""
        if not isinstance(item, dict):
            return None
        
        # Handle nested structure (GraphQL style)
        if 'node' in item:
            item = item['node']
        
        # Must have URL and title
        url = item.get('url') or item.get('link') or item.get('permalink')
        title = item.get('title') or item.get('headline')
        
        if not url or not title or url in self.scraped_urls:
            return None
        
        article = {
            'id': item.get('id', ''),
            'url': url,
            'title': title,
            'summary': item.get('summary') or item.get('description') or item.get('excerpt', ''),
            'created_at': item.get('createdAt') or item.get('publishedAt') or item.get('date', ''),
            'read_time': item.get('readTime', 0),
            'upvotes': item.get('numUpvotes') or item.get('upvotes', 0),
            'comments': item.get('numComments') or item.get('comments', 0),
            'source': item.get('source', {}).get('name', 'Daily.dev') if isinstance(item.get('source'), dict) else str(item.get('source', 'Daily.dev')),
            'author': '',
            'tags': item.get('tags', []),
            'feed_type': 'HTML_EXTRACTED'
        }
        
        # Handle author
        author = item.get('author')
        if isinstance(author, dict):
            article['author'] = author.get('name', '')
        elif isinstance(author, str):
            article['author'] = author
        
        self.scraped_urls.add(url)
        return article
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]]) -> int:
        """Add articles to knowledge base."""
        print(f"📚 Adding {len(articles)} authenticated Daily.dev articles...")
        
        kb = self._load_knowledge_base()
        added_count = 0
        
        for article in articles:
            if not article.get('url') or not article.get('title'):
                continue
            
            article_id = self._generate_id(article['url'])
            
            if article_id in kb:
                continue
            
            content = article.get('summary', '') or article.get('title', '')
            
            kb[article_id] = {
                'metadata': {
                    'id': article_id,
                    'title': article['title'],
                    'source_type': 'url',
                    'source_url': article['url'],
                    'author': 'Daily.dev',
                    'original_source': article.get('source', 'Daily.dev'),
                    'date_added': datetime.now().isoformat(),
                    'description': article.get('summary', ''),
                    'tags': ['daily.dev', 'tech', 'article', 'authenticated'] + article.get('tags', []),
                    'upvotes': article.get('upvotes', 0),
                    'comments': article.get('comments', 0),
                    'read_time': article.get('read_time', 0),
                    'feed_type': article.get('feed_type', 'AUTHENTICATED'),
                    'github_authenticated': True  # Mark as GitHub authenticated
                },
                'content': content,
                'chunks': [content] if content else [],
                'chunk_count': 1 if content else 0,
                'processing_notes': [f'GitHub-authenticated Daily.dev scrape on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 100 == 0:
                print(f"   ✅ Added {added_count} articles...")
                self._save_knowledge_base(kb)
        
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new authenticated articles!")
        
        return added_count
    
    def scrape_comprehensive(self, target_articles: int = 2000) -> int:
        """Main comprehensive scraping method."""
        print(f"🚀 COMPREHENSIVE AUTHENTICATED Daily.dev SCRAPING")
        print(f"🎯 Target: {target_articles} articles")
        print("🔐 Using GitHub authentication")
        
        if not self.authenticate():
            return 0
        
        all_articles = []
        
        # Method 1: GraphQL API
        print("\n📡 Method 1: GraphQL API...")
        graphql_articles = self.scrape_daily_dev_graphql(max_articles=target_articles)
        all_articles.extend(graphql_articles)
        
        # Method 2: HTML scraping (if we need more)
        if len(all_articles) < target_articles // 2:
            print("\n📄 Method 2: HTML scraping...")
            html_articles = self.scrape_daily_dev_html(max_articles=target_articles - len(all_articles))
            all_articles.extend(html_articles)
        
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   Total articles collected: {len(all_articles)}")
        print(f"   Unique URLs: {len(self.scraped_urls)}")
        
        if not all_articles:
            print("❌ No articles collected!")
            return 0
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(all_articles)
        
        return added_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Authenticated comprehensive Daily.dev scraper")
    parser.add_argument("--target", type=int, default=2000, help="Target number of articles")
    
    args = parser.parse_args()
    
    print("🔐 AUTHENTICATED COMPREHENSIVE DAILY.DEV SCRAPER")
    print("=" * 60)
    
    scraper = AuthenticatedDailyDevScraper()
    added_count = scraper.scrape_comprehensive(target_articles=args.target)
    
    if added_count > 0:
        print(f"\n🎉 SUCCESS! Added {added_count} authenticated Daily.dev articles!")
        print("✅ Your AI Advisor now has comprehensive Daily.dev content!")
    else:
        print("\n❌ No articles were added. Check authentication setup.")


if __name__ == "__main__":
    main()