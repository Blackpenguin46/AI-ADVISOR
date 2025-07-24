#!/usr/bin/env python3
"""
Daily.dev Authenticated Scraper
Uses cookies to scrape ALL articles from Daily.dev with authentication.
"""

import requests
import json
import time
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
import re


class DailyDevAuthenticatedScraper:
    """Authenticated scraper for Daily.dev using cookies."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        self.cookies_loaded = False
    
    def load_cookies(self) -> bool:
        """Load authentication cookies from the secure file."""
        cookie_file = Path('daily_dev_cookies.json')
        
        if not cookie_file.exists():
            print("❌ No cookie file found. Run daily_dev_cookie_extractor.py first!")
            return False
        
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            # Check expiration
            expires_str = cookie_data.get('expires_at', '')
            try:
                expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                if datetime.now() > expires_at.replace(tzinfo=None):
                    print("⏰ Cookies expired. Re-run daily_dev_cookie_extractor.py")
                    return False
            except Exception as e:
                print(f"⚠️ Could not parse expiration date: {e}, continuing anyway")
            
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
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            chunk = text[start:end]
            last_period = chunk.rfind('. ')
            
            if last_period > chunk_size * 0.7:
                chunks.append(text[start:start + last_period + 1])
                start = start + last_period + 1 - overlap
            else:
                last_space = chunk.rfind(' ')
                if last_space > chunk_size * 0.7:
                    chunks.append(text[start:start + last_space])
                    start = start + last_space - overlap
                else:
                    chunks.append(chunk)
                    start = end - overlap
            
            if start < 0:
                start = 0
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def test_authentication(self) -> bool:
        """Test if authentication is working."""
        if not self.cookies_loaded:
            return False
        
        try:
            # Try to access the authenticated Daily.dev feed
            response = self.session.get('https://app.daily.dev/', timeout=30)
            
            if response.status_code == 200:
                # Check if we're actually logged in by looking for user-specific content
                content = response.text.lower()
                
                # Look for signs of authentication
                authenticated_indicators = [
                    'logout', 'profile', 'settings', 'my feed', 'bookmarks',
                    'user', 'notifications', 'account'
                ]
                
                if any(indicator in content for indicator in authenticated_indicators):
                    print("✅ Authentication successful - logged in to Daily.dev")
                    return True
                else:
                    print("⚠️ Cookies loaded but may not be authenticated")
                    return True  # Still try scraping
            else:
                print(f"❌ Authentication failed - status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    def discover_api_endpoints(self) -> List[str]:
        """Discover Daily.dev API endpoints by analyzing the web app."""
        print("🔍 Discovering Daily.dev API endpoints...")
        
        endpoints = []
        
        try:
            # Get the main app page
            response = self.session.get('https://app.daily.dev/', timeout=30)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for API endpoints in JavaScript
                api_patterns = [
                    r'https://app\.daily\.dev/api/[^"\']+',
                    r'/api/[^"\']+',
                    r'https://api\.daily\.dev/[^"\']+',
                    r'"posts".*?"query"',
                    r'"feed".*?"query"',
                    r'graphql.*?query',
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    endpoints.extend(matches)
                
                # Common Daily.dev API endpoints to try
                common_endpoints = [
                    'https://app.daily.dev/api/graphql',
                    'https://app.daily.dev/api/posts',
                    'https://app.daily.dev/api/feed',
                    'https://app.daily.dev/api/v1/posts',
                    'https://app.daily.dev/api/v1/feed',
                ]
                
                endpoints.extend(common_endpoints)
                
                # Remove duplicates and clean up
                unique_endpoints = list(set(endpoints))
                
                print(f"🎯 Discovered {len(unique_endpoints)} potential API endpoints")
                return unique_endpoints
                
        except Exception as e:
            print(f"⚠️ Endpoint discovery failed: {e}")
        
        return []
    
    def try_graphql_feed(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Try to get posts using GraphQL API."""
        print("🚀 Trying GraphQL feed...")
        
        articles = []
        
        # Common GraphQL queries for Daily.dev
        graphql_queries = [
            {
                "query": """
                query Feed($first: Int!, $after: String) {
                    page: feed(first: $first, after: $after) {
                        edges {
                            node {
                                id
                                title
                                url
                                summary
                                createdAt
                                updatedAt
                                image
                                source {
                                    name
                                    image
                                }
                                author {
                                    name
                                    username
                                }
                                tags {
                                    name
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
                """,
                "variables": {"first": limit}
            },
            {
                "query": """
                query Posts($first: Int!) {
                    posts(first: $first) {
                        edges {
                            node {
                                id
                                title
                                url
                                summary
                                createdAt
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
                "variables": {"first": limit}
            }
        ]
        
        endpoints = [
            'https://app.daily.dev/api/graphql',
            'https://app.daily.dev/graphql',
            'https://api.daily.dev/graphql',
        ]
        
        for endpoint in endpoints:
            for query_data in graphql_queries:
                try:
                    print(f"🔄 Trying {endpoint}...")
                    
                    response = self.session.post(
                        endpoint,
                        json=query_data,
                        timeout=30,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse GraphQL response
                        posts = []
                        if 'data' in data:
                            if 'page' in data['data'] and 'edges' in data['data']['page']:
                                posts = [edge['node'] for edge in data['data']['page']['edges']]
                            elif 'posts' in data['data'] and 'edges' in data['data']['posts']:
                                posts = [edge['node'] for edge in data['data']['posts']['edges']]
                            elif 'feed' in data['data']:
                                posts = data['data']['feed']
                        
                        if posts:
                            print(f"✅ GraphQL success! Got {len(posts)} posts from {endpoint}")
                            
                            for post in posts:
                                article = {
                                    'url': post.get('url', ''),
                                    'title': post.get('title', ''),
                                    'description': post.get('summary', ''),
                                    'source': post.get('source', {}).get('name', 'Daily.dev'),
                                    'author': post.get('author', {}).get('name', ''),
                                    'created_at': post.get('createdAt', ''),
                                    'tags': [tag.get('name', '') for tag in post.get('tags', [])],
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                if article['url'] and article['title']:
                                    articles.append(article)
                            
                            return articles
                    
                    else:
                        print(f"⚠️ {endpoint} returned status {response.status_code}")
                
                except Exception as e:
                    print(f"⚠️ GraphQL attempt failed: {e}")
                    continue
        
        return articles
    
    def try_rest_api(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Try to get posts using REST API endpoints."""
        print("🔄 Trying REST API endpoints...")
        
        articles = []
        
        # REST API endpoints to try
        rest_endpoints = [
            f'https://app.daily.dev/api/posts?limit={limit}',
            f'https://app.daily.dev/api/feed?limit={limit}',
            f'https://app.daily.dev/api/v1/posts?per_page={limit}',
            f'https://app.daily.dev/api/v1/feed?per_page={limit}',
            f'https://api.daily.dev/posts?limit={limit}',
            f'https://api.daily.dev/feed?limit={limit}',
        ]
        
        for endpoint in rest_endpoints:
            try:
                print(f"🔄 Trying {endpoint}...")
                
                response = self.session.get(endpoint, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse different response formats
                    posts = []
                    if isinstance(data, list):
                        posts = data
                    elif isinstance(data, dict):
                        if 'data' in data:
                            posts = data['data']
                        elif 'posts' in data:
                            posts = data['posts']
                        elif 'feed' in data:
                            posts = data['feed']
                        elif 'results' in data:
                            posts = data['results']
                    
                    if posts:
                        print(f"✅ REST API success! Got {len(posts)} posts from {endpoint}")
                        
                        for post in posts:
                            article = {
                                'url': post.get('url', ''),
                                'title': post.get('title', ''),
                                'description': post.get('summary', post.get('description', '')),
                                'source': 'Daily.dev',
                                'author': post.get('author', {}).get('name', '') if isinstance(post.get('author'), dict) else str(post.get('author', '')),
                                'created_at': post.get('createdAt', post.get('created_at', '')),
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            if article['url'] and article['title']:
                                articles.append(article)
                        
                        return articles
                
                else:
                    print(f"⚠️ {endpoint} returned status {response.status_code}")
            
            except Exception as e:
                print(f"⚠️ REST API attempt failed: {e}")
                continue
        
        return articles
    
    def scrape_html_feed(self) -> List[Dict[str, Any]]:
        """Fallback: scrape Daily.dev HTML directly."""
        print("🔄 Falling back to HTML scraping...")
        
        articles = []
        
        try:
            response = self.session.get('https://app.daily.dev/', timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for article containers with various selectors
                article_selectors = [
                    'article',
                    '.post',
                    '.feed-item',
                    '.story',
                    '[data-testid*="post"]',
                    '.card',
                    '.article-card'
                ]
                
                for selector in article_selectors:
                    elements = soup.select(selector)
                    
                    if elements:
                        print(f"📄 Found {len(elements)} elements with selector '{selector}'")
                        
                        for element in elements:
                            try:
                                # Extract title
                                title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title', '.headline'])
                                title = title_elem.get_text(strip=True) if title_elem else ''
                                
                                # Extract URL
                                link_elem = element.find('a', href=True)
                                url = link_elem['href'] if link_elem else ''
                                
                                # Make URL absolute
                                if url and url.startswith('/'):
                                    url = 'https://app.daily.dev' + url
                                elif url and not url.startswith('http'):
                                    continue  # Skip invalid URLs
                                
                                # Extract description
                                desc_elem = element.find(['p', '.description', '.summary'])
                                description = desc_elem.get_text(strip=True) if desc_elem else ''
                                
                                if url and title:
                                    articles.append({
                                        'url': url,
                                        'title': title,
                                        'description': description,
                                        'source': 'Daily.dev',
                                        'scraped_at': datetime.now().isoformat()
                                    })
                            
                            except Exception as e:
                                continue
                        
                        if articles:
                            print(f"✅ HTML scraping successful! Got {len(articles)} articles")
                            return articles
                
        except Exception as e:
            print(f"❌ HTML scraping failed: {e}")
        
        return articles
    
    def fetch_article_content(self, url: str) -> str:
        """Fetch full article content from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', '.entry-content',
                '#content', '.article-body', '.post-body', '.story-content'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            content = re.sub(r'\s+', ' ', content)
            
            return content[:15000]  # Limit content length
            
        except Exception as e:
            print(f"⚠️ Failed to fetch content from {url}: {e}")
            return ""
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]], fetch_content: bool = True) -> int:
        """Add scraped articles to the knowledge base."""
        print(f"📚 Adding {len(articles)} Daily.dev articles to knowledge base...")
        
        kb = self._load_knowledge_base()
        added_count = 0
        
        for i, article in enumerate(articles):
            if not article.get('url') or not article.get('title'):
                continue
            
            article_id = self._generate_id(article['url'])
            
            # Skip if already exists
            if article_id in kb:
                continue
            
            # Fetch full content
            content = ""
            if fetch_content:
                if i % 10 == 0:
                    print(f"📄 Fetching content for articles {i+1}-{min(i+10, len(articles))}...")
                
                content = self.fetch_article_content(article['url'])
                time.sleep(1)  # Be respectful
            
            if not content:
                content = article.get('description', '')
            
            # Create chunks
            chunks = self._chunk_text(content) if content else []
            
            # Add to knowledge base
            kb[article_id] = {
                'metadata': {
                    'id': article_id,
                    'title': article['title'],
                    'source_type': 'url',
                    'source_url': article['url'],
                    'author': article.get('source', 'Daily.dev'),
                    'date_added': datetime.now().isoformat(),
                    'description': article.get('description', ''),
                    'tags': ['daily.dev', 'tech', 'article', 'authenticated'] + article.get('tags', [])
                },
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'processing_notes': [f'Scraped from Daily.dev with authentication on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 10 == 0:
                print(f"✅ Added {added_count} articles to knowledge base...")
                self._save_knowledge_base(kb)
        
        # Final save
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new Daily.dev articles!")
        
        return added_count
    
    def scrape_all_daily_dev(self, max_articles: int = 500, fetch_content: bool = True) -> int:
        """Main method to scrape ALL Daily.dev articles."""
        print(f"🚀 Starting COMPLETE Daily.dev scraping (target: {max_articles} articles)")
        
        # Load cookies
        if not self.load_cookies():
            print("❌ Failed to load authentication cookies")
            return 0
        
        # Test authentication
        if not self.test_authentication():
            print("❌ Authentication failed")
            return 0
        
        all_articles = []
        
        # Try multiple methods to get articles
        print("🔍 Trying multiple scraping methods...")
        
        # Method 1: GraphQL API
        graphql_articles = self.try_graphql_feed(max_articles)
        if graphql_articles:
            all_articles.extend(graphql_articles)
            print(f"✅ GraphQL: {len(graphql_articles)} articles")
        
        # Method 2: REST API (if GraphQL didn't get enough)
        if len(all_articles) < max_articles // 2:
            rest_articles = self.try_rest_api(max_articles)
            if rest_articles:
                all_articles.extend(rest_articles)
                print(f"✅ REST API: {len(rest_articles)} articles")
        
        # Method 3: HTML scraping (fallback)
        if len(all_articles) < 10:
            html_articles = self.scrape_html_feed()
            if html_articles:
                all_articles.extend(html_articles)
                print(f"✅ HTML scraping: {len(html_articles)} articles")
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"📊 Found {len(unique_articles)} unique Daily.dev articles")
        
        if not unique_articles:
            print("❌ No articles found! Check authentication or try manual cookie extraction")
            return 0
        
        # Limit to requested max
        if len(unique_articles) > max_articles:
            unique_articles = unique_articles[:max_articles]
            print(f"📊 Limited to {max_articles} articles as requested")
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(unique_articles, fetch_content)
        
        return added_count


def create_authenticated_scraper_interface():
    """Create Streamlit interface for authenticated Daily.dev scraping."""
    st.header("🔐 Daily.dev Authenticated Scraper")
    st.write("Scrape ALL articles from Daily.dev using your authenticated session")
    
    # Check if cookies exist
    cookie_file = Path('daily_dev_cookies.json')
    
    if not cookie_file.exists():
        st.error("❌ No authentication cookies found!")
        st.write("**Setup required:**")
        st.code("python daily_dev_cookie_extractor.py")
        st.info("Run the cookie extractor first to set up authentication")
        return
    
    # Load cookie info
    try:
        with open(cookie_file, 'r') as f:
            cookie_data = json.load(f)
        
        expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
        
        if datetime.now() > expires_at:
            st.error("⏰ Authentication cookies expired!")
            st.write("**Re-run cookie extractor:**")
            st.code("python daily_dev_cookie_extractor.py")
            return
        
        st.success(f"✅ Authentication cookies loaded ({len(cookie_data['cookies'])} cookies)")
        time_left = expires_at - datetime.now()
        st.info(f"⏰ Expires in {time_left.seconds // 3600} hours")
        
    except Exception as e:
        st.error(f"❌ Failed to load cookies: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_articles = st.slider("Maximum articles to scrape", 100, 1000, 500)
        fetch_content = st.checkbox("Fetch full article content", True)
    
    with col2:
        st.metric("Scraping method", "Authenticated")
        st.info("This will get your personalized Daily.dev feed")
    
    # Show scraping strategy
    st.subheader("🎯 Scraping Strategy")
    st.write("""
    1. **GraphQL API** - Try Daily.dev's internal API
    2. **REST API** - Try alternative API endpoints  
    3. **HTML Scraping** - Fallback to page scraping
    4. **Content Fetching** - Get full article text
    """)
    
    if st.button("🚀 Start Authenticated Scraping", type="primary"):
        scraper = DailyDevAuthenticatedScraper()
        
        with st.spinner(f"Scraping {max_articles} articles from your Daily.dev feed..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Loading authentication cookies...")
            progress_bar.progress(10)
            
            try:
                added_count = scraper.scrape_all_daily_dev(
                    max_articles=max_articles,
                    fetch_content=fetch_content
                )
                
                progress_bar.progress(100)
                
                if added_count > 0:
                    st.success(f"🎉 Successfully added {added_count} new Daily.dev articles!")
                    st.balloons()
                    
                    # Show updated stats
                    kb = scraper._load_knowledge_base()
                    daily_dev_articles = [
                        data for data in kb.values() 
                        if 'daily.dev' in data['metadata'].get('tags', [])
                    ]
                    
                    st.success(f"📊 Your knowledge base now has {len(daily_dev_articles)} Daily.dev articles!")
                    
                    # Show breakdown
                    authenticated_articles = [
                        data for data in daily_dev_articles
                        if 'authenticated' in data['metadata'].get('tags', [])
                    ]
                    
                    st.metric("🔐 Authenticated articles", len(authenticated_articles))
                    st.metric("📰 Total Daily.dev articles", len(daily_dev_articles))
                    
                    # Show sample articles
                    st.subheader("📰 Recently added articles:")
                    recent_articles = sorted(
                        authenticated_articles, 
                        key=lambda x: x['metadata']['date_added'], 
                        reverse=True
                    )[:5]
                    
                    for article in recent_articles:
                        with st.expander(f"📄 {article['metadata']['title'][:70]}..."):
                            st.write(f"**Source:** {article['metadata']['author']}")
                            st.write(f"**URL:** {article['metadata']['source_url']}")
                            if article['metadata']['description']:
                                st.write(f"**Description:** {article['metadata']['description'][:200]}...")
                            st.write(f"**Chunks:** {article['chunk_count']}")
                            st.write(f"**Added:** {article['metadata']['date_added'][:10]}")
                
                else:
                    st.warning("No new articles were added. They might already exist or authentication failed.")
                    st.info("Try re-running the cookie extractor if articles aren't loading")
                    
            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
                st.write("**Troubleshooting:**")
                st.write("1. Re-run cookie extractor")
                st.write("2. Make sure you're logged into Daily.dev")
                st.write("3. Check if Daily.dev changed their API")


if __name__ == "__main__":
    # Command line usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Daily.dev with authentication")
    parser.add_argument("--max-articles", type=int, default=500, help="Maximum articles to scrape")
    parser.add_argument("--no-content", action="store_true", help="Don't fetch full content")
    
    args = parser.parse_args()
    
    scraper = DailyDevAuthenticatedScraper()
    added_count = scraper.scrape_all_daily_dev(
        max_articles=args.max_articles,
        fetch_content=not args.no_content
    )
    
    print(f"\n🎉 Daily.dev scraping complete! Added {added_count} articles to knowledge base.")