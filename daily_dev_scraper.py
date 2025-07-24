#!/usr/bin/env python3
"""
Daily.dev Web Scraper
Scrapes articles from daily.dev and adds them to the AI Advisor knowledge base.
"""

import requests
import json
import time
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import hashlib
from pathlib import Path


class DailyDevScraper:
    """Scrapes articles from Daily.dev and processes them for the knowledge base."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
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
            
            if last_period > chunk_size * 0.7:  # Good break point
                chunks.append(text[start:start + last_period + 1])
                start = start + last_period + 1 - overlap
            else:
                # Break at word boundary
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
    
    def scrape_with_selenium(self, max_articles: int = 100) -> List[Dict[str, Any]]:
        """Scrape Daily.dev articles using Selenium for dynamic content."""
        print(f"🔄 Starting Selenium scraper for {max_articles} articles...")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        articles = []
        
        try:
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            
            print("📱 Loading Daily.dev...")
            driver.get("https://app.daily.dev/")
            
            # Wait for articles to load
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            
            articles_found = 0
            scroll_attempts = 0
            max_scrolls = 20
            
            while articles_found < max_articles and scroll_attempts < max_scrolls:
                # Find all article elements
                article_elements = driver.find_elements(By.TAG_NAME, "article")
                
                for article_elem in article_elements[articles_found:]:
                    if articles_found >= max_articles:
                        break
                    
                    try:
                        # Extract article link
                        link_elem = article_elem.find_element(By.TAG_NAME, "a")
                        article_url = link_elem.get_attribute("href")
                        
                        # Extract title
                        title_elem = article_elem.find_element(By.CSS_SELECTOR, "h2, h3, .title, [data-testid*='title']")
                        title = title_elem.text.strip()
                        
                        # Extract summary/description
                        description = ""
                        try:
                            desc_elem = article_elem.find_element(By.CSS_SELECTOR, "p, .summary, .description")
                            description = desc_elem.text.strip()
                        except:
                            pass
                        
                        # Extract source/author
                        source = "Daily.dev"
                        try:
                            source_elem = article_elem.find_element(By.CSS_SELECTOR, ".source, .author, [data-testid*='source']")
                            source = source_elem.text.strip()
                        except:
                            pass
                        
                        if article_url and title:
                            articles.append({
                                'url': article_url,
                                'title': title,
                                'description': description,
                                'source': source,
                                'scraped_at': datetime.now().isoformat()
                            })
                            articles_found += 1
                            
                            if articles_found % 10 == 0:
                                print(f"📄 Found {articles_found} articles...")
                    
                    except Exception as e:
                        continue
                
                # Scroll down to load more articles
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_attempts += 1
            
            driver.quit()
            print(f"✅ Scraped {len(articles)} articles from Daily.dev")
            
        except Exception as e:
            print(f"❌ Selenium scraping failed: {e}")
            try:
                driver.quit()
            except:
                pass
        
        return articles
    
    def scrape_with_api(self, max_articles: int = 50) -> List[Dict[str, Any]]:
        """Try to scrape using Daily.dev API endpoints."""
        print(f"🔄 Trying API scraping for {max_articles} articles...")
        
        articles = []
        
        # Try different API endpoints
        api_urls = [
            "https://app.daily.dev/api/graphql",
            "https://api.daily.dev/v1/posts",
            "https://app.daily.dev/posts"
        ]
        
        for api_url in api_urls:
            try:
                if "graphql" in api_url:
                    # GraphQL query for posts
                    query = {
                        "query": """
                        query Posts($first: Int!) {
                            posts(first: $first) {
                                edges {
                                    node {
                                        id
                                        title
                                        url
                                        summary
                                        author {
                                            name
                                        }
                                        source {
                                            name
                                        }
                                        createdAt
                                    }
                                }
                            }
                        }
                        """,
                        "variables": {"first": max_articles}
                    }
                    
                    response = self.session.post(api_url, json=query, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'posts' in data['data']:
                            for edge in data['data']['posts']['edges']:
                                node = edge['node']
                                articles.append({
                                    'url': node.get('url', ''),
                                    'title': node.get('title', ''),
                                    'description': node.get('summary', ''),
                                    'source': node.get('source', {}).get('name', 'Daily.dev'),
                                    'author': node.get('author', {}).get('name', ''),
                                    'created_at': node.get('createdAt', ''),
                                    'scraped_at': datetime.now().isoformat()
                                })
                else:
                    # REST API
                    params = {'limit': max_articles, 'page': 1}
                    response = self.session.get(api_url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            posts = data
                        elif 'posts' in data:
                            posts = data['posts']
                        elif 'data' in data:
                            posts = data['data']
                        else:
                            continue
                        
                        for post in posts[:max_articles]:
                            articles.append({
                                'url': post.get('url', ''),
                                'title': post.get('title', ''),
                                'description': post.get('description', post.get('summary', '')),
                                'source': post.get('source', {}).get('name', 'Daily.dev') if isinstance(post.get('source'), dict) else post.get('source', 'Daily.dev'),
                                'scraped_at': datetime.now().isoformat()
                            })
                
                if articles:
                    print(f"✅ API scraping successful: {len(articles)} articles")
                    return articles
                    
            except Exception as e:
                print(f"⚠️ API {api_url} failed: {e}")
                continue
        
        print("❌ All API endpoints failed")
        return []
    
    def fetch_article_content(self, url: str) -> str:
        """Fetch full article content from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '#content', '.article-body'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Clean up content
            lines = content.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            content = '\n'.join(lines)
            
            return content[:10000]  # Limit to 10k characters
            
        except Exception as e:
            print(f"⚠️ Failed to fetch content from {url}: {e}")
            return ""
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]], fetch_content: bool = True) -> int:
        """Add scraped articles to the knowledge base."""
        print(f"📚 Adding {len(articles)} articles to knowledge base...")
        
        kb = self._load_knowledge_base()
        added_count = 0
        
        for i, article in enumerate(articles):
            if not article.get('url') or not article.get('title'):
                continue
            
            article_id = self._generate_id(article['url'])
            
            # Skip if already exists
            if article_id in kb:
                continue
            
            # Fetch full content if requested
            content = ""
            if fetch_content:
                print(f"📄 Fetching content for article {i+1}/{len(articles)}: {article['title'][:50]}...")
                content = self.fetch_article_content(article['url'])
                if not content:
                    content = article.get('description', '')
            else:
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
                    'tags': ['daily.dev', 'tech', 'article']
                },
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'processing_notes': [f'Scraped from Daily.dev on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 5 == 0:
                print(f"✅ Added {added_count} articles to knowledge base...")
                # Save periodically
                self._save_knowledge_base(kb)
        
        # Final save
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new articles to knowledge base!")
        
        return added_count
    
    def scrape_and_add(self, max_articles: int = 100, use_selenium: bool = True, fetch_content: bool = True) -> int:
        """Main method to scrape Daily.dev and add articles to knowledge base."""
        print(f"🚀 Starting Daily.dev scraping (max: {max_articles} articles)")
        
        # Try API first (faster)
        articles = self.scrape_with_api(max_articles)
        
        # If API fails or gets few results, use Selenium
        if len(articles) < 10 and use_selenium:
            print("🔄 API results limited, switching to Selenium...")
            selenium_articles = self.scrape_with_selenium(max_articles)
            articles.extend(selenium_articles)
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"📊 Found {len(unique_articles)} unique articles")
        
        if not unique_articles:
            print("❌ No articles found!")
            return 0
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(unique_articles, fetch_content)
        
        return added_count


def create_scraper_interface():
    """Create Streamlit interface for the Daily.dev scraper."""
    st.header("📰 Daily.dev Article Scraper")
    st.write("Scrape articles from Daily.dev and add them to your knowledge base")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_articles = st.slider("Maximum articles to scrape", 10, 500, 100)
        use_selenium = st.checkbox("Use Selenium (slower but more reliable)", True)
    
    with col2:
        fetch_content = st.checkbox("Fetch full article content", True)
        st.info("Full content fetching takes longer but provides better search results")
    
    if st.button("🚀 Start Scraping", type="primary"):
        scraper = DailyDevScraper()
        
        with st.spinner(f"Scraping {max_articles} articles from Daily.dev..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Initializing scraper...")
            progress_bar.progress(10)
            
            try:
                added_count = scraper.scrape_and_add(
                    max_articles=max_articles,
                    use_selenium=use_selenium,
                    fetch_content=fetch_content
                )
                
                progress_bar.progress(100)
                
                if added_count > 0:
                    st.success(f"🎉 Successfully added {added_count} new articles to your knowledge base!")
                    st.balloons()
                    
                    # Show sample of added articles
                    st.subheader("Sample of added articles:")
                    kb = scraper._load_knowledge_base()
                    daily_dev_articles = [
                        (rid, data) for rid, data in kb.items() 
                        if 'daily.dev' in data['metadata'].get('tags', [])
                    ]
                    
                    for rid, data in daily_dev_articles[-5:]:  # Show last 5 added
                        with st.expander(f"📄 {data['metadata']['title'][:60]}..."):
                            st.write(f"**Source:** {data['metadata']['author']}")
                            st.write(f"**URL:** {data['metadata']['source_url']}")
                            st.write(f"**Description:** {data['metadata']['description'][:200]}...")
                            st.write(f"**Chunks:** {data['chunk_count']}")
                else:
                    st.warning("No new articles were added. They might already exist in your knowledge base.")
                    
            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
                st.exception(e)


if __name__ == "__main__":
    # Command line usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Daily.dev articles")
    parser.add_argument("--max-articles", type=int, default=100, help="Maximum articles to scrape")
    parser.add_argument("--no-selenium", action="store_true", help="Don't use Selenium")
    parser.add_argument("--no-content", action="store_true", help="Don't fetch full content")
    
    args = parser.parse_args()
    
    scraper = DailyDevScraper()
    added_count = scraper.scrape_and_add(
        max_articles=args.max_articles,
        use_selenium=not args.no_selenium,
        fetch_content=not args.no_content
    )
    
    print(f"\n🎉 Scraping complete! Added {added_count} articles to knowledge base.")