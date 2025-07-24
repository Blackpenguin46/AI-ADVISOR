#!/usr/bin/env python3
"""
Working Tech Article Scraper
A reliable scraper that gets articles from multiple working sources.
"""

import requests
import json
import time
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
import re


class WorkingTechScraper:
    """Scraper that uses working endpoints and HTML scraping."""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.knowledge_file = self.data_directory / "unified_knowledge_base.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
    
    def scrape_hacker_news(self, max_articles: int = 30) -> List[Dict[str, Any]]:
        """Scrape Hacker News using their API."""
        print("📡 Fetching from Hacker News API...")
        articles = []
        
        try:
            # Get top stories
            response = self.session.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=30)
            response.raise_for_status()
            story_ids = response.json()[:max_articles]
            
            for i, story_id in enumerate(story_ids):
                if i >= max_articles:
                    break
                
                try:
                    # Get story details
                    story_response = self.session.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10)
                    story_response.raise_for_status()
                    story = story_response.json()
                    
                    if story and story.get('url') and story.get('title'):
                        articles.append({
                            'url': story['url'],
                            'title': story['title'],
                            'description': story.get('text', '')[:500] if story.get('text') else '',
                            'source': 'Hacker News',
                            'score': story.get('score', 0),
                            'scraped_at': datetime.now().isoformat()
                        })
                    
                    if i % 5 == 0:
                        print(f"  📄 Fetched {i+1}/{len(story_ids)} stories...")
                
                except Exception as e:
                    continue
            
            print(f"✅ Got {len(articles)} articles from Hacker News")
            
        except Exception as e:
            print(f"❌ Hacker News failed: {e}")
        
        return articles
    
    def scrape_reddit_programming(self, max_articles: int = 25) -> List[Dict[str, Any]]:
        """Scrape Reddit programming subreddits."""
        print("📡 Fetching from Reddit programming...")
        articles = []
        
        subreddits = ['programming', 'MachineLearning', 'artificial', 'technology', 'webdev']
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                for post in data['data']['children']:
                    post_data = post['data']
                    
                    # Skip self posts without URLs
                    if post_data.get('is_self', True) and not post_data.get('url_overridden_by_dest'):
                        continue
                    
                    url = post_data.get('url_overridden_by_dest') or post_data.get('url', '')
                    title = post_data.get('title', '')
                    
                    if url and title and 'reddit.com' not in url:
                        articles.append({
                            'url': url,
                            'title': title,
                            'description': post_data.get('selftext', '')[:500],
                            'source': f'Reddit r/{subreddit}',
                            'score': post_data.get('score', 0),
                            'scraped_at': datetime.now().isoformat()
                        })
                    
                    if len(articles) >= max_articles:
                        break
                
                time.sleep(1)  # Be nice to Reddit
                
            except Exception as e:
                print(f"⚠️ Reddit r/{subreddit} failed: {e}")
                continue
        
        print(f"✅ Got {len(articles)} articles from Reddit")
        return articles
    
    def scrape_dev_to_api(self, max_articles: int = 30) -> List[Dict[str, Any]]:
        """Scrape Dev.to using their API."""
        print("📡 Fetching from Dev.to API...")
        articles = []
        
        try:
            # Dev.to has a public API
            response = self.session.get(f"https://dev.to/api/articles?per_page={max_articles}&top=7", timeout=30)
            response.raise_for_status()
            
            posts = response.json()
            
            for post in posts:
                articles.append({
                    'url': post.get('url', ''),
                    'title': post.get('title', ''),
                    'description': post.get('description', '')[:500],
                    'source': 'Dev.to',
                    'tags': post.get('tag_list', []),
                    'published': post.get('published_at', ''),
                    'scraped_at': datetime.now().isoformat()
                })
            
            print(f"✅ Got {len(articles)} articles from Dev.to")
            
        except Exception as e:
            print(f"❌ Dev.to failed: {e}")
        
        return articles
    
    def scrape_github_trending(self, max_articles: int = 20) -> List[Dict[str, Any]]:
        """Scrape GitHub trending repositories."""
        print("📡 Fetching from GitHub trending...")
        articles = []
        
        try:
            response = self.session.get("https://github.com/trending", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find trending repo containers
            repos = soup.find_all('article', class_='Box-row')
            
            for repo in repos[:max_articles]:
                try:
                    # Get repo title/name
                    title_elem = repo.find('h2')
                    if not title_elem:
                        continue
                    
                    repo_link = title_elem.find('a')
                    if not repo_link:
                        continue
                    
                    title = repo_link.get_text(strip=True)
                    url = "https://github.com" + repo_link.get('href', '')
                    
                    # Get description
                    desc_elem = repo.find('p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    # Get language
                    lang_elem = repo.find('span', itemprop='programmingLanguage')
                    language = lang_elem.get_text(strip=True) if lang_elem else ''
                    
                    # Get stars
                    stars_elem = repo.find('a', href=lambda x: x and '/stargazers' in x)
                    stars = stars_elem.get_text(strip=True) if stars_elem else '0'
                    
                    if url and title:
                        articles.append({
                            'url': url,
                            'title': f"{title} ({language})" if language else title,
                            'description': f"{description} ⭐ {stars}",
                            'source': 'GitHub Trending',
                            'language': language,
                            'stars': stars,
                            'scraped_at': datetime.now().isoformat()
                        })
                
                except Exception as e:
                    continue
            
            print(f"✅ Got {len(articles)} repos from GitHub trending")
            
        except Exception as e:
            print(f"❌ GitHub trending failed: {e}")
        
        return articles
    
    def scrape_lobsters(self, max_articles: int = 25) -> List[Dict[str, Any]]:
        """Scrape Lobsters tech news."""
        print("📡 Fetching from Lobsters...")
        articles = []
        
        try:
            response = self.session.get("https://lobste.rs/", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find story containers
            stories = soup.find_all('div', class_='story')
            
            for story in stories[:max_articles]:
                try:
                    # Get title and URL
                    title_elem = story.find('a', class_='u-url')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    # Get description/tags
                    tags_elem = story.find('div', class_='tags')
                    tags = [tag.get_text(strip=True) for tag in tags_elem.find_all('a')] if tags_elem else []
                    
                    # Get domain
                    domain_elem = story.find('span', class_='domain')
                    domain = domain_elem.get_text(strip=True) if domain_elem else ''
                    
                    if url and title:
                        articles.append({
                            'url': url,
                            'title': title,
                            'description': f"From {domain}. Tags: {', '.join(tags)}" if tags else f"From {domain}",
                            'source': 'Lobsters',
                            'tags': tags,
                            'domain': domain,
                            'scraped_at': datetime.now().isoformat()
                        })
                
                except Exception as e:
                    continue
            
            print(f"✅ Got {len(articles)} articles from Lobsters")
            
        except Exception as e:
            print(f"❌ Lobsters failed: {e}")
        
        return articles
    
    def fetch_article_content(self, url: str, max_length: int = 15000) -> str:
        """Fetch full article content from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'button']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', '.entry-content', 
                '#content', '.article-body', '.post-body', '.story-content',
                '.markdown-body', '.readme'  # For GitHub
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                # Fallback to body
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)
            
            return content[:max_length]
            
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
            if fetch_content and len(articles) <= 100:  # Only for reasonable batch sizes
                if i % 10 == 0:
                    print(f"📄 Fetching content for articles {i+1}-{min(i+10, len(articles))}...")
                
                content = self.fetch_article_content(article['url'])
                time.sleep(0.5)  # Be respectful
                
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
                    'author': article.get('source', 'Tech News'),
                    'date_added': datetime.now().isoformat(),
                    'description': article.get('description', ''),
                    'tags': ['daily.dev', 'tech', 'article'] + article.get('tags', [])
                },
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'processing_notes': [f'Scraped from {article.get("source", "web")} on {datetime.now().strftime("%Y-%m-%d")}']
            }
            
            added_count += 1
            
            if added_count % 10 == 0:
                print(f"✅ Added {added_count} articles to knowledge base...")
                # Save periodically
                self._save_knowledge_base(kb)
        
        # Final save
        self._save_knowledge_base(kb)
        print(f"🎉 Successfully added {added_count} new articles to knowledge base!")
        
        return added_count
    
    def scrape_and_add(self, max_articles: int = 100, fetch_content: bool = True) -> int:
        """Main method to scrape multiple sources and add to knowledge base."""
        print(f"🚀 Starting comprehensive tech scraping (target: {max_articles} articles)")
        
        all_articles = []
        
        # Calculate articles per source
        sources_count = 5  # We have 5 scraping methods
        per_source = max_articles // sources_count
        
        # Scrape from all sources
        print(f"📊 Target: {per_source} articles per source")
        
        all_articles.extend(self.scrape_hacker_news(per_source))
        all_articles.extend(self.scrape_reddit_programming(per_source))
        all_articles.extend(self.scrape_dev_to_api(per_source))
        all_articles.extend(self.scrape_github_trending(per_source))
        all_articles.extend(self.scrape_lobsters(per_source))
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"📊 Found {len(unique_articles)} unique articles total")
        
        if not unique_articles:
            print("❌ No articles found!")
            return 0
        
        # Limit to requested max
        if len(unique_articles) > max_articles:
            unique_articles = unique_articles[:max_articles]
            print(f"📊 Limited to {max_articles} articles as requested")
        
        # Add to knowledge base
        added_count = self.add_articles_to_knowledge_base(unique_articles, fetch_content)
        
        return added_count


def create_working_scraper_interface():
    """Create Streamlit interface for the working scraper."""
    st.header("🚀 Working Tech Article Scraper")
    st.write("Scrape tech articles from Hacker News, Reddit, Dev.to, GitHub, and Lobsters")
    
    st.success("This scraper uses working APIs and endpoints that actually return articles!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_articles = st.slider("Maximum articles to scrape", 50, 300, 150)
        fetch_content = st.checkbox("Fetch full article content", True)
    
    with col2:
        st.metric("Estimated sources", "5 platforms")
        st.info(f"~{max_articles//5} articles per source")
    
    # Show what sources we'll use
    st.subheader("📡 Sources")
    sources_info = """
    - **Hacker News** - Tech stories and discussions
    - **Reddit** - Programming, ML, AI, and tech subreddits  
    - **Dev.to** - Developer articles and tutorials
    - **GitHub** - Trending repositories and projects
    - **Lobsters** - Tech news and discussions
    """
    st.markdown(sources_info)
    
    if st.button("🚀 Start Comprehensive Scraping", type="primary"):
        scraper = WorkingTechScraper()
        
        with st.spinner(f"Scraping {max_articles} tech articles from 5 sources..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Initializing scraper...")
            progress_bar.progress(10)
            
            try:
                added_count = scraper.scrape_and_add(
                    max_articles=max_articles,
                    fetch_content=fetch_content
                )
                
                progress_bar.progress(100)
                
                if added_count > 0:
                    st.success(f"🎉 Successfully added {added_count} new articles to your knowledge base!")
                    st.balloons()
                    
                    # Show updated stats
                    kb = scraper._load_knowledge_base()
                    tech_articles = [
                        data for data in kb.values() 
                        if 'daily.dev' in data['metadata'].get('tags', []) or 
                           'tech' in data['metadata'].get('tags', [])
                    ]
                    
                    st.success(f"📊 Your knowledge base now has {len(tech_articles)} tech articles!")
                    
                    # Show breakdown by source
                    sources = {}
                    for article in tech_articles:
                        source = article['metadata'].get('author', 'Unknown')
                        sources[source] = sources.get(source, 0) + 1
                    
                    st.subheader("📊 Articles by source:")
                    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"• **{source}**: {count} articles")
                    
                    # Show sample of newest articles
                    st.subheader("📰 Recently added articles:")
                    recent_articles = sorted(tech_articles, key=lambda x: x['metadata']['date_added'], reverse=True)[:5]
                    
                    for article in recent_articles:
                        with st.expander(f"📄 {article['metadata']['title'][:70]}..."):
                            st.write(f"**Source:** {article['metadata']['author']}")
                            st.write(f"**URL:** {article['metadata']['source_url']}")
                            if article['metadata']['description']:
                                st.write(f"**Description:** {article['metadata']['description'][:200]}...")
                            st.write(f"**Chunks:** {article['chunk_count']}")
                            st.write(f"**Added:** {article['metadata']['date_added'][:10]}")
                else:
                    st.warning("No new articles were added. They might already exist in your knowledge base.")
                    
            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
                st.exception(e)


if __name__ == "__main__":
    # Command line usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape tech articles from working sources")
    parser.add_argument("--max-articles", type=int, default=150, help="Maximum articles to scrape")
    parser.add_argument("--no-content", action="store_true", help="Don't fetch full content")
    
    args = parser.parse_args()
    
    scraper = WorkingTechScraper()
    added_count = scraper.scrape_and_add(
        max_articles=args.max_articles,
        fetch_content=not args.no_content
    )
    
    print(f"\n🎉 Scraping complete! Added {added_count} articles to knowledge base.")