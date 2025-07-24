#!/usr/bin/env python3
"""
Simple Daily.dev Scraper

A standalone script to scrape Daily.dev articles and add them to your AI Advisor knowledge base.
This script works without MCP and can be run directly.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.dailydev_mcp import DailyDevMCP
from managers.vector_database import HybridKnowledgeBase


def load_config(config_path: str = "dailydev_cookies.json") -> dict:
    """Load Daily.dev configuration."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        print("Run: python daily_dev_cookie_extractor.py")
        return {}
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}


def main():
    """Main function to scrape Daily.dev articles."""
    print("🚀 Simple Daily.dev Scraper")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Initialize knowledge base
    print("📚 Initializing knowledge base...")
    knowledge_base = HybridKnowledgeBase(
        "./data/vector_db", 
        "./knowledge_base_final.json"
    )
    
    # Initialize Daily.dev MCP
    print("🔗 Connecting to Daily.dev...")
    dailydev_mcp = DailyDevMCP()
    
    if not dailydev_mcp.initialize(config):
        print("❌ Failed to initialize Daily.dev connection")
        print("Check your cookies and configuration")
        return
    
    print("✅ Connected to Daily.dev successfully!")
    
    # Menu for user actions
    while True:
        print("\n" + "=" * 50)
        print("📋 What would you like to do?")
        print("1. Sync popular articles")
        print("2. Sync recent articles") 
        print("3. Sync your bookmarks")
        print("4. Search for specific topics")
        print("5. Get sync statistics")
        print("6. Test connection")
        print("0. Exit")
        print("=" * 50)
        
        choice = input("Enter your choice (0-6): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
            
        elif choice == "1":
            print("\n🔥 Syncing popular articles...")
            max_articles = input("How many articles? (default: 50): ").strip()
            max_articles = int(max_articles) if max_articles.isdigit() else 50
            
            result = dailydev_mcp.sync_articles(
                knowledge_base,
                max_articles=max_articles,
                feed_types=["popular"]
            )
            
            if result.get("success"):
                print(f"✅ Success! Added {result['articles_added']} articles in {result['duration_seconds']:.1f}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "2":
            print("\n🆕 Syncing recent articles...")
            max_articles = input("How many articles? (default: 50): ").strip()
            max_articles = int(max_articles) if max_articles.isdigit() else 50
            
            result = dailydev_mcp.sync_articles(
                knowledge_base,
                max_articles=max_articles,
                feed_types=["recent"]
            )
            
            if result.get("success"):
                print(f"✅ Success! Added {result['articles_added']} articles in {result['duration_seconds']:.1f}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "3":
            print("\n🔖 Syncing your bookmarks...")
            result = dailydev_mcp.sync_bookmarks(knowledge_base)
            
            if result.get("success"):
                print(f"✅ Success! Added {result['articles_added']} bookmarked articles")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "4":
            print("\n🔍 Search Daily.dev articles...")
            query = input("Enter search query: ").strip()
            if not query:
                print("❌ Search query cannot be empty")
                continue
                
            limit = input("How many results? (default: 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            
            result = dailydev_mcp.search_and_add(knowledge_base, query, limit)
            
            if result.get("success"):
                print(f"✅ Success! Added {result['articles_added']} articles for '{query}'")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "5":
            print("\n📊 Daily.dev Integration Statistics")
            context = dailydev_mcp.get_context()
            
            if "error" in context:
                print(f"❌ Error: {context['error']}")
                continue
            
            stats = context.get("sync_stats", {})
            print(f"• Total articles processed: {stats.get('total_articles_processed', 0)}")
            print(f"• Articles added: {stats.get('articles_added', 0)}")
            print(f"• Articles updated: {stats.get('articles_updated', 0)}")
            print(f"• Errors: {stats.get('errors', 0)}")
            print(f"• Last sync duration: {stats.get('last_sync_duration', 0):.2f}s")
            print(f"• Last sync: {context.get('last_sync', 'Never')}")
        
        elif choice == "6":
            print("\n🔧 Testing Daily.dev connection...")
            
            if dailydev_mcp.is_available():
                try:
                    # Test by fetching one article
                    test_articles = dailydev_mcp.scraper.get_feed_articles(page_size=1)
                    if test_articles:
                        print("✅ Connection test successful!")
                        print("🔐 Authentication is working")
                        print("📡 API access is available")
                    else:
                        print("⚠️  Connection established but no articles returned")
                        print("🔐 Authentication may have issues")
                except Exception as e:
                    print(f"❌ Connection test failed: {e}")
            else:
                print("❌ Daily.dev MCP is not available")
        
        else:
            print("❌ Invalid choice. Please enter 0-6.")


if __name__ == "__main__":
    main()