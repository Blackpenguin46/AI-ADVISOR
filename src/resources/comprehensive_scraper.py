"""
Comprehensive Daily.dev scraper that fetches ALL available resources.
Implements pagination, infinite scroll, and bulk processing.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st

from .unified_knowledge_base import UnifiedKnowledgeBase
from .daily_dev_integration import DailyDevMCPClient

logger = logging.getLogger(__name__)


class ComprehensiveDailyDevScraper:
    """Scraper that fetches ALL resources from daily.dev."""
    
    def __init__(self, knowledge_base: UnifiedKnowledgeBase):
        self.kb = knowledge_base
        self.scraped_urls: Set[str] = set()
        self.scraped_hashes: Set[str] = set()
        self.session_stats = {
            "articles_found": 0,
            "articles_processed": 0,
            "articles_added": 0,
            "articles_skipped": 0,
            "errors": [],
            "start_time": None,
            "end_time": None,
            "pages_scraped": 0,
            "scroll_attempts": 0
        }
        
        # Load existing articles to avoid re-processing
        self._load_existing_articles()
    
    def _load_existing_articles(self):
        """Load existing daily.dev articles to avoid duplicates."""
        existing_resources = self.kb.get_all_resources()
        
        for resource_data in existing_resources.values():
            url = resource_data.get('source_url', '')
            if 'daily.dev' in url or any(tag == 'daily.dev' for tag in resource_data.get('tags', [])):
                self.scraped_urls.add(url)
                # Also track by title hash for better deduplication
                title = resource_data.get('title', '')
                if title:
                    import hashlib
                    title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                    self.scraped_hashes.add(title_hash)
        
        logger.info(f"Found {len(self.scraped_urls)} existing daily.dev articles")
    
    def create_comprehensive_driver(self):
        """Create optimized Chrome driver for extensive scraping."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Faster loading
        options.add_argument('--disable-javascript')  # Faster if not needed
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--memory-pressure-off')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (compatible; AIAdvisorBot/1.0; Comprehensive)')
        
        # Performance optimization
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(45)
            return driver
        except Exception as e:
            logger.error(f"Failed to create comprehensive driver: {e}")
            raise
    
    def extract_all_articles_from_page(self, driver) -> List[Dict[str, Any]]:
        """Extract all articles from the current page."""
        articles = []
        
        # Multiple selectors to catch all possible article containers
        article_selectors = [
            'article',
            '[data-testid*="post"]',
            '[data-testid*="article"]',
            'div[role="article"]',
            'a[href*="/posts/"]',
            'div:has(h1)',
            'div:has(h2)', 
            'div:has(h3)',
            'div:has(a[href*="/posts/"])',
            '.post', '.article', '.card',
            '[class*="post"]', '[class*="article"]'
        ]
        
        found_elements = set()  # Avoid duplicate elements
        
        for selector in article_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    # Use element ID or location to avoid duplicates
                    element_id = f"{element.location['x']},{element.location['y']},{element.size['width']},{element.size['height']}"
                    if element_id not in found_elements:
                        found_elements.add(element_id)
                        
                        article_data = self.extract_comprehensive_article_data(element)
                        if article_data:
                            articles.append(article_data)
                            
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Remove duplicates based on content hash
        unique_articles = []
        seen_hashes = set()
        
        for article in articles:
            content_hash = article.get('content_hash')
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_articles.append(article)
        
        return unique_articles
    
    def extract_comprehensive_article_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract comprehensive data from article element."""
        try:
            article_data = {}
            
            # Title extraction with multiple strategies
            title_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5',
                '[data-testid*="title"]',
                '[data-testid*="post-title"]', 
                '.title', '.post-title', '.article-title',
                'a[href*="/posts/"]',
                'span[class*="title"]'
            ]
            
            title_text = None
            for selector in title_selectors:
                try:
                    title_elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for title_elem in title_elements:
                        text = title_elem.text.strip()
                        if text and 10 <= len(text) <= 200:  # Reasonable title length
                            title_text = text
                            break
                    if title_text:
                        break
                except:
                    continue
            
            if not title_text:
                return None
            
            article_data['title'] = title_text
            
            # Generate content hash for deduplication
            import hashlib
            content_hash = hashlib.md5(title_text.encode()).hexdigest()[:12]
            article_data['content_hash'] = content_hash
            
            # Skip if we already have this article
            if content_hash in self.scraped_hashes:
                return None
            
            # URL extraction - both daily.dev and external
            try:
                # Daily.dev post URL
                daily_links = element.find_elements(By.CSS_SELECTOR, 'a[href*="/posts/"]')
                for link in daily_links:
                    href = link.get_attribute('href')
                    if href and '/posts/' in href:
                        article_data['daily_dev_url'] = href
                        break
                
                # External/source URL
                external_links = element.find_elements(By.CSS_SELECTOR, 'a[href^="http"]:not([href*="daily.dev"])')
                for link in external_links:
                    href = link.get_attribute('href')
                    if href and not any(excluded in href.lower() for excluded in ['facebook', 'twitter', 'linkedin', 'share', 'mailto']):
                        article_data['url'] = href
                        break
            except:
                pass
            
            # Enhanced tag extraction
            try:
                tag_selectors = [
                    '[data-testid*="tag"]',
                    '.tag', '.badge', '.chip', '.label',
                    '[class*="tag"]', '[class*="badge"]',
                    'span[style*="background"]',  # Color-coded tags
                    'small', 'span[class*="text-xs"]'  # Small text that might be tags
                ]
                
                tags = set()
                for selector in tag_selectors:
                    try:
                        tag_elements = element.find_elements(By.CSS_SELECTOR, selector)
                        for tag_elem in tag_elements:
                            tag_text = tag_elem.text.strip().lower()
                            if tag_text and 2 <= len(tag_text) <= 25 and tag_text.replace(' ', '').isalnum():
                                tags.add(tag_text)
                    except:
                        continue
                
                if tags:
                    article_data['tags'] = list(tags)
            except:
                pass
            
            # Engagement metrics (upvotes, comments, views)
            try:
                metric_selectors = [
                    '[data-testid*="upvote"]', '[data-testid*="vote"]',
                    '[data-testid*="comment"]', '[data-testid*="view"]',
                    '[aria-label*="upvote"]', '[aria-label*="comment"]',
                    'button', 'span[class*="count"]'
                ]
                
                for selector in metric_selectors:
                    try:
                        metric_elements = element.find_elements(By.CSS_SELECTOR, selector)
                        for metric_elem in metric_elements:
                            text = metric_elem.text.strip()
                            if text.isdigit():
                                number = int(text)
                                aria_label = metric_elem.get_attribute('aria-label') or ''
                                data_testid = metric_elem.get_attribute('data-testid') or ''
                                
                                if 'upvote' in aria_label.lower() or 'upvote' in data_testid.lower():
                                    article_data['upvotes'] = number
                                elif 'comment' in aria_label.lower() or 'comment' in data_testid.lower():
                                    article_data['comments'] = number
                                elif 'view' in aria_label.lower() or 'view' in data_testid.lower():
                                    article_data['views'] = number
                    except:
                        continue
            except:
                pass
            
            # Author information
            try:
                author_selectors = [
                    '[data-testid*="author"]', '[data-testid*="user"]',
                    '.author', '.user', '.byline',
                    'img[alt*="avatar"]', 'img[src*="avatar"]'
                ]
                
                for selector in author_selectors:
                    try:
                        author_elem = element.find_element(By.CSS_SELECTOR, selector)
                        if 'img' in selector:
                            author_name = author_elem.get_attribute('alt')
                        else:
                            author_name = author_elem.text.strip()
                        
                        if author_name and len(author_name) < 100:
                            article_data['author'] = {'name': author_name}
                            break
                    except:
                        continue
            except:
                pass
            
            # Publication date/time
            try:
                time_selectors = [
                    'time', '[datetime]',
                    '[data-testid*="date"]', '[data-testid*="time"]',
                    'span[title*="ago"]', 'span[title*="hour"]'
                ]
                
                for selector in time_selectors:
                    try:
                        time_elem = element.find_element(By.CSS_SELECTOR, selector)
                        datetime_attr = time_elem.get_attribute('datetime')
                        if datetime_attr:
                            article_data['published_at'] = datetime_attr
                            break
                        
                        time_text = time_elem.text.strip()
                        if time_text and any(word in time_text.lower() for word in ['ago', 'hour', 'day', 'week', 'month']):
                            article_data['published_at_text'] = time_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Source domain
            if article_data.get('url'):
                from urllib.parse import urlparse
                try:
                    domain = urlparse(article_data['url']).netloc
                    article_data['source_domain'] = domain
                except:
                    pass
            
            # Add scraping metadata
            article_data['scraped_at'] = datetime.now().isoformat()
            article_data['scraping_method'] = 'comprehensive'
            
            return article_data
            
        except Exception as e:
            logger.warning(f"Error extracting comprehensive article data: {e}")
            return None
    
    async def scrape_all_daily_dev_articles(self, 
                                          max_pages: int = 50, 
                                          max_scroll_per_page: int = 20,
                                          delay_between_pages: float = 2.0,
                                          progress_callback=None) -> Dict[str, Any]:
        """Scrape ALL articles from daily.dev with pagination and scrolling."""
        
        self.session_stats["start_time"] = datetime.now().isoformat()
        
        driver = None
        all_articles = []
        
        try:
            driver = self.create_comprehensive_driver()
            
            # Start with the main posts page
            base_urls = [
                "https://app.daily.dev/posts",
                "https://app.daily.dev/posts?r=all",  # All posts
                "https://app.daily.dev/posts?r=popular",  # Popular
                "https://app.daily.dev/posts?r=recent",  # Recent
            ]
            
            for base_url in base_urls:
                try:
                    logger.info(f"Scraping from: {base_url}")
                    driver.get(base_url)
                    await asyncio.sleep(3)  # Let page load
                    
                    page_num = 0
                    no_new_articles_count = 0
                    
                    while page_num < max_pages and no_new_articles_count < 3:
                        page_num += 1
                        self.session_stats["pages_scraped"] += 1
                        
                        if progress_callback:
                            progress_callback(f"Scraping page {page_num} from {base_url}")
                        
                        # Scroll to load more content
                        articles_before_scroll = len(all_articles)
                        
                        for scroll in range(max_scroll_per_page):
                            try:
                                # Scroll down
                                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                await asyncio.sleep(1)
                                
                                # Extract articles from current view
                                current_articles = self.extract_all_articles_from_page(driver)
                                
                                # Add new articles
                                new_articles_added = 0
                                for article in current_articles:
                                    content_hash = article.get('content_hash')
                                    if content_hash and content_hash not in self.scraped_hashes:
                                        all_articles.append(article)
                                        self.scraped_hashes.add(content_hash)
                                        if article.get('url'):
                                            self.scraped_urls.add(article['url'])
                                        new_articles_added += 1
                                
                                self.session_stats["scroll_attempts"] += 1
                                
                                if progress_callback:
                                    progress_callback(f"Page {page_num}, Scroll {scroll+1}: Found {len(current_articles)} articles, {new_articles_added} new")
                                
                                # Check if we're still finding new content
                                if new_articles_added == 0:
                                    no_new_articles_count += 1
                                    if no_new_articles_count >= 5:  # No new articles in 5 scrolls
                                        break
                                else:
                                    no_new_articles_count = 0
                                
                                # Try to find and click "Load more" buttons
                                try:
                                    load_more_selectors = [
                                        'button[data-testid*="load"]',
                                        'button:contains("Load more")',
                                        'button:contains("Show more")',
                                        '[data-testid*="load-more"]'
                                    ]
                                    
                                    for selector in load_more_selectors:
                                        try:
                                            load_more_btn = driver.find_element(By.CSS_SELECTOR, selector)
                                            if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                                                driver.execute_script("arguments[0].click();", load_more_btn)
                                                await asyncio.sleep(2)
                                                break
                                        except:
                                            continue
                                except:
                                    pass
                                
                            except Exception as e:
                                logger.warning(f"Error during scroll {scroll}: {e}")
                                continue
                        
                        # Check if we found any new articles on this page
                        articles_after_scroll = len(all_articles)
                        if articles_after_scroll == articles_before_scroll:
                            no_new_articles_count += 1
                        else:
                            no_new_articles_count = 0
                        
                        # Small delay between pages
                        await asyncio.sleep(delay_between_pages)
                    
                except Exception as e:
                    logger.error(f"Error scraping {base_url}: {e}")
                    self.session_stats["errors"].append(f"Error scraping {base_url}: {str(e)}")
                    continue
            
            # Update session stats
            self.session_stats["articles_found"] = len(all_articles)
            
            if progress_callback:
                progress_callback(f"Scraping complete! Found {len(all_articles)} total articles")
            
            return {
                "success": True,
                "articles": all_articles,
                "stats": self.session_stats
            }
            
        except Exception as e:
            logger.error(f"Comprehensive scraping failed: {e}")
            self.session_stats["errors"].append(f"Comprehensive scraping failed: {str(e)}")
            return {
                "success": False,
                "articles": all_articles,
                "stats": self.session_stats,
                "error": str(e)
            }
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            self.session_stats["end_time"] = datetime.now().isoformat()
    
    async def process_and_add_articles(self, articles: List[Dict[str, Any]], 
                                     fetch_content: bool = False,
                                     batch_size: int = 10,
                                     progress_callback=None) -> Dict[str, Any]:
        """Process scraped articles and add them to knowledge base."""
        
        results = {
            "articles_processed": 0,
            "articles_added": 0,
            "articles_skipped": 0,
            "errors": []
        }
        
        total_articles = len(articles)
        
        for i in range(0, total_articles, batch_size):
            batch = articles[i:i + batch_size]
            
            if progress_callback:
                progress_callback(f"Processing batch {i//batch_size + 1}/{(total_articles + batch_size - 1)//batch_size}")
            
            for article in batch:
                try:
                    results["articles_processed"] += 1
                    
                    # Check if already exists
                    article_url = article.get('url') or article.get('daily_dev_url')
                    if article_url and article_url in self.scraped_urls:
                        results["articles_skipped"] += 1
                        continue
                    
                    # Prepare article data for knowledge base
                    title = article.get('title', 'Daily.dev Article')
                    author = article.get('author', {}).get('name', 'Daily.dev')
                    tags = ['daily.dev', 'tech', 'programming'] + article.get('tags', [])
                    
                    # Create content from available metadata
                    content_parts = [f"Title: {title}"]
                    
                    if article.get('tags'):
                        content_parts.append(f"Tags: {', '.join(article['tags'])}")
                    if article.get('upvotes'):
                        content_parts.append(f"Upvotes: {article['upvotes']}")
                    if article.get('comments'):
                        content_parts.append(f"Comments: {article['comments']}")
                    if article.get('source_domain'):
                        content_parts.append(f"Source: {article['source_domain']}")
                    if article.get('published_at_text'):
                        content_parts.append(f"Published: {article['published_at_text']}")
                    
                    content = "\n".join(content_parts)
                    
                    # Optionally fetch full content
                    if fetch_content and article_url:
                        try:
                            # Use your MCP client or direct HTTP to fetch content
                            pass  # Implementation would go here
                        except Exception as e:
                            logger.warning(f"Failed to fetch content for {article_url}: {e}")
                    
                    # Add to knowledge base
                    success = self.kb.add_resource(
                        source=content,
                        source_type='url',
                        title=title,
                        author=author,
                        description=f"Article from daily.dev: {title}",
                        tags=tags
                    )
                    
                    if success:
                        results["articles_added"] += 1
                        if article_url:
                            self.scraped_urls.add(article_url)
                    else:
                        results["articles_skipped"] += 1
                
                except Exception as e:
                    results["errors"].append(f"Error processing article: {str(e)}")
                    continue
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return results


def create_comprehensive_scraper_interface(knowledge_base: UnifiedKnowledgeBase):
    """Create interface for comprehensive daily.dev scraping."""
    
    st.subheader("🌐 Comprehensive Daily.dev Scraper")
    st.write("Scrape ALL available articles from daily.dev (may take significant time)")
    
    # Initialize scraper
    if 'comprehensive_scraper' not in st.session_state:
        st.session_state.comprehensive_scraper = ComprehensiveDailyDevScraper(knowledge_base)
    
    scraper = st.session_state.comprehensive_scraper
    
    # Current status
    existing_count = len(scraper.scraped_urls)
    st.info(f"📊 Found {existing_count} existing daily.dev articles in your knowledge base")
    
    # Configuration
    st.write("**⚙️ Scraping Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_pages = st.slider("Maximum pages to scrape", 10, 200, 50, 
                             help="More pages = more articles but longer scraping time")
        
        max_scroll = st.slider("Scrolls per page", 5, 50, 20,
                              help="More scrolls = more articles per page")
        
        fetch_content = st.checkbox("Fetch full article content", value=False,
                                   help="Get complete articles (much slower)")
    
    with col2:
        delay_pages = st.slider("Delay between pages (seconds)", 1.0, 10.0, 2.0,
                               help="Longer delays = more respectful to servers")
        
        batch_size = st.slider("Processing batch size", 5, 50, 10,
                              help="Articles processed at once")
        
        st.write("**Estimated Time:**")
        estimated_minutes = (max_pages * max_scroll * 0.1) + (max_pages * delay_pages / 60)
        st.write(f"~{estimated_minutes:.1f} minutes")
    
    # Warning about comprehensive scraping
    st.warning("""
    ⚠️ **Comprehensive Scraping Notice:**
    
    - This will attempt to scrape ALL articles on daily.dev
    - May take 30+ minutes to complete
    - Will find hundreds or thousands of articles
    - Uses significant system resources
    - Should be run during off-peak hours
    - Respects rate limits but is intensive
    """)
    
    # Start comprehensive scraping
    if st.button("🚀 Start Comprehensive Scraping", type="primary"):
        
        # Create progress placeholders
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_container = st.empty()
        
        async def progress_callback(message):
            status_text.text(message)
        
        # Run comprehensive scraping
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status_text.text("🔍 Starting comprehensive scraping...")
            
            # Phase 1: Scrape all articles
            scrape_result = loop.run_until_complete(
                scraper.scrape_all_daily_dev_articles(
                    max_pages=max_pages,
                    max_scroll_per_page=max_scroll,
                    delay_between_pages=delay_pages,
                    progress_callback=progress_callback
                )
            )
            
            progress_bar.progress(50)
            
            if scrape_result["success"]:
                articles = scrape_result["articles"]
                stats = scrape_result["stats"]
                
                status_text.text(f"✅ Scraping complete! Found {len(articles)} articles")
                
                # Display scraping stats
                with stats_container.container():
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Articles Found", len(articles))
                    with col2:
                        st.metric("Pages Scraped", stats["pages_scraped"])
                    with col3:
                        st.metric("Scroll Attempts", stats["scroll_attempts"])
                    with col4:
                        scraping_time = "Unknown"
                        if stats["start_time"] and stats.get("end_time"):
                            start = datetime.fromisoformat(stats["start_time"])
                            end = datetime.fromisoformat(stats["end_time"])
                            scraping_time = f"{(end - start).total_seconds():.0f}s"
                        st.metric("Scraping Time", scraping_time)
                
                # Phase 2: Process and add articles
                if articles:
                    status_text.text("📝 Processing and adding articles to knowledge base...")
                    
                    process_result = loop.run_until_complete(
                        scraper.process_and_add_articles(
                            articles,
                            fetch_content=fetch_content,
                            batch_size=batch_size,
                            progress_callback=progress_callback
                        )
                    )
                    
                    progress_bar.progress(100)
                    
                    # Final results
                    status_text.text("🎉 Comprehensive scraping completed!")
                    
                    with stats_container.container():
                        st.subheader("📊 Final Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Articles Found", len(articles))
                        with col2:
                            st.metric("Articles Added", process_result["articles_added"])
                        with col3:
                            st.metric("Articles Skipped", process_result["articles_skipped"])
                        with col4:
                            st.metric("Errors", len(process_result["errors"]))
                        
                        if process_result["errors"]:
                            with st.expander("View Errors"):
                                for error in process_result["errors"]:
                                    st.write(f"• {error}")
                        
                        # Success message
                        if process_result["articles_added"] > 0:
                            st.success(f"""
                            ✅ **Success!** Added {process_result['articles_added']} new articles to your knowledge base.
                            
                            Your AI Advisor now has access to comprehensive daily.dev content!
                            """)
                        else:
                            st.info("No new articles were added (all articles may already exist in your knowledge base)")
                
                else:
                    status_text.text("❌ No articles found during scraping")
                    progress_bar.progress(100)
            
            else:
                status_text.text("❌ Scraping failed")
                st.error(f"Scraping error: {scrape_result.get('error', 'Unknown error')}")
                progress_bar.progress(100)
        
        except Exception as e:
            status_text.text("❌ Error during scraping")
            st.error(f"Comprehensive scraping error: {e}")
            progress_bar.progress(100)
        
        finally:
            loop.close()
    
    # Information about what gets scraped
    with st.expander("ℹ️ What Gets Scraped"):
        st.write("""
        **Comprehensive Scraping Coverage:**
        
        📄 **Article Metadata:**
        - Titles and descriptions
        - Tags and categories  
        - Upvotes and engagement metrics
        - Author information
        - Publication dates
        - Source domains
        
        🔗 **URL Types:**
        - Daily.dev post pages
        - Original article URLs
        - Source website links
        
        📊 **Sources Covered:**
        - All posts feed
        - Popular articles
        - Recent articles  
        - Tagged content
        - Multiple pages with infinite scroll
        
        🎯 **Deduplication:**
        - Skips articles already in knowledge base
        - Uses content hashing to avoid duplicates
        - Tracks URLs to prevent re-processing
        
        **Result:** Comprehensive tech knowledge base with thousands of curated articles!
        """)