#!/usr/bin/env python3
"""
Modern Daily.dev Scraper

Uses the correct Daily.dev GraphQL API endpoint and modern query structure.
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import hashlib


class ModernDailyDevScraper:
    """Modern scraper for Daily.dev using the correct GraphQL API."""
    
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

    def load_cookies(self) -> bool:
        """Load authentication cookies."""
        cookie_file = Path('daily_dev_cookies.json')
        
        if not cookie_file.exists():
            print("❌ No cookie file found.")
            return False
        
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            cookies = cookie_data['cookies']
            self.session.cookies.update(cookies)
            
            print(f"✅ Loaded {len(cookies)} cookies for authentication")
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
    
    def get_feed_articles(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get articles from Daily.dev feed using modern GraphQL API."""
        print(f"🔍 Fetching {limit} articles from Daily.dev feed...")
        
        # Modern Daily.dev GraphQL query
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
                "first": limit,
                "ranking": "POPULARITY",
                "supportedTypes": ["article", "share", "freeform"]
            }
        }
        
        try:
            response = self.session.post(self.api_url, json=query, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'page' in data['data'] and 'edges' in data['data']['page']:
                    articles = []
                    edges = data['data']['page']['edges']
                    
                    print(f"✅ Successfully fetched {len(edges)} articles from Daily.dev")
                    
                    for edge in edges:
                        node = edge['node']
                        
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
                        }
                        
                        if article['url'] and article['title']:
                            articles.append(article)
                    
                    return articles
                
                else:
                    print(f"⚠️ Unexpected response structure: {data}")
                    return []
            
            else:
                print(f"❌ API request failed with status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching articles: {e}")
            return []
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]]) -> int:
        """Add Daily.dev articles to the knowledge base."""
        print(f"📚 Adding {len(articles)} Daily.dev articles to knowledge base...")
        
        kb = self._load_knowledge_base()
        added_count = 0
        
        for article in articles:
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
            
            # Add to knowledge base
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
                    'read_time': article.get('read_time', 0)
                },
                'content': content,
                'chunks': [content] if content else [],
                'chunk_count': 1 if content else 0,
                'processing_notes': [f'Scraped from Daily.dev API on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 10 == 0:
                print(f"✅ Added {added_count} articles...")
                self._save_knowledge_base(kb)
        
        # Final save
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new Daily.dev articles!")
        
        return added_count
    
    def scrape_daily_dev(self, max_articles: int = 50) -> int:
        """Main method to scrape Daily.dev articles."""
        print(f"🚀 Starting Daily.dev scraping (target: {max_articles} articles)")
        
        # Load cookies if available
        if not self.load_cookies():
            print("⚠️ No authentication cookies found, trying without authentication...")
        
        # Get articles
        articles = self.get_feed_articles(max_articles)
        
        if not articles:
            print("❌ No articles found from Daily.dev")
            return 0
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(articles)
        
        return added_count


def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Modern Daily.dev scraper")
    parser.add_argument("--max-articles", type=int, default=50, help="Maximum articles to scrape")
    
    args = parser.parse_args()
    
    scraper = ModernDailyDevScraper()
    added_count = scraper.scrape_daily_dev(max_articles=args.max_articles)
    
    print(f"\n🎉 Daily.dev scraping complete! Added {added_count} articles to knowledge base.")


if __name__ == "__main__":
    main()