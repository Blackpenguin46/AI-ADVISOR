"""
Secure Daily.dev MCP Server implementation.

This module provides MCP (Model Context Protocol) server functionality
for Daily.dev integration with secure authentication and content processing.
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP library not available. Install with: pip install mcp")
    MCP_AVAILABLE = False
    
    # Create mock classes for development without MCP
    class Server:
        def __init__(self, name: str):
            self.name = name
            self.tools = []
        
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
        
        async def run(self):
            print(f"Mock MCP server {self.name} would run here")
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: Dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

from integrations.dailydev_auth import DailyDevAuth, get_auth_from_stored
from integrations.dailydev_scraper import SecureDailyDevScraper
from integrations.dailydev_content_processor import DailyDevContentProcessor


class MockKnowledgeBase:
    """Mock knowledge base for testing when real one is not available."""
    
    def __init__(self):
        self.contents = []
    
    def add_content(self, text_content: str, metadata: Dict[str, Any], source_type: Any) -> str:
        """Mock add content method."""
        content_id = f"mock_content_{len(self.contents)}"
        self.contents.append({
            'id': content_id,
            'text_content': text_content,
            'metadata': metadata,
            'source_type': source_type
        })
        return content_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Mock search method."""
        return self.contents[:limit]


class SecureDailyDevMCPServer:
    """Secure MCP Server for Daily.dev integration."""
    
    def __init__(self, knowledge_base=None):
        """Initialize the MCP server."""
        self.auth = None
        self.scraper = None
        self.content_processor = DailyDevContentProcessor()
        self.knowledge_base = knowledge_base or MockKnowledgeBase()
        self.server = None
        self.is_initialized = False
        
        # Server statistics
        self.stats = {
            'server_start_time': time.time(),
            'total_tool_calls': 0,
            'successful_tool_calls': 0,
            'failed_tool_calls': 0,
            'authentication_attempts': 0,
            'successful_authentications': 0,
            'articles_synced': 0,
            'searches_performed': 0,
            'bookmarks_synced': 0
        }
        
        if MCP_AVAILABLE:
            self.server = Server("dailydev-mcp-secure")
            self._setup_tools()
    
    def _setup_tools(self):
        """Set up MCP tools with the server."""
        if not self.server:
            return
        
        @self.server.list_tools()
        async def list_tools():
            """List available Daily.dev MCP tools."""
            return [
                Tool(
                    name="authenticate_dailydev",
                    description="Authenticate with Daily.dev using stored encrypted credentials",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "password": {
                                "type": "string",
                                "description": "Password to decrypt stored credentials"
                            }
                        },
                        "required": ["password"]
                    }
                ),
                Tool(
                    name="test_dailydev_connection",
                    description="Test connection to Daily.dev API and authentication status",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="sync_dailydev_articles",
                    description="Sync articles from Daily.dev feeds to knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_articles": {
                                "type": "integer", 
                                "description": "Maximum number of articles to sync",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 200
                            },
                            "feed_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["popular", "recent", "trending"]
                                },
                                "description": "Types of feeds to sync",
                                "default": ["popular"]
                            },
                            "min_quality": {
                                "type": "number",
                                "description": "Minimum quality score for articles (0.0-1.0)",
                                "default": 0.5,
                                "minimum": 0.0,
                                "maximum": 1.0
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
                                "description": "Maximum number of search results to process",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "min_quality": {
                                "type": "number",
                                "description": "Minimum quality score for articles (0.0-1.0)",
                                "default": 0.5,
                                "minimum": 0.0,
                                "maximum": 1.0
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
                        "properties": {
                            "min_quality": {
                                "type": "number",
                                "description": "Minimum quality score for bookmarks (0.0-1.0)",
                                "default": 0.3,
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        }
                    }
                ),
                Tool(
                    name="get_dailydev_stats",
                    description="Get comprehensive statistics about Daily.dev integration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_processing_stats": {
                                "type": "boolean",
                                "description": "Include content processing statistics",
                                "default": True
                            },
                            "include_scraper_stats": {
                                "type": "boolean",
                                "description": "Include scraper performance statistics",
                                "default": True
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Handle MCP tool calls."""
            self.stats['total_tool_calls'] += 1
            
            try:
                if name == "authenticate_dailydev":
                    result = await self._handle_authenticate(arguments)
                elif name == "test_dailydev_connection":
                    result = await self._handle_test_connection(arguments)
                elif name == "sync_dailydev_articles":
                    result = await self._handle_sync_articles(arguments)
                elif name == "search_dailydev":
                    result = await self._handle_search(arguments)
                elif name == "sync_bookmarks":
                    result = await self._handle_sync_bookmarks(arguments)
                elif name == "get_dailydev_stats":
                    result = await self._handle_get_stats(arguments)
                else:
                    result = [TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )]
                
                self.stats['successful_tool_calls'] += 1
                return result
                
            except Exception as e:
                self.stats['failed_tool_calls'] += 1
                error_message = f"❌ Error executing tool '{name}': {str(e)}"
                print(error_message)
                return [TextContent(type="text", text=error_message)]
    
    async def _handle_authenticate(self, arguments: dict) -> List[TextContent]:
        """Handle authentication tool calls."""
        self.stats['authentication_attempts'] += 1
        
        password = arguments.get("password")
        if not password:
            return [TextContent(
                type="text",
                text="❌ Password is required for authentication."
            )]
        
        try:
            # Get authentication from stored credentials
            self.auth = get_auth_from_stored(password)
            
            if not self.auth or not self.auth.is_authenticated():
                return [TextContent(
                    type="text",
                    text="❌ Authentication failed. Please check your password and ensure credentials are set up using the setup script."
                )]
            
            # Initialize scraper with authentication
            self.scraper = SecureDailyDevScraper(self.auth)
            
            # Test the connection
            if self.scraper.test_connection():
                self.is_initialized = True
                self.stats['successful_authentications'] += 1
                
                session_info = self.auth.get_session_info()
                time_remaining = session_info.get('time_remaining', 0)
                hours_remaining = int(time_remaining // 3600)
                
                return [TextContent(
                    type="text",
                    text=f"""✅ Authentication successful!

🔐 **Authentication Status:**
• Status: Authenticated and connected
• Session valid for: ~{hours_remaining} hours
• Daily.dev API: Accessible

🛠️ **Available Tools:**
• `sync_dailydev_articles` - Sync articles from feeds
• `search_dailydev` - Search and add articles
• `sync_bookmarks` - Sync your bookmarks
• `get_dailydev_stats` - View integration statistics
• `test_dailydev_connection` - Test connection

You can now use all Daily.dev MCP tools!"""
                )]
            else:
                return [TextContent(
                    type="text",
                    text="⚠️ Authentication succeeded but connection test failed. Check your network connection and try again."
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Authentication error: {str(e)}\n\nPlease ensure you've run the setup script and have valid credentials stored."
            )]
    
    async def _handle_test_connection(self, arguments: dict) -> List[TextContent]:
        """Handle connection test tool calls."""
        if not self._check_authentication():
            return [TextContent(
                type="text",
                text="❌ Not authenticated. Please use `authenticate_dailydev` tool first."
            )]
        
        try:
            # Test scraper connection
            connection_ok = self.scraper.test_connection()
            
            # Get session info
            session_info = self.auth.get_session_info()
            scraper_stats = self.scraper.get_stats()
            
            if connection_ok:
                time_remaining = session_info.get('time_remaining', 0)
                hours_remaining = int(time_remaining // 3600)
                
                message = f"""✅ **Daily.dev Connection Test: PASSED**

🔗 **Connection Status:**
• API Access: ✅ Working
• Authentication: ✅ Valid
• Session Time Remaining: ~{hours_remaining} hours

📊 **Request Statistics:**
• Total Requests: {scraper_stats['total_requests']}
• Success Rate: {scraper_stats['success_rate']}%
• Rate Limited: {scraper_stats['rate_limited_requests']}

🎯 **Ready for Operations:**
All Daily.dev MCP tools are ready to use!"""
            else:
                message = """❌ **Daily.dev Connection Test: FAILED**

🔗 **Connection Issues Detected:**
• API Access: ❌ Failed
• Possible Causes:
  - Network connectivity issues
  - Authentication expired
  - Daily.dev API temporarily unavailable

🔧 **Troubleshooting:**
1. Check your internet connection
2. Try re-authenticating with `authenticate_dailydev`
3. Verify your credentials are still valid"""
            
            return [TextContent(type="text", text=message)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Connection test failed with error: {str(e)}"
            )]
    
    async def _handle_sync_articles(self, arguments: dict) -> List[TextContent]:
        """Handle article synchronization tool calls."""
        if not self._check_authentication():
            return [TextContent(
                type="text",
                text="❌ Not authenticated. Please use `authenticate_dailydev` tool first."
            )]
        
        max_articles = arguments.get("max_articles", 50)
        feed_types = arguments.get("feed_types", ["popular"])
        min_quality = arguments.get("min_quality", 0.5)
        
        try:
            start_time = time.time()
            total_processed = 0
            total_added = 0
            total_errors = 0
            
            for feed_type in feed_types:
                # Get articles from feed
                articles_per_feed = max_articles // len(feed_types)
                articles = self.scraper.get_feed_articles(
                    page_size=min(articles_per_feed, 50),
                    feed_type=feed_type
                )
                
                if not articles:
                    continue
                
                # Process articles
                for article_edge in articles:
                    if total_processed >= max_articles:
                        break
                    
                    try:
                        article_node = article_edge['node']
                        
                        # Convert to enhanced content
                        content = self.content_processor.convert_article_to_content(article_node)
                        
                        # Filter by quality
                        if content.quality_score < min_quality:
                            continue
                        
                        # Add to knowledge base
                        content_id = self.knowledge_base.add_content(
                            content.text_content,
                            content.metadata,
                            content.source_type
                        )
                        
                        if content_id:
                            total_added += 1
                        
                        total_processed += 1
                        
                    except Exception as e:
                        print(f"Error processing article: {e}")
                        total_errors += 1
            
            # Update stats
            self.stats['articles_synced'] += total_added
            duration = time.time() - start_time
            
            # Get processing stats
            proc_stats = self.content_processor.get_processing_stats()
            
            message = f"""✅ **Daily.dev Article Sync Complete!**

📊 **Sync Results:**
• Articles Processed: {total_processed}
• Articles Added: {total_added}
• Errors: {total_errors}
• Duration: {duration:.1f} seconds
• Average Quality Score: {proc_stats.get('average_quality_score', 0):.2f}

🔍 **Feed Types Synced:**
{', '.join(f'• {feed.title()}' for feed in feed_types)}

⚡ **Performance:**
• Processing Rate: {total_processed/max(duration, 0.1):.1f} articles/sec
• Success Rate: {((total_processed - total_errors) / max(total_processed, 1)) * 100:.1f}%

📚 **Knowledge Base Updated:**
Your AI advisor now has access to the latest Daily.dev articles!"""
            
            return [TextContent(type="text", text=message)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Article sync failed: {str(e)}"
            )]
    
    async def _handle_search(self, arguments: dict) -> List[TextContent]:
        """Handle search tool calls."""
        if not self._check_authentication():
            return [TextContent(
                type="text",
                text="❌ Not authenticated. Please use `authenticate_dailydev` tool first."
            )]
        
        query = arguments.get("query", "")
        limit = arguments.get("limit", 20)
        min_quality = arguments.get("min_quality", 0.5)
        
        if not query.strip():
            return [TextContent(
                type="text",
                text="❌ Search query is required and cannot be empty."
            )]
        
        try:
            start_time = time.time()
            
            # Search articles
            search_results = self.scraper.search_articles(query, limit)
            
            if not search_results:
                return [TextContent(
                    type="text",
                    text=f"🔍 **Search Results for '{query}'**\n\nNo articles found matching your query. Try different keywords or check your spelling."
                )]
            
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
                    content.add_tag(f'query:{query.lower()}')
                    
                    # Filter by quality
                    if content.quality_score < min_quality:
                        articles_processed += 1
                        continue
                    
                    # Add to knowledge base
                    content_id = self.knowledge_base.add_content(
                        content.text_content,
                        content.metadata,
                        content.source_type
                    )
                    
                    if content_id:
                        articles_added += 1
                    
                    articles_processed += 1
                    
                except Exception as e:
                    print(f"Error processing search result: {e}")
                    errors += 1
            
            # Update stats
            self.stats['searches_performed'] += 1
            duration = time.time() - start_time
            
            message = f"""🔍 **Daily.dev Search Complete!**

**Query:** "{query}"

📊 **Search Results:**
• Results Found: {len(search_results)}
• Articles Processed: {articles_processed}
• Articles Added: {articles_added}
• Filtered by Quality: {articles_processed - articles_added}
• Errors: {errors}
• Duration: {duration:.1f} seconds

⚡ **Quality Filter:**
• Minimum Score: {min_quality}
• Articles meeting criteria: {articles_added}/{articles_processed}

📚 **Knowledge Base Updated:**
Relevant articles for "{query}" have been added to your knowledge base!"""
            
            return [TextContent(type="text", text=message)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Search failed: {str(e)}"
            )]
    
    async def _handle_sync_bookmarks(self, arguments: dict) -> List[TextContent]:
        """Handle bookmark synchronization tool calls."""
        if not self._check_authentication():
            return [TextContent(
                type="text",
                text="❌ Not authenticated. Please use `authenticate_dailydev` tool first."
            )]
        
        min_quality = arguments.get("min_quality", 0.3)
        
        try:
            start_time = time.time()
            
            # Get user bookmarks
            bookmarks = self.scraper.get_user_bookmarks()
            
            if not bookmarks:
                return [TextContent(
                    type="text",
                    text="🔖 **Bookmark Sync Complete**\n\nNo bookmarks found in your Daily.dev account. Start bookmarking articles you find interesting!"
                )]
            
            # Process bookmarks
            bookmarks_added = 0
            bookmarks_processed = 0
            errors = 0
            
            for bookmark_edge in bookmarks:
                try:
                    article_node = bookmark_edge['node']
                    
                    # Convert to enhanced content
                    content = self.content_processor.convert_article_to_content(article_node)
                    
                    # Add bookmark-specific metadata and tags
                    content.metadata['is_bookmarked'] = True
                    content.metadata['bookmark_date'] = time.time()
                    content.add_tag('bookmarked')
                    content.add_tag('personal_collection')
                    
                    # Bookmarks have lower quality threshold since they're personally curated
                    if content.quality_score < min_quality:
                        bookmarks_processed += 1
                        continue
                    
                    # Add to knowledge base
                    content_id = self.knowledge_base.add_content(
                        content.text_content,
                        content.metadata,
                        content.source_type
                    )
                    
                    if content_id:
                        bookmarks_added += 1
                    
                    bookmarks_processed += 1
                    
                except Exception as e:
                    print(f"Error processing bookmark: {e}")
                    errors += 1
            
            # Update stats
            self.stats['bookmarks_synced'] += bookmarks_added
            duration = time.time() - start_time
            
            message = f"""🔖 **Daily.dev Bookmarks Sync Complete!**

📊 **Sync Results:**
• Bookmarks Found: {len(bookmarks)}
• Bookmarks Processed: {bookmarks_processed}
• Bookmarks Added: {bookmarks_added}
• Filtered by Quality: {bookmarks_processed - bookmarks_added}
• Errors: {errors}
• Duration: {duration:.1f} seconds

⭐ **Personal Collection:**
Your bookmarked articles have been added with special tags:
• `bookmarked` - Identifies personal bookmarks
• `personal_collection` - Part of your curated content

📚 **Knowledge Base Updated:**
Your personally curated Daily.dev articles are now available to your AI advisor!"""
            
            return [TextContent(type="text", text=message)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Bookmark sync failed: {str(e)}"
            )]
    
    async def _handle_get_stats(self, arguments: dict) -> List[TextContent]:
        """Handle statistics tool calls."""
        include_processing = arguments.get("include_processing_stats", True)
        include_scraper = arguments.get("include_scraper_stats", True)
        
        try:
            # Server uptime
            uptime_seconds = time.time() - self.stats['server_start_time']
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            
            # Build statistics message
            message_parts = [
                "📊 **Daily.dev MCP Integration Statistics**",
                "",
                "🖥️ **Server Status:**",
                f"• Uptime: {uptime_hours}h {uptime_minutes}m",
                f"• Initialized: {'✅ Yes' if self.is_initialized else '❌ No'}",
                f"• Authenticated: {'✅ Yes' if self._check_authentication() else '❌ No'}",
                "",
                "🔧 **Tool Usage:**",
                f"• Total Tool Calls: {self.stats['total_tool_calls']}",
                f"• Successful Calls: {self.stats['successful_tool_calls']}",
                f"• Failed Calls: {self.stats['failed_tool_calls']}",
                f"• Success Rate: {(self.stats['successful_tool_calls'] / max(self.stats['total_tool_calls'], 1)) * 100:.1f}%",
                "",
                "🔐 **Authentication:**",
                f"• Authentication Attempts: {self.stats['authentication_attempts']}",
                f"• Successful Authentications: {self.stats['successful_authentications']}",
                "",
                "📚 **Content Operations:**",
                f"• Articles Synced: {self.stats['articles_synced']}",
                f"• Searches Performed: {self.stats['searches_performed']}",
                f"• Bookmarks Synced: {self.stats['bookmarks_synced']}"
            ]
            
            # Add processing stats if requested
            if include_processing and hasattr(self, 'content_processor'):
                proc_stats = self.content_processor.get_processing_stats()
                message_parts.extend([
                    "",
                    "⚙️ **Content Processing:**",
                    f"• Articles Processed: {proc_stats['articles_processed']}",
                    f"• Processing Errors: {proc_stats['articles_with_errors']}",
                    f"• Average Quality Score: {proc_stats['average_quality_score']:.2f}",
                    f"• Error Rate: {proc_stats['error_rate']:.1f}%"
                ])
            
            # Add scraper stats if requested and available
            if include_scraper and self.scraper:
                scraper_stats = self.scraper.get_stats()
                message_parts.extend([
                    "",
                    "🌐 **API Performance:**",
                    f"• Total API Requests: {scraper_stats['total_requests']}",
                    f"• Successful Requests: {scraper_stats['successful_requests']}",
                    f"• Failed Requests: {scraper_stats['failed_requests']}",
                    f"• Rate Limited Requests: {scraper_stats['rate_limited_requests']}",
                    f"• API Success Rate: {scraper_stats['success_rate']}%"
                ])
                
                # Add session info if authenticated
                if self.auth:
                    session_info = self.auth.get_session_info()
                    time_remaining = session_info.get('time_remaining', 0)
                    hours_remaining = int(time_remaining // 3600)
                    
                    message_parts.extend([
                        "",
                        "🔑 **Session Info:**",
                        f"• Session Valid: {'✅ Yes' if session_info['authenticated'] else '❌ No'}",
                        f"• Time Remaining: ~{hours_remaining} hours",
                        f"• Credential Timestamp: {session_info.get('credential_timestamp', 'Unknown')}"
                    ])
            
            return [TextContent(type="text", text="\n".join(message_parts))]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Failed to get statistics: {str(e)}"
            )]
    
    def _check_authentication(self) -> bool:
        """Check if the server is properly authenticated."""
        return (self.auth is not None and 
                self.auth.is_authenticated() and 
                self.scraper is not None and
                self.is_initialized)
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and status."""
        return {
            'server_name': 'dailydev-mcp-secure',
            'is_initialized': self.is_initialized,
            'is_authenticated': self._check_authentication(),
            'mcp_available': MCP_AVAILABLE,
            'stats': self.stats,
            'uptime_seconds': time.time() - self.stats['server_start_time']
        }
    
    async def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            print("❌ MCP library not available. Cannot start server.")
            print("Install with: pip install mcp")
            return
        
        if not self.server:
            print("❌ Server not initialized.")
            return
        
        print("🚀 Starting Secure Daily.dev MCP Server...")
        print(f"📋 Server Name: dailydev-mcp-secure")
        print(f"🔧 Available Tools: 6")
        print("")
        print("🛠️ **Available Tools:**")
        print("  • authenticate_dailydev - Authenticate with encrypted credentials")
        print("  • test_dailydev_connection - Test Daily.dev API connection")
        print("  • sync_dailydev_articles - Sync articles from feeds")
        print("  • search_dailydev - Search and add articles")
        print("  • sync_bookmarks - Sync personal bookmarks")
        print("  • get_dailydev_stats - View integration statistics")
        print("")
        print("🔐 **Authentication Required:**")
        print("  Before using other tools, authenticate with:")
        print("  authenticate_dailydev(password='your-encryption-password')")
        print("")
        print("✅ Server ready! Connect your MCP client to start using Daily.dev integration.")
        
        # Run the server
        await self.server.run()


# Standalone server runner
async def main():
    """Main function to run the Daily.dev MCP server."""
    # Check if credentials are set up
    from integrations.dailydev_auth import CredentialManager
    
    credential_manager = CredentialManager()
    if not credential_manager.credentials_exist():
        print("⚠️  No credentials found.")
        print("Please run the setup script first to configure your Daily.dev authentication:")
        print("  python secure_dailydev_setup.py")
        return
    
    # Create and run server
    server = SecureDailyDevMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())