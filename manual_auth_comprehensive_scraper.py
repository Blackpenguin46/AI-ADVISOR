#!/usr/bin/env python3
"""
Manual Authentication Comprehensive Daily.dev Scraper

This approach uses manually extracted cookies to perform comprehensive scraping.
No browser automation required - just copy/paste your cookies once.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
import hashlib
import re


class ManualAuthDailyDevScraper:
    """Comprehensive scraper using manually provided authentication."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.session = requests.Session()
        self.scraped_urls: Set[str] = set()
        self.authenticated = False
        
    def setup_manual_authentication(self):
        """Guide user through manual cookie extraction."""
        print("🔐 MANUAL DAILY.DEV AUTHENTICATION SETUP")
        print("=" * 60)
        print("Since Chrome automation isn't available, we'll use manual cookie extraction.")
        print()
        print("STEP 1: Open Daily.dev in your browser")
        print("=" * 40)
        print("1. Open https://app.daily.dev in your browser")
        print("2. Sign in with your GitHub account")
        print("3. Make sure you're fully logged in")
        print()
        print("STEP 2: Extract authentication cookies")
        print("=" * 40)
        print("1. Press F12 to open Developer Tools")
        print("2. Go to Application tab → Storage → Cookies → https://app.daily.dev")
        print("3. Look for these important cookies:")
        print("   • da2, da3, ory_kratos_session")
        print("   • Any cookies with 'auth', 'session', or 'token' in the name")
        print()
        
        cookies = {}
        
        print("STEP 3: Enter your cookies")
        print("=" * 40)
        print("Copy and paste the cookie values below:")
        print("(Press Enter to skip any cookie you don't have)")
        print()
        
        # Essential cookies for Daily.dev
        cookie_names = [
            'da2', 'da3', 'ory_kratos_session', '_cfuvid', 'das', 
            'session', 'auth_token', 'access_token', 'jwt'
        ]
        
        for cookie_name in cookie_names:
            try:
                value = input(f"Enter value for '{cookie_name}' (or press Enter to skip): ").strip()
                if value:
                    cookies[cookie_name] = value
                    print(f"  ✅ Added {cookie_name}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n⚠️  Skipping {cookie_name}")
                continue
        
        if not cookies:
            print("❌ No cookies provided. Cannot proceed with authentication.")
            return False
        
        # Save cookies
        cookie_data = {
            'cookies': cookies,
            'extracted_at': datetime.now().isoformat(),
            'expires_estimate': (datetime.now() + timedelta(hours=24)).isoformat(),
            'manual_extraction': True
        }
        
        with open('manual_dailydev_cookies.json', 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        print(f"\n✅ Saved {len(cookies)} cookies for authentication")
        return True
        
    def load_authentication(self) -> bool:
        """Load authentication cookies."""
        cookie_files = ['manual_dailydev_cookies.json', 'daily_dev_cookies.json']
        
        for cookie_file in cookie_files:
            if Path(cookie_file).exists():
                print(f"🔍 Loading cookies from {cookie_file}...")
                
                try:
                    with open(cookie_file, 'r') as f:
                        cookie_data = json.load(f)
                    
                    cookies = cookie_data.get('cookies', {})
                    
                    if not cookies:
                        continue
                    
                    # Set up session headers
                    self.session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    })
                    
                    # Add cookies
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value, domain='.daily.dev')
                    
                    print(f"✅ Loaded {len(cookies)} authentication cookies")
                    
                    # Test authentication
                    if self.test_authentication():
                        self.authenticated = True
                        return True
                    
                except Exception as e:
                    print(f"❌ Error loading {cookie_file}: {e}")
                    continue
        
        print("❌ No valid authentication found")
        return False
    
    def test_authentication(self) -> bool:
        """Test if authentication is working."""
        print("🧪 Testing Daily.dev authentication...")
        
        try:
            # Test main page access
            response = self.session.get("https://app.daily.dev/", timeout=30)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for authenticated indicators
                auth_indicators = [
                    'logout', 'profile', 'settings', 'bookmarks',
                    'notifications', 'dashboard', 'sign out'
                ]
                
                authenticated = any(indicator in content for indicator in auth_indicators)
                
                if authenticated:
                    print("✅ Authentication confirmed - logged into Daily.dev")
                    return True
                else:
                    print("⚠️  Connected to Daily.dev but authentication unclear")
                    # Still try scraping - might work
                    return True
            
            else:
                print(f"❌ Cannot access Daily.dev - status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    def scrape_daily_dev_graphql(self, max_articles: int = 3000) -> List[Dict[str, Any]]:
        """Scrape Daily.dev using GraphQL API - the correct approach."""
        print(f"🚀 Scraping Daily.dev via GraphQL API for up to {max_articles} articles...")
        
        all_articles = []
        cursor = None
        page = 0
        max_pages = max_articles // 50 + 1
        
        # Update session headers for GraphQL
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://app.daily.dev',
            'Referer': 'https://app.daily.dev/',
        })
        
        while page < max_pages and len(all_articles) < max_articles:
            print(f"   📄 Fetching page {page + 1}...")
            
            # GraphQL query that works with authentication
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
                                    'tags': [],
                                    'feed_type': 'GRAPHQL_API'
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
                        print(f"         💤 Rate limited, waiting...")
                        time.sleep(10)
                        continue
                    break
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
                break
        
        print(f"✅ GraphQL scraping complete: found {len(all_articles)} unique articles")
        return all_articles
    
    def extract_articles_from_html(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract article data from HTML content."""
        articles = []
        
        # Look for __NEXT_DATA__ specifically (this is what Daily.dev uses)
        print(f"      🔍 Looking for Next.js data in HTML...")
        
        # More precise Next.js data extraction
        next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">({.+?})</script>'
        matches = re.findall(next_data_pattern, html, re.DOTALL)
        
        for match in matches:
            try:
                print(f"         📦 Found __NEXT_DATA__ block ({len(match)} chars)")
                data = json.loads(match)
                extracted = self.extract_articles_from_next_data(data)
                articles.extend(extracted)
                if extracted:
                    print(f"         ✅ Extracted {len(extracted)} articles from Next.js data")
                    break
            except Exception as e:
                print(f"         ❌ Error parsing Next.js data: {e}")
                continue
        
        # Fallback: Look for other JSON patterns
        if not articles:
            print(f"      🔍 Trying other JSON patterns...")
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__PRELOADED_STATE__\s*=\s*({.+?});',
                r'"articles":\s*(\[.+?\])',
                r'"posts":\s*(\[.+?\])', 
                r'"feed":\s*(\[.+?\])',
                r'"data":\s*{[^}]*"feed":\s*{[^}]*"edges":\s*(\[.+?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        extracted = self.extract_articles_from_data(data)
                        articles.extend(extracted)
                        if extracted:
                            print(f"         ✅ Extracted {len(extracted)} articles from JSON pattern")
                            break
                    except:
                        continue
                if articles:
                    break
        
        # Last resort: extract from HTML structure directly
        if not articles:
            print(f"      🔍 Trying DOM extraction...")
            articles = self.extract_articles_from_dom(html)
            if articles:
                print(f"         ✅ Extracted {len(articles)} articles from DOM")
        
        return articles
    
    def extract_articles_from_next_data(self, next_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract articles from Next.js __NEXT_DATA__ structure."""
        articles = []
        
        # Next.js data structure is usually: { props: { pageProps: { ... } } }
        try:
            # Look for common Next.js data paths
            data_paths = [
                ['props', 'pageProps', 'feed', 'edges'],
                ['props', 'pageProps', 'data', 'feed', 'edges'], 
                ['props', 'pageProps', 'articles'],
                ['props', 'pageProps', 'posts'],
                ['props', 'pageProps', 'initialData', 'feed', 'edges'],
                ['props', 'pageProps', 'dehydratedState', 'queries'],
                ['query', 'data', 'feed', 'edges']
            ]
            
            for path in data_paths:
                current = next_data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                
                if current and isinstance(current, list):
                    print(f"         📊 Found data at path: {' → '.join(path)} ({len(current)} items)")
                    
                    for item in current:
                        if isinstance(item, dict):
                            # Handle GraphQL edge structure
                            if 'node' in item:
                                article = self.create_article_from_node(item['node'])
                            else:
                                article = self.create_article_from_node(item)
                            
                            if article:
                                articles.append(article)
                    
                    if articles:
                        break
            
            # Also search recursively for any data that looks like articles
            if not articles:
                articles = self.search_next_data_recursively(next_data)
                
        except Exception as e:
            print(f"         ❌ Error extracting from Next.js data: {e}")
        
        return articles
    
    def search_next_data_recursively(self, data: Any, path: str = "root") -> List[Dict[str, Any]]:
        """Recursively search Next.js data for article-like structures."""
        articles = []
        
        if isinstance(data, dict):
            # Look for arrays that might contain articles
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Check if this list contains article-like objects
                    sample = value[0] if value else None
                    if (isinstance(sample, dict) and 
                        ('url' in sample or 'link' in sample) and 
                        ('title' in sample or 'headline' in sample)):
                        
                        print(f"         📊 Found potential articles at: {path}.{key} ({len(value)} items)")
                        
                        for item in value:
                            if isinstance(item, dict):
                                # Handle GraphQL edge structure
                                if 'node' in item:
                                    article = self.create_article_from_node(item['node'])
                                else:
                                    article = self.create_article_from_node(item)
                                
                                if article:
                                    articles.append(article)
                        
                        # Don't search deeper if we found articles here
                        if articles:
                            break
                
                # Recurse into nested objects
                if isinstance(value, (dict, list)) and not articles:
                    nested_articles = self.search_next_data_recursively(value, f"{path}.{key}")
                    articles.extend(nested_articles)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)) and not articles:
                    nested_articles = self.search_next_data_recursively(item, f"{path}[{i}]")
                    articles.extend(nested_articles)
        
        return articles
    
    def extract_articles_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract articles from JSON data."""
        articles = []
        
        def search_for_articles(obj):
            if isinstance(obj, dict):
                # Handle GraphQL edge structure
                if 'edges' in obj and isinstance(obj['edges'], list):
                    for edge in obj['edges']:
                        if isinstance(edge, dict) and 'node' in edge:
                            article = self.create_article_from_node(edge['node'])
                            if article:
                                articles.append(article)
                
                # Handle direct article arrays
                for key in ['articles', 'posts', 'feed', 'data']:
                    if key in obj and isinstance(obj[key], list):
                        for item in obj[key]:
                            article = self.create_article_from_node(item)
                            if article:
                                articles.append(article)
                
                # Recurse into nested objects
                for value in obj.values():
                    search_for_articles(value)
                    
            elif isinstance(obj, list):
                for item in obj:
                    search_for_articles(item)
        
        search_for_articles(data)
        return articles
    
    def create_article_from_node(self, node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create article from a data node."""
        if not isinstance(node, dict):
            return None
        
        # Must have URL and title
        url = node.get('url') or node.get('link') or node.get('permalink')
        title = node.get('title') or node.get('headline')
        
        if not url or not title:
            return None
        
        return {
            'id': node.get('id', ''),
            'url': url,
            'title': title,
            'summary': node.get('summary') or node.get('description') or node.get('excerpt', ''),
            'created_at': node.get('createdAt') or node.get('publishedAt') or node.get('date', ''),
            'read_time': node.get('readTime', 0),
            'upvotes': node.get('numUpvotes') or node.get('upvotes', 0),
            'comments': node.get('numComments') or node.get('comments', 0),
            'source': self.extract_source_name(node),
            'author': self.extract_author_name(node),
            'tags': node.get('tags', []),
            'feed_type': 'MANUAL_AUTH'
        }
    
    def extract_source_name(self, node: Dict[str, Any]) -> str:
        """Extract source name from node."""
        source = node.get('source')
        if isinstance(source, dict):
            return source.get('name', 'Daily.dev')
        elif isinstance(source, str):
            return source
        return 'Daily.dev'
    
    def extract_author_name(self, node: Dict[str, Any]) -> str:
        """Extract author name from node."""
        author = node.get('author')
        if isinstance(author, dict):
            return author.get('name', '')
        elif isinstance(author, str):
            return author
        return ''
    
    def extract_articles_from_dom(self, html: str) -> List[Dict[str, Any]]:
        """Extract articles from HTML DOM structure."""
        articles = []
        
        # Look for article URLs in HTML
        url_patterns = [
            r'href="(https://[^"]+)"',
            r'data-href="(https://[^"]+)"',
            r'link[^>]*href="(https://[^"]+)"'
        ]
        
        urls = set()
        for pattern in url_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                # Filter for article-like URLs
                if any(domain in match for domain in [
                    'medium.com', 'dev.to', 'stackoverflow.com', 'github.com',
                    'techcrunch.com', 'arstechnica.com', 'wired.com', 'verge.com'
                ]):
                    urls.add(match)
        
        # Create basic articles from URLs
        for url in list(urls)[:100]:  # Limit to first 100 URLs
            articles.append({
                'id': '',
                'url': url,
                'title': self.extract_title_from_url(url),
                'summary': '',
                'created_at': '',
                'read_time': 0,
                'upvotes': 0,
                'comments': 0,
                'source': self.extract_domain_from_url(url),
                'author': '',
                'tags': [],
                'feed_type': 'DOM_EXTRACTED'
            })
        
        return articles
    
    def extract_title_from_url(self, url: str) -> str:
        """Extract a reasonable title from URL."""
        # Remove protocol and domain
        path = url.split('/')[-1]
        # Remove file extension
        title = path.split('.')[-2] if '.' in path else path
        # Replace hyphens and underscores with spaces
        title = title.replace('-', ' ').replace('_', ' ')
        # Capitalize
        return title.title() if title else 'Article'
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return 'Unknown'
    
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
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]]) -> int:
        """Add articles to knowledge base."""
        print(f"📚 Adding {len(articles)} Daily.dev articles to knowledge base...")
        
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
                    'tags': ['daily.dev', 'tech', 'article', 'comprehensive'] + article.get('tags', []),
                    'upvotes': article.get('upvotes', 0),
                    'comments': article.get('comments', 0),
                    'read_time': article.get('read_time', 0),
                    'feed_type': article.get('feed_type', 'MANUAL_AUTH'),
                    'manual_authenticated': True
                },
                'content': content,
                'chunks': [content] if content else [],
                'chunk_count': 1 if content else 0,
                'processing_notes': [f'Comprehensive Daily.dev scrape on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 100 == 0:
                print(f"   ✅ Added {added_count} articles...")
                self._save_knowledge_base(kb)
        
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new articles!")
        
        return added_count
    
    def scrape_comprehensive(self, target_articles: int = 3000) -> int:
        """Main comprehensive scraping method."""
        print(f"🚀 COMPREHENSIVE DAILY.DEV SCRAPING (MANUAL AUTH)")
        print(f"🎯 Target: {target_articles} articles")
        
        # Set up authentication
        if not self.load_authentication():
            print("🔐 Setting up manual authentication...")
            if not self.setup_manual_authentication():
                print("❌ Authentication setup failed")
                return 0
            
            if not self.load_authentication():
                print("❌ Could not load authentication after setup")
                return 0
        
        # Scrape articles using GraphQL API (the correct approach)
        articles = self.scrape_daily_dev_graphql(max_articles=target_articles)
        
        if not articles:
            print("❌ No articles found! Check your authentication.")
            return 0
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(articles)
        
        return added_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manual authentication comprehensive Daily.dev scraper")
    parser.add_argument("--target", type=int, default=3000, help="Target number of articles")
    
    args = parser.parse_args()
    
    print("🔐 MANUAL AUTHENTICATION COMPREHENSIVE DAILY.DEV SCRAPER")
    print("=" * 70)
    print("This approach works without Chrome - just copy/paste your cookies!")
    print()
    
    scraper = ManualAuthDailyDevScraper()
    added_count = scraper.scrape_comprehensive(target_articles=args.target)
    
    if added_count > 1000:
        print(f"\n🎉 HUGE SUCCESS! Added {added_count} Daily.dev articles!")
        print("✅ Your AI Advisor now has comprehensive Daily.dev content!")
    elif added_count > 0:
        print(f"\n✅ Added {added_count} Daily.dev articles!")
        print("   This is a good start - you can run again to get more!")
    else:
        print("\n❌ No articles were added. Check your authentication setup.")


if __name__ == "__main__":
    main()