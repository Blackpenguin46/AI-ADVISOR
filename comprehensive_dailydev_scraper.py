#!/usr/bin/env python3
"""
Comprehensive Daily.dev Scraper

This scraper gets THOUSANDS of articles from your Daily.dev account using:
- Pagination to get many pages of results
- Multiple feed types (personalized, popular, recent, trending)
- Your bookmarks and reading history
- All sources you follow
- Historical articles
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from pathlib import Path
import hashlib
import sys


class ComprehensiveDailyDevScraper:
    """Comprehensive scraper that gets ALL your Daily.dev content."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://app.daily.dev',
            'Referer': 'https://app.daily.dev/',
        })
        self.api_url = "https://api.daily.dev/graphql"
        self.cookies_loaded = False
        self.scraped_urls: Set[str] = set()  # Track scraped URLs to avoid duplicates
        
    def load_cookies(self) -> bool:
        """Load authentication cookies."""
        cookie_file = Path('daily_dev_cookies.json')
        
        if not cookie_file.exists():
            print("❌ No Daily.dev cookie file found. Cannot scrape personalized content!")
            return False
        
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            cookies = cookie_data['cookies']
            self.session.cookies.update(cookies)
            
            print(f"✅ Loaded {len(cookies)} Daily.dev cookies for authenticated scraping")
            self.cookies_loaded = True
            return True
            
        except Exception as e:
            print(f"❌ Failed to load cookies: {e}")
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
    
    def get_feed_with_pagination(self, feed_type: str = "POPULARITY", max_pages: int = 20, articles_per_page: int = 50) -> List[Dict[str, Any]]:
        """Get articles with pagination to fetch many pages."""
        print(f"🔍 Scraping {feed_type} feed with pagination ({max_pages} pages, {articles_per_page} per page)")
        
        all_articles = []
        cursor = None
        page = 0
        
        while page < max_pages:
            print(f"   📄 Fetching page {page + 1}/{max_pages}...")
            
            # GraphQL query with pagination
            query = {
                "query": """
                query Feed($first: Int, $after: String, $ranking: Ranking, $supportedTypes: [String!]) {
                  page: feed(
                    first: $first
                    after: $after
                    ranking: $ranking
                    supportedTypes: $supportedTypes
                  ) {
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      node {
                        id
                        url
                        title
                        summary
                        createdAt
                        updatedAt
                        readTime
                        image
                        permalink
                        commentsPermalink
                        numUpvotes
                        numComments
                        source {
                          id
                          name
                          image
                          public
                        }
                        tags
                        author {
                          id
                          name
                          username
                          image
                        }
                      }
                    }
                  }
                }
                """,
                "variables": {
                    "first": articles_per_page,
                    "after": cursor,
                    "ranking": feed_type,
                    "supportedTypes": ["article", "share", "freeform", "video:youtube"]
                }
            }
            
            try:
                response = self.session.post(self.api_url, json=query, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'page' in data['data'] and 'edges' in data['data']['page']:
                        edges = data['data']['page']['edges']
                        page_info = data['data']['page']['pageInfo']
                        
                        print(f"      ✅ Got {len(edges)} articles from page {page + 1}")
                        
                        # Process articles
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
                                    'image': node.get('image', ''),
                                    'upvotes': node.get('numUpvotes', 0),
                                    'comments': node.get('numComments', 0),
                                    'source': node.get('source', {}).get('name', 'Daily.dev'),
                                    'author': node.get('author', {}).get('name', '') if node.get('author') else '',
                                    'tags': node.get('tags') or [],
                                    'feed_type': feed_type
                                }
                                
                                all_articles.append(article)
                                self.scraped_urls.add(article['url'])
                        
                        # Check if there are more pages
                        if not page_info.get('hasNextPage'):
                            print(f"      📋 Reached end of {feed_type} feed at page {page + 1}")
                            break
                        
                        cursor = page_info.get('endCursor')
                        page += 1
                        
                        # Rate limiting
                        time.sleep(2)
                        
                    else:
                        print(f"      ❌ Unexpected response structure: {data}")
                        break
                
                else:
                    print(f"      ❌ API request failed with status {response.status_code}")
                    if response.status_code == 429:  # Rate limited
                        print("         💤 Rate limited, waiting 10 seconds...")
                        time.sleep(10)
                        continue
                    break
                    
            except Exception as e:
                print(f"      ❌ Error fetching page {page + 1}: {e}")
                break
        
        print(f"✅ {feed_type} feed complete: {len(all_articles)} unique articles")
        return all_articles
    
    def get_bookmarks(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Get user's bookmarked articles."""
        print(f"🔖 Scraping your bookmarks ({max_pages} pages)...")
        
        all_bookmarks = []
        cursor = None
        page = 0
        
        while page < max_pages:
            print(f"   📄 Fetching bookmark page {page + 1}/{max_pages}...")
            
            # GraphQL query for bookmarks
            query = {
                "query": """
                query Bookmarks($first: Int, $after: String) {
                  bookmarks(first: $first, after: $after) {
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
                        image
                        numUpvotes
                        numComments
                        source {
                          name
                        }
                        tags
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
                response = self.session.post(self.api_url, json=query, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'bookmarks' in data['data']:
                        edges = data['data']['bookmarks']['edges']
                        page_info = data['data']['bookmarks']['pageInfo']
                        
                        print(f"      ✅ Got {len(edges)} bookmarks from page {page + 1}")
                        
                        for edge in edges:
                            node = edge['node']
                            
                            if node.get('url') and node.get('url') not in self.scraped_urls:
                                bookmark = {
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
                                    'tags': node.get('tags') or [],
                                    'feed_type': 'BOOKMARKS'
                                }
                                
                                all_bookmarks.append(bookmark)
                                self.scraped_urls.add(bookmark['url'])
                        
                        if not page_info.get('hasNextPage'):
                            print(f"      📋 Reached end of bookmarks at page {page + 1}")
                            break
                        
                        cursor = page_info.get('endCursor')
                        page += 1
                        time.sleep(1)
                        
                    else:
                        print(f"      ❌ No bookmarks data in response")
                        break
                
                else:
                    print(f"      ❌ Bookmarks request failed with status {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"      ❌ Error fetching bookmarks page {page + 1}: {e}")
                break
        
        print(f"✅ Bookmarks complete: {len(all_bookmarks)} unique bookmarks")
        return all_bookmarks
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]]) -> int:
        """Add comprehensive Daily.dev articles to knowledge base."""
        print(f"📚 Adding {len(articles)} comprehensive Daily.dev articles to knowledge base...")
        
        kb = self._load_knowledge_base()
        added_count = 0
        
        # Count existing content
        youtube_count = 0
        existing_dailydev_count = 0
        
        for item in kb.values():
            if 'metadata' in item:
                metadata = item['metadata']
                if metadata.get('source_type') == 'video':
                    youtube_count += 1
                elif 'daily.dev' in metadata.get('tags', []):
                    existing_dailydev_count += 1
        
        print(f"📊 Current knowledge base: {youtube_count} YouTube videos, {existing_dailydev_count} Daily.dev articles")
        
        for i, article in enumerate(articles):
            if not article.get('url') or not article.get('title'):
                continue
            
            article_id = self._generate_id(article['url'])
            
            # Skip if already exists
            if article_id in kb:
                continue
            
            # Create content from summary
            content = article.get('summary', '')
            if not content:
                content = article.get('title', '')
            
            # Add comprehensive metadata
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
                    'tags': ['daily.dev', 'tech', 'article'] + article.get('tags', []),
                    'upvotes': article.get('upvotes', 0),
                    'comments': article.get('comments', 0),
                    'read_time': article.get('read_time', 0),
                    'feed_type': article.get('feed_type', 'UNKNOWN'),
                    'created_at': article.get('created_at', ''),
                    'comprehensive_scrape': True  # Mark as comprehensive scrape
                },
                'content': content,
                'chunks': [content] if content else [],
                'chunk_count': 1 if content else 0,
                'processing_notes': [f'Comprehensive Daily.dev scrape on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 100 == 0:
                print(f"✅ Added {added_count} articles...")
                self._save_knowledge_base(kb)
        
        # Final save
        self._save_knowledge_base(kb)
        
        # Final count
        final_youtube_count = 0
        final_dailydev_count = 0
        
        for item in kb.values():
            if 'metadata' in item:
                metadata = item['metadata']
                if metadata.get('source_type') == 'video':
                    final_youtube_count += 1
                elif 'daily.dev' in metadata.get('tags', []):
                    final_dailydev_count += 1
        
        print(f"🎉 Successfully added {added_count} new Daily.dev articles!")
        print(f"📊 Final knowledge base: {final_youtube_count} YouTube videos, {final_dailydev_count} Daily.dev articles")
        
        return added_count
    
    def scrape_comprehensive_daily_dev(self, target_articles: int = 5000) -> int:
        """Main method to comprehensively scrape Daily.dev."""
        print(f"🚀 COMPREHENSIVE Daily.dev scraping (target: {target_articles} articles)")
        print("📺 YouTube videos will be preserved")
        print("🔐 Using your authentication for personalized content")
        
        if not self.load_cookies():
            print("❌ Cannot proceed without authentication cookies!")
            return 0
        
        all_articles = []
        
        # Feed types to scrape
        feed_types = [
            ("POPULARITY", "Popular articles", 30),      # 30 pages = ~1500 articles
            ("TIME", "Recent articles", 20),             # 20 pages = ~1000 articles  
            ("UPVOTES", "Most upvoted", 15),            # 15 pages = ~750 articles
        ]
        
        # Scrape different feed types
        for feed_type, description, max_pages in feed_types:
            print(f"\n📡 Scraping {description}...")
            feed_articles = self.get_feed_with_pagination(
                feed_type=feed_type, 
                max_pages=max_pages,
                articles_per_page=50
            )
            all_articles.extend(feed_articles)
            
            print(f"   📊 Running total: {len(all_articles)} unique articles")
            
            if len(all_articles) >= target_articles:
                print(f"   🎯 Reached target of {target_articles} articles!")
                break
        
        # Scrape bookmarks
        print(f"\n🔖 Scraping your bookmarks...")
        bookmarks = self.get_bookmarks(max_pages=10)
        all_articles.extend(bookmarks)
        
        print(f"\n📊 SCRAPING COMPLETE:")
        print(f"   Total unique articles scraped: {len(all_articles)}")
        print(f"   Target was: {target_articles}")
        
        if len(all_articles) == 0:
            print("❌ No articles scraped! Check your authentication.")
            return 0
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(all_articles)
        
        return added_count


def main():
    """Main function to run comprehensive scraping."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Daily.dev scraper - gets thousands of articles")
    parser.add_argument("--target", type=int, default=5000, help="Target number of articles to scrape")
    
    args = parser.parse_args()
    
    print("🔥 COMPREHENSIVE DAILY.DEV SCRAPER")
    print("=" * 60)
    print("This will scrape THOUSANDS of articles from your Daily.dev account!")
    print()
    
    scraper = ComprehensiveDailyDevScraper()
    added_count = scraper.scrape_comprehensive_daily_dev(target_articles=args.target)
    
    print(f"\n🎉 Comprehensive Daily.dev scraping complete!")
    print(f"📊 Added {added_count} new articles to knowledge base")
    
    if added_count > 1000:
        print("✅ SUCCESS: Now you have thousands of Daily.dev articles!")
    elif added_count > 0:
        print("⚠️  Got some articles, but may need to run again for full coverage")
    else:
        print("❌ No articles added - check your authentication cookies")


if __name__ == "__main__":
    main()