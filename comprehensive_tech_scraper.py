#!/usr/bin/env python3
"""
Comprehensive Tech Article Scraper with Daily.dev Integration

This scraper combines all working sources including Daily.dev with authentication.
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
import re
from modern_dailydev_scraper import ModernDailyDevScraper


def scrape_comprehensive_tech_articles(max_articles: int = 200) -> int:
    """Scrape from all available tech sources including Daily.dev."""
    print(f"🚀 Starting comprehensive tech scraping (target: {max_articles} articles)")
    
    articles_per_source = max_articles // 6  # Distribute across 6 sources
    print(f"📊 Target: {articles_per_source} articles per source")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    all_articles = []
    
    # 1. Daily.dev (NEW!)
    print("📡 Fetching from Daily.dev...")
    try:
        daily_scraper = ModernDailyDevScraper()
        daily_scraper.load_cookies()  # Load if available
        daily_articles = daily_scraper.get_feed_articles(articles_per_source)
        
        for article in daily_articles:
            all_articles.append({
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'description': article.get('summary', ''),
                'source': 'Daily.dev',
                'scraped_at': datetime.now().isoformat(),
                'upvotes': article.get('upvotes', 0),
                'tags': article.get('tags', [])
            })
        
        print(f"✅ Got {len([a for a in all_articles if a['source'] == 'Daily.dev'])} articles from Daily.dev")
    except Exception as e:
        print(f"⚠️ Daily.dev scraping failed: {e}")
    
    # 2. Hacker News
    print("📡 Fetching from Hacker News API...")
    try:
        # Get top stories
        response = session.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=30)
        if response.status_code == 200:
            story_ids = response.json()[:articles_per_source]
            
            for i, story_id in enumerate(story_ids):
                if i % 5 == 0:
                    print(f"  📄 Fetched {i+1}/{len(story_ids)} stories...")
                
                try:
                    story_response = session.get(
                        f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                        timeout=10
                    )
                    if story_response.status_code == 200:
                        story = story_response.json()
                        if story.get('url'):  # Only include stories with URLs
                            all_articles.append({
                                'url': story['url'],
                                'title': story.get('title', ''),
                                'description': story.get('text', ''),
                                'source': 'Hacker News',
                                'scraped_at': datetime.now().isoformat()
                            })
                    time.sleep(0.1)  # Rate limiting
                except Exception:
                    continue
            
            print(f"✅ Got {len([a for a in all_articles if a['source'] == 'Hacker News'])} articles from Hacker News")
    except Exception as e:
        print(f"⚠️ Hacker News scraping failed: {e}")
    
    # 3. Reddit
    print("📡 Fetching from Reddit programming...")
    subreddits = ['programming', 'MachineLearning', 'artificial', 'technology', 'webdev']
    
    for subreddit in subreddits:
        try:
            response = session.get(f'https://www.reddit.com/r/{subreddit}/hot.json?limit={articles_per_source//len(subreddits)}', timeout=30)
            if response.status_code == 200:
                data = response.json()
                for post in data['data']['children']:
                    post_data = post['data']
                    if post_data.get('url') and not post_data['url'].startswith('https://www.reddit.com'):
                        all_articles.append({
                            'url': post_data['url'],
                            'title': post_data.get('title', ''),
                            'description': post_data.get('selftext', ''),
                            'source': f'Reddit r/{subreddit}',
                            'scraped_at': datetime.now().isoformat()
                        })
            time.sleep(1)  # Reddit rate limiting
        except Exception as e:
            print(f"⚠️ Reddit r/{subreddit} failed: {e}")
    
    print(f"✅ Got {len([a for a in all_articles if 'Reddit' in a['source']])} articles from Reddit")
    
    # 4. Dev.to
    print("📡 Fetching from Dev.to API...")
    try:
        response = session.get(f'https://dev.to/api/articles?per_page={articles_per_source}&top=7', timeout=30)
        if response.status_code == 200:
            articles = response.json()
            for article in articles:
                all_articles.append({
                    'url': article.get('url', ''),
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'source': 'Dev.to',
                    'scraped_at': datetime.now().isoformat()
                })
            print(f"✅ Got {len([a for a in all_articles if a['source'] == 'Dev.to'])} articles from Dev.to")
    except Exception as e:
        print(f"⚠️ Dev.to scraping failed: {e}")
    
    # 5. GitHub Trending
    print("📡 Fetching from GitHub trending...")
    try:
        response = session.get('https://github.com/trending', timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            repos = soup.find_all('article', class_='Box-row')
            
            for repo in repos[:articles_per_source]:
                try:
                    title_elem = repo.find('h2')
                    if title_elem and title_elem.find('a'):
                        repo_path = title_elem.find('a')['href']
                        repo_url = f"https://github.com{repo_path}"
                        title = title_elem.get_text(strip=True)
                        
                        desc_elem = repo.find('p')
                        description = desc_elem.get_text(strip=True) if desc_elem else ''
                        
                        all_articles.append({
                            'url': repo_url,
                            'title': title,
                            'description': description,
                            'source': 'GitHub Trending',
                            'scraped_at': datetime.now().isoformat()
                        })
                except Exception:
                    continue
            
            print(f"✅ Got {len([a for a in all_articles if a['source'] == 'GitHub Trending'])} repos from GitHub trending")
    except Exception as e:
        print(f"⚠️ GitHub trending scraping failed: {e}")
    
    # 6. Lobsters
    print("📡 Fetching from Lobsters...")
    try:
        response = session.get('https://lobste.rs/hottest.json', timeout=30)
        if response.status_code == 200:
            posts = response.json()
            for post in posts[:articles_per_source]:
                all_articles.append({
                    'url': post.get('url', post.get('comments_url', '')),
                    'title': post.get('title', ''),
                    'description': post.get('description', ''),
                    'source': 'Lobsters',
                    'scraped_at': datetime.now().isoformat()
                })
            print(f"✅ Got {len([a for a in all_articles if a['source'] == 'Lobsters'])} articles from Lobsters")
        else:
            print(f"⚠️ Lobsters returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Lobsters scraping failed: {e}")
    
    # Remove duplicates
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls and article['url']:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    print(f"📊 Found {len(unique_articles)} unique articles total")
    
    # Add to knowledge base using the working scraper's method
    return add_articles_to_knowledge_base(unique_articles)


def add_articles_to_knowledge_base(articles: List[Dict[str, Any]]) -> int:
    """Add articles to the unified knowledge base."""
    print(f"📚 Adding {len(articles)} articles to knowledge base...")
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    knowledge_file = data_dir / "unified_knowledge_base.json"
    
    # Load existing knowledge base
    kb = {}
    if knowledge_file.exists():
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                kb = json.load(f)
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    added_count = 0
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    for i, article in enumerate(articles):
        if not article.get('url') or not article.get('title'):
            continue
        
        article_id = hashlib.md5(article['url'].encode()).hexdigest()[:12]
        
        # Skip if already exists
        if article_id in kb:
            continue
        
        # Fetch content for every 10th article to avoid rate limiting
        content = ""
        if i % 10 == 0:
            print(f"📄 Fetching content for articles {i+1}-{min(i+10, len(articles))}...")
            try:
                response = session.get(article['url'], timeout=30)
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
                
                for selector in content_selectors:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text(separator=' ', strip=True)
                        break
                
                if not content:
                    content = soup.get_text(separator=' ', strip=True)
                
                # Clean up content
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                content = '\n'.join(lines)
                content = re.sub(r'\s+', ' ', content)
                content = content[:10000]  # Limit content length
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"⚠️ Failed to fetch content from {article['url']}: {e}")
                content = article.get('description', '')
        else:
            content = article.get('description', '')
        
        # Create chunks
        chunks = []
        if content:
            chunk_size = 1000
            for j in range(0, len(content), chunk_size):
                chunks.append(content[j:j+chunk_size])
        
        # Add to knowledge base
        kb[article_id] = {
            'metadata': {
                'id': article_id,
                'title': article['title'],
                'source_type': 'url',
                'source_url': article['url'],
                'author': article['source'],
                'date_added': datetime.now().isoformat(),
                'description': article.get('description', ''),
                'tags': ['daily.dev', 'tech', 'article'] + article.get('tags', []) if article['source'] == 'Daily.dev' else ['tech', 'article']
            },
            'content': content,
            'chunks': chunks,
            'chunk_count': len(chunks),
            'processing_notes': [f'Scraped from {article["source"]} on {datetime.now().strftime("%Y-%m-%d")}']
        }
        
        added_count += 1
        
        if added_count % 10 == 0:
            print(f"✅ Added {added_count} articles to knowledge base...")
            # Save periodically
            try:
                with open(knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump(kb, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving knowledge base: {e}")
    
    # Final save
    try:
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(kb, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving knowledge base: {e}")
    
    print(f"🎉 Successfully added {added_count} new articles!")
    return added_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive tech scraper with Daily.dev")
    parser.add_argument("--max-articles", type=int, default=200, help="Maximum articles to scrape")
    
    args = parser.parse_args()
    
    added_count = scrape_comprehensive_tech_articles(max_articles=args.max_articles)
    print(f"\n🎉 Comprehensive scraping complete! Added {added_count} articles to knowledge base.")


if __name__ == "__main__":
    main()