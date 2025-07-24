#!/usr/bin/env python3
"""
Daily.dev MCP Server

A standalone MCP server for Daily.dev integration that can be used with Kiro or other MCP clients.
This server provides tools for syncing Daily.dev articles to your knowledge base.
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    MCP_AVAILABLE = True
except ImportError:
    print("MCP library not available. Install with: pip install mcp")
    MCP_AVAILABLE = False

from integrations.dailydev_mcp import SecureDailyDevMCPServer
from managers.vector_database import HybridKnowledgeBase


class DailyDevMCPServer:
    """MCP Server for Daily.dev integration."""
    
    def __init__(self, config_path: str = "dailydev_cookies.json"):
        """Initialize the MCP server."""
        self.config_path = config_path
        self.dailydev_mcp = None
        self.knowledge_base = None
        self.server = None
        
        if MCP_AVAILABLE:
            self.server = Server("dailydev-mcp")
            self._setup_tools()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            print("Run daily_dev_cookie_extractor.py to create the config file")
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _initialize_components(self) -> bool:
        """Initialize Daily.dev MCP and knowledge base."""
        try:
            # Load configuration
            config = self._load_config()
            if not config:
                return False
            
            # Initialize knowledge base
            self.knowledge_base = HybridKnowledgeBase(
                "./data/vector_db", 
                "./knowledge_base_final.json"
            )
            
            # Initialize Daily.dev MCP
            self.dailydev_mcp = DailyDevMCP()
            if not self.dailydev_mcp.initialize(config):
                print("Failed to initialize Daily.dev MCP")
                return False
            
            print("Daily.dev MCP Server initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Error initializing components: {e}")
            return False
    
    def _setup_tools(self):
        """Set up MCP tools."""
        if not self.server:
            return
        
        @self.server.list_tools()
        async def list_tools():
            """List available tools."""
            return [
                Tool(
                    name="sync_dailydev_articles",
                    description="Sync articles from Daily.dev feeds to knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_articles": {
                                "type": "integer", 
                                "description": "Maximum number of articles to sync",
                                "default": 50
                            },
                            "feed_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of feeds to sync (popular, recent, trending)",
                                "default": ["popular"]
                            }
                        }
                    }
                ),
                Tool(
                    name="search_dailydev",
                    description="Search Daily.dev articles and add results to knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for Daily.dev articles"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of search results to add",
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="sync_bookmarks",
                    description="Sync user's Daily.dev bookmarks to knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_dailydev_stats",
                    description="Get statistics about Daily.dev integration and sync status",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="test_dailydev_connection",
                    description="Test connection to Daily.dev and authentication status",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Handle tool calls."""
            # Initialize components if not already done
            if not self.dailydev_mcp or not self.knowledge_base:
                if not self._initialize_components():
                    return [TextContent(
                        type="text", 
                        text="Error: Failed to initialize Daily.dev MCP components. Check your configuration."
                    )]
            
            try:
                if name == "sync_dailydev_articles":
                    return await self._sync_articles(arguments)
                elif name == "search_dailydev":
                    return await self._search_articles(arguments)
                elif name == "sync_bookmarks":
                    return await self._sync_bookmarks(arguments)
                elif name == "get_dailydev_stats":
                    return await self._get_stats(arguments)
                elif name == "test_dailydev_connection":
                    return await self._test_connection(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]
    
    async def _sync_articles(self, arguments: dict) -> List[TextContent]:
        """Sync articles from Daily.dev."""
        max_articles = arguments.get("max_articles", 50)
        feed_types = arguments.get("feed_types", ["popular"])
        
        result = self.dailydev_mcp.sync_articles(
            self.knowledge_base,
            max_articles=max_articles,
            feed_types=feed_types
        )
        
        if result.get("success"):
            message = f"""✅ Daily.dev Article Sync Completed!

📊 Results:
• Articles processed: {result['articles_processed']}
• Articles added: {result['articles_added']}
• Articles updated: {result['articles_updated']}
• Errors: {result['errors']}
• Duration: {result['duration_seconds']:.2f} seconds

🔍 Feed types synced: {', '.join(feed_types)}
📚 Your knowledge base now has the latest Daily.dev articles!"""
        else:
            message = f"❌ Sync failed: {result.get('error', 'Unknown error')}"
        
        return [TextContent(type="text", text=message)]
    
    async def _search_articles(self, arguments: dict) -> List[TextContent]:
        """Search Daily.dev articles."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 20)
        
        if not query:
            return [TextContent(
                type="text",
                text="❌ Error: Search query is required"
            )]
        
        result = self.dailydev_mcp.search_and_add(
            self.knowledge_base,
            query=query,
            limit=limit
        )
        
        if result.get("success"):
            message = f"""🔍 Daily.dev Search Completed!

Query: "{query}"

📊 Results:
• Search results found: {result['search_results']}
• Articles added: {result['articles_added']}
• Errors: {result['errors']}

📚 Relevant articles have been added to your knowledge base!"""
        else:
            message = f"❌ Search failed: {result.get('error', 'Unknown error')}"
        
        return [TextContent(type="text", text=message)]
    
    async def _sync_bookmarks(self, arguments: dict) -> List[TextContent]:
        """Sync user bookmarks."""
        result = self.dailydev_mcp.sync_bookmarks(self.knowledge_base)
        
        if result.get("success"):
            message = f"""🔖 Daily.dev Bookmarks Sync Completed!

📊 Results:
• Bookmarks processed: {result['bookmarks_processed']}
• Articles added: {result['articles_added']}
• Errors: {result['errors']}

📚 Your bookmarked articles are now in your knowledge base!"""
        else:
            message = f"❌ Bookmark sync failed: {result.get('error', 'Unknown error')}"
        
        return [TextContent(type="text", text=message)]
    
    async def _get_stats(self, arguments: dict) -> List[TextContent]:
        """Get Daily.dev integration statistics."""
        context = self.dailydev_mcp.get_context()
        
        if "error" in context:
            return [TextContent(
                type="text",
                text=f"❌ Daily.dev MCP not available: {context['error']}"
            )]
        
        stats = context.get("sync_stats", {})
        
        message = f"""📊 Daily.dev Integration Statistics

🔧 Status:
• Plugin initialized: {context['is_initialized']}
• Last sync: {context.get('last_sync', 'Never')}

📈 Sync Statistics:
• Total articles processed: {stats.get('total_articles_processed', 0)}
• Articles added: {stats.get('articles_added', 0)}
• Articles updated: {stats.get('articles_updated', 0)}
• Errors encountered: {stats.get('errors', 0)}
• Last sync duration: {stats.get('last_sync_duration', 0):.2f} seconds

⚙️ Configuration:
• Has authentication cookies: {context.get('config', {}).get('has_cookies', False)}
• Sync interval: {context.get('config', {}).get('sync_interval', 24)} hours"""
        
        return [TextContent(type="text", text=message)]
    
    async def _test_connection(self, arguments: dict) -> List[TextContent]:
        """Test Daily.dev connection."""
        if not self.dailydev_mcp.is_available():
            return [TextContent(
                type="text",
                text="❌ Daily.dev MCP is not available. Check your configuration and authentication."
            )]
        
        # Try to fetch a small number of articles to test connection
        try:
            test_articles = self.dailydev_mcp.scraper.get_feed_articles(page_size=1)
            
            if test_articles:
                message = """✅ Daily.dev Connection Test Successful!

🔗 Connection Status: Connected
🔐 Authentication: Working
📡 API Access: Available

You can now sync articles, search content, and access your bookmarks."""
            else:
                message = """⚠️ Daily.dev Connection Test Warning

🔗 Connection Status: Connected
🔐 Authentication: May have issues
📡 API Access: Limited or no data returned

Check your cookies and authentication. You may need to refresh your session."""
                
        except Exception as e:
            message = f"""❌ Daily.dev Connection Test Failed

🔗 Connection Status: Failed
🔐 Authentication: Error
📡 API Access: Unavailable

Error: {str(e)}

Please check your configuration and try running the cookie extractor again."""
        
        return [TextContent(type="text", text=message)]
    
    def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            print("MCP library not available. Cannot start server.")
            return
        
        if not self.server:
            print("Server not initialized.")
            return
        
        print("Starting Daily.dev MCP Server...")
        print("Available tools:")
        print("  - sync_dailydev_articles: Sync articles from Daily.dev feeds")
        print("  - search_dailydev: Search and add Daily.dev articles")
        print("  - sync_bookmarks: Sync your Daily.dev bookmarks")
        print("  - get_dailydev_stats: Get integration statistics")
        print("  - test_dailydev_connection: Test Daily.dev connection")
        print()
        print("Server ready! Connect your MCP client to start using Daily.dev integration.")
        
        # Run the server
        asyncio.run(self.server.run())


def main():
    """Main function to run the Daily.dev MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily.dev MCP Server")
    parser.add_argument(
        "--config", 
        default="dailydev_cookies.json",
        help="Path to Daily.dev configuration file"
    )
    
    args = parser.parse_args()
    
    # Create and run server
    server = DailyDevMCPServer(config_path=args.config)
    server.run()


if __name__ == "__main__":
    main()