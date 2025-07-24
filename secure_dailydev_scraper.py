#!/usr/bin/env python3
"""
Secure Daily.dev Scraper

A standalone script to securely scrape Daily.dev articles and add them to your AI Advisor knowledge base.
This script uses encrypted credentials for authentication and works without MCP.
"""

import sys
import getpass
import time
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.dailydev_auth import DailyDevAuth, CredentialManager
from integrations.dailydev_scraper import SecureDailyDevScraper
from integrations.dailydev_content_processor import DailyDevContentProcessor
from integrations.dailydev_mcp import MockKnowledgeBase


class StandaloneDailyDevScraper:
    """Standalone Daily.dev scraper with interactive interface."""
    
    def __init__(self):
        """Initialize the standalone scraper."""
        self.auth = None
        self.scraper = None
        self.content_processor = DailyDevContentProcessor()
        self.knowledge_base = MockKnowledgeBase()
        self.is_authenticated = False
        
        # Statistics
        self.session_stats = {
            'articles_synced': 0,
            'searches_performed': 0,
            'bookmarks_synced': 0,
            'total_articles_processed': 0,
            'session_start_time': time.time()
        }
    
    def print_header(self):
        """Print application header."""
        print("=" * 70)
        print("🔒 SECURE DAILY.DEV SCRAPER")
        print("=" * 70)
        print("Standalone tool for scraping Daily.dev articles with secure authentication")
        print()
    
    def authenticate(self) -> bool:
        """Authenticate with stored credentials."""
        credential_manager = CredentialManager()
        
        if not credential_manager.credentials_exist():
            print("❌ No credentials found.")
            print("Please run 'python secure_dailydev_setup.py' first to set up authentication.")
            return False
        
        print("🔐 Authentication required")
        password = getpass.getpass("Enter password to decrypt Daily.dev credentials: ")
        
        try:
            self.auth = DailyDevAuth()
            if not self.auth.login(password=password):
                print("❌ Authentication failed. Wrong password or invalid credentials.")
                return False
            
            # Initialize scraper
            self.scraper = SecureDailyDevScraper(self.auth)
            
            # Test connection
            print("🧪 Testing connection to Daily.dev...")
            if self.scraper.test_connection():
                print("✅ Authentication successful! Connected to Daily.dev")
                self.is_authenticated = True
                
                # Show session info
                session_info = self.auth.get_session_info()
                time_remaining = session_info.get('time_remaining', 0)
                hours_remaining = int(time_remaining // 3600)
                print(f"⏰ Session valid for ~{hours_remaining} hours")
                return True
            else:
                print("⚠️  Authentication succeeded but connection test failed.")
                print("Check your network connection or try refreshing your credentials.")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def show_main_menu(self):
        """Show the main menu."""
        print("\n" + "=" * 50)
        print("📋 MAIN MENU")
        print("=" * 50)
        print("1. Sync popular articles")
        print("2. Sync recent articles")
        print("3. Sync trending articles")
        print("4. Search for specific topics")
        print("5. Sync your bookmarks")
        print("6. View statistics")
        print("7. Test connection")
        print("8. View knowledge base")
        print("9. Help")
        print("0. Exit")
        print()
    
    def sync_articles(self, feed_type: str, max_articles: int = 50) -> Dict[str, Any]:
        """Sync articles from a specific feed type."""
        if not self.is_authenticated:
            return {"error": "Not authenticated"}
        
        print(f"\n🔄 Syncing {feed_type} articles from Daily.dev...")
        print(f"📊 Maximum articles: {max_articles}")
        
        start_time = time.time()
        
        try:
            # Get articles from feed
            articles = self.scraper.get_feed_articles(
                page_size=min(max_articles, 50),
                feed_type=feed_type
            )
            
            if not articles:
                print(f"⚠️  No {feed_type} articles found.")
                return {"success": False, "message": "No articles found"}
            
            print(f"📥 Found {len(articles)} articles. Processing...")
            
            # Process articles
            articles_added = 0
            articles_processed = 0
            errors = 0
            
            for article_edge in articles:
                try:
                    article_node = article_edge['node']
                    
                    # Convert to enhanced content
                    content = self.content_processor.convert_article_to_content(article_node)
                    
                    # Add to knowledge base
                    content_id = self.knowledge_base.add_content(
                        content.text_content,
                        content.metadata,
                        content.source_type
                    )
                    
                    if content_id:
                        articles_added += 1
                        print(f"  ✅ Added: {content.title[:60]}...")
                    
                    articles_processed += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing article: {e}")
                    errors += 1
            
            # Update stats
            self.session_stats['articles_synced'] += articles_added
            self.session_stats['total_articles_processed'] += articles_processed
            
            duration = time.time() - start_time
            
            print(f"\n✅ Sync complete!")
            print(f"📊 Results:")
            print(f"   • Articles processed: {articles_processed}")
            print(f"   • Articles added: {articles_added}")
            print(f"   • Errors: {errors}")
            print(f"   • Duration: {duration:.1f} seconds")
            
            return {
                "success": True,
                "articles_processed": articles_processed,
                "articles_added": articles_added,
                "errors": errors,
                "duration": duration
            }
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return {"error": str(e)}
    
    def search_articles(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for articles and add them to knowledge base."""
        if not self.is_authenticated:
            return {"error": "Not authenticated"}
        
        print(f"\n🔍 Searching Daily.dev for: '{query}'")
        print(f"📊 Maximum results: {limit}")
        
        start_time = time.time()
        
        try:
            # Search articles
            search_results = self.scraper.search_articles(query, limit)
            
            if not search_results:
                print("⚠️  No articles found matching your query.")
                return {"success": False, "message": "No results found"}
            
            print(f"📥 Found {len(search_results)} results. Processing...")
            
            # Process search results
            articles_added = 0
            articles_processed = 0
            errors = 0
            
            for result_edge in search_results:
                try:
                    article_node = result_edge['node']
                    
                    # Convert to enhanced content
                    content = self.content_processor.convert_article_to_content(article_node)
                    
                    # Add search-specific metadata
                    content.metadata['search_query'] = query
                    content.add_tag('search_result')
                    
                    # Add to knowledge base
                    content_id = self.knowledge_base.add_content(
                        content.text_content,
                        content.metadata,
                        content.source_type
                    )
                    
                    if content_id:
                        articles_added += 1
                        print(f"  ✅ Added: {content.title[:60]}...")
                    
                    articles_processed += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing result: {e}")
                    errors += 1
            
            # Update stats
            self.session_stats['searches_performed'] += 1
            self.session_stats['total_articles_processed'] += articles_processed
            
            duration = time.time() - start_time
            
            print(f"\n✅ Search complete!")
            print(f"📊 Results:")
            print(f"   • Search results: {len(search_results)}")
            print(f"   • Articles processed: {articles_processed}")
            print(f"   • Articles added: {articles_added}")
            print(f"   • Errors: {errors}")
            print(f"   • Duration: {duration:.1f} seconds")
            
            return {
                "success": True,
                "search_results": len(search_results),
                "articles_processed": articles_processed,
                "articles_added": articles_added,
                "errors": errors,
                "duration": duration
            }
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"error": str(e)}
    
    def sync_bookmarks(self) -> Dict[str, Any]:
        """Sync user's bookmarks to knowledge base."""
        if not self.is_authenticated:
            return {"error": "Not authenticated"}
        
        print("\n🔖 Syncing your Daily.dev bookmarks...")
        
        start_time = time.time()
        
        try:
            # Get user bookmarks
            bookmarks = self.scraper.get_user_bookmarks()
            
            if not bookmarks:
                print("⚠️  No bookmarks found in your Daily.dev account.")
                return {"success": False, "message": "No bookmarks found"}
            
            print(f"📥 Found {len(bookmarks)} bookmarks. Processing...")
            
            # Process bookmarks
            bookmarks_added = 0
            bookmarks_processed = 0
            errors = 0
            
            for bookmark_edge in bookmarks:
                try:
                    article_node = bookmark_edge['node']
                    
                    # Convert to enhanced content
                    content = self.content_processor.convert_article_to_content(article_node)
                    
                    # Add bookmark-specific metadata
                    content.metadata['is_bookmarked'] = True
                    content.add_tag('bookmarked')
                    content.add_tag('personal_collection')
                    
                    # Add to knowledge base
                    content_id = self.knowledge_base.add_content(
                        content.text_content,
                        content.metadata,
                        content.source_type
                    )
                    
                    if content_id:
                        bookmarks_added += 1
                        print(f"  ✅ Added: {content.title[:60]}...")
                    
                    bookmarks_processed += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing bookmark: {e}")
                    errors += 1
            
            # Update stats
            self.session_stats['bookmarks_synced'] += bookmarks_added
            self.session_stats['total_articles_processed'] += bookmarks_processed
            
            duration = time.time() - start_time
            
            print(f"\n✅ Bookmark sync complete!")
            print(f"📊 Results:")
            print(f"   • Bookmarks found: {len(bookmarks)}")
            print(f"   • Bookmarks processed: {bookmarks_processed}")
            print(f"   • Bookmarks added: {bookmarks_added}")
            print(f"   • Errors: {errors}")
            print(f"   • Duration: {duration:.1f} seconds")
            
            return {
                "success": True,
                "bookmarks_found": len(bookmarks),
                "bookmarks_processed": bookmarks_processed,
                "bookmarks_added": bookmarks_added,
                "errors": errors,
                "duration": duration
            }
            
        except Exception as e:
            print(f"❌ Bookmark sync failed: {e}")
            return {"error": str(e)}
    
    def show_statistics(self):
        """Show session and scraper statistics."""
        print("\n📊 STATISTICS")
        print("=" * 30)
        
        # Session stats
        session_duration = time.time() - self.session_stats['session_start_time']
        hours = int(session_duration // 3600)
        minutes = int((session_duration % 3600) // 60)
        
        print("🖥️  Session Info:")
        print(f"   • Duration: {hours}h {minutes}m")
        print(f"   • Authenticated: {'✅ Yes' if self.is_authenticated else '❌ No'}")
        print()
        
        print("📚 Content Operations:")
        print(f"   • Articles synced: {self.session_stats['articles_synced']}")
        print(f"   • Searches performed: {self.session_stats['searches_performed']}")
        print(f"   • Bookmarks synced: {self.session_stats['bookmarks_synced']}")
        print(f"   • Total articles processed: {self.session_stats['total_articles_processed']}")
        print()
        
        # Knowledge base stats
        print("🗄️  Knowledge Base:")
        print(f"   • Total items: {len(self.knowledge_base.contents)}")
        print()
        
        # Scraper stats (if available)
        if self.scraper:
            scraper_stats = self.scraper.get_stats()
            print("🌐 API Performance:")
            print(f"   • Total requests: {scraper_stats['total_requests']}")
            print(f"   • Success rate: {scraper_stats['success_rate']}%")
            print(f"   • Rate limited: {scraper_stats['rate_limited_requests']}")
            print()
        
        # Content processing stats
        proc_stats = self.content_processor.get_processing_stats()
        print("⚙️  Content Processing:")
        print(f"   • Articles processed: {proc_stats['articles_processed']}")
        print(f"   • Processing errors: {proc_stats['articles_with_errors']}")
        print(f"   • Average quality: {proc_stats['average_quality_score']:.2f}")
        print(f"   • Error rate: {proc_stats['error_rate']:.1f}%")
    
    def test_connection(self):
        """Test connection to Daily.dev."""
        if not self.is_authenticated:
            print("❌ Not authenticated. Please authenticate first.")
            return
        
        print("\n🧪 Testing connection to Daily.dev...")
        
        if self.scraper.test_connection():
            print("✅ Connection test successful!")
            
            # Show additional info
            session_info = self.auth.get_session_info()
            scraper_stats = self.scraper.get_stats()
            
            time_remaining = session_info.get('time_remaining', 0)
            hours_remaining = int(time_remaining // 3600)
            
            print(f"🔐 Session valid for ~{hours_remaining} hours")
            print(f"📊 API success rate: {scraper_stats['success_rate']}%")
        else:
            print("❌ Connection test failed!")
            print("Check your network connection or try re-authenticating.")
    
    def view_knowledge_base(self):
        """View knowledge base contents."""
        print("\n📚 KNOWLEDGE BASE CONTENTS")
        print("=" * 40)
        
        if not self.knowledge_base.contents:
            print("📭 Knowledge base is empty.")
            print("Use the sync or search options to add content.")
            return
        
        print(f"📊 Total items: {len(self.knowledge_base.contents)}")
        print()
        
        # Show recent items
        recent_items = self.knowledge_base.contents[-10:]  # Last 10 items
        
        print("🕒 Recent items:")
        for i, item in enumerate(recent_items, 1):
            metadata = item.get('metadata', {})
            title = metadata.get('title', 'Untitled')
            source = metadata.get('original_source', 'Unknown')
            
            print(f"   {i:2d}. {title[:50]}{'...' if len(title) > 50 else ''}")
            print(f"       Source: {source}")
        
        if len(self.knowledge_base.contents) > 10:
            print(f"       ... and {len(self.knowledge_base.contents) - 10} more items")
    
    def show_help(self):
        """Show help information."""
        print("\n❓ HELP")
        print("=" * 20)
        print("This tool helps you scrape Daily.dev articles and add them to your knowledge base.")
        print()
        print("🔧 Available Operations:")
        print("   • Sync Articles: Get articles from Daily.dev feeds (popular, recent, trending)")
        print("   • Search: Find articles matching specific topics or keywords")
        print("   • Bookmarks: Sync your personally bookmarked articles")
        print("   • Statistics: View performance and usage statistics")
        print("   • Test Connection: Verify your Daily.dev connection")
        print()
        print("🔐 Authentication:")
        print("   • Your credentials are encrypted and stored locally")
        print("   • You need to authenticate once per session")
        print("   • Sessions typically last 24 hours")
        print()
        print("📚 Knowledge Base:")
        print("   • Articles are processed and stored in a local knowledge base")
        print("   • Quality scoring helps filter high-value content")
        print("   • Metadata and tags are preserved for better searchability")
        print()
        print("🆘 Troubleshooting:")
        print("   • If authentication fails, run 'python secure_dailydev_setup.py'")
        print("   • If connection fails, check your network and try re-authenticating")
        print("   • For expired sessions, simply re-authenticate")
    
    def run(self):
        """Run the interactive scraper."""
        self.print_header()
        
        # Authenticate
        if not self.authenticate():
            return
        
        # Main loop
        while True:
            try:
                self.show_main_menu()
                choice = input("Choose an option [0-9]: ").strip()
                
                if choice == '0':
                    print("\n👋 Goodbye!")
                    break
                
                elif choice == '1':
                    max_articles = input("Maximum articles to sync (default 50): ").strip()
                    max_articles = int(max_articles) if max_articles.isdigit() else 50
                    self.sync_articles("popular", max_articles)
                
                elif choice == '2':
                    max_articles = input("Maximum articles to sync (default 50): ").strip()
                    max_articles = int(max_articles) if max_articles.isdigit() else 50
                    self.sync_articles("recent", max_articles)
                
                elif choice == '3':
                    max_articles = input("Maximum articles to sync (default 50): ").strip()
                    max_articles = int(max_articles) if max_articles.isdigit() else 50
                    self.sync_articles("trending", max_articles)
                
                elif choice == '4':
                    query = input("Enter search query: ").strip()
                    if query:
                        limit = input("Maximum results (default 20): ").strip()
                        limit = int(limit) if limit.isdigit() else 20
                        self.search_articles(query, limit)
                    else:
                        print("❌ Search query cannot be empty.")
                
                elif choice == '5':
                    self.sync_bookmarks()
                
                elif choice == '6':
                    self.show_statistics()
                
                elif choice == '7':
                    self.test_connection()
                
                elif choice == '8':
                    self.view_knowledge_base()
                
                elif choice == '9':
                    self.show_help()
                
                else:
                    print("❌ Invalid choice. Please try again.")
                
                # Pause before showing menu again
                if choice != '0':
                    input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Secure Daily.dev Scraper")
        print()
        print("A standalone tool for scraping Daily.dev articles with secure authentication.")
        print()
        print("Usage:")
        print("  python secure_dailydev_scraper.py")
        print()
        print("Features:")
        print("  • Secure encrypted credential storage")
        print("  • Interactive menu interface")
        print("  • Article syncing from multiple feeds")
        print("  • Search functionality")
        print("  • Bookmark synchronization")
        print("  • Statistics and monitoring")
        print()
        print("Prerequisites:")
        print("  • Run 'python secure_dailydev_setup.py' first to set up authentication")
        print("  • Ensure you have valid Daily.dev credentials")
        return
    
    try:
        scraper = StandaloneDailyDevScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        print("Please check your setup and try again.")


if __name__ == "__main__":
    main()