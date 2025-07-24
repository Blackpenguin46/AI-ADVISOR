"""
Daily.dev integration for AI Advisor.
Connects with the Daily.dev MCP server to automatically ingest articles.
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import streamlit as st
from pathlib import Path

# MCP client imports
try:
    import mcp
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioClientTransport
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .unified_knowledge_base import UnifiedKnowledgeBase

logger = logging.getLogger(__name__)


class DailyDevMCPClient:
    """Client for interacting with the Daily.dev MCP server."""
    
    def __init__(self, mcp_server_path: str = None):
        self.mcp_server_path = mcp_server_path or "daily_dev_mcp_server.py"
        self.session = None
        self.transport = None
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        if not MCP_AVAILABLE:
            logger.error("MCP client not available. Install with: pip install mcp")
            return False
        
        try:
            # Create transport to the MCP server
            self.transport = StdioClientTransport(
                command=["python", self.mcp_server_path],
                stderr_handler=lambda data: logger.info(f"MCP Server: {data.decode()}")
            )
            
            # Create session
            self.session = ClientSession(self.transport)
            await self.session.initialize()
            
            logger.info("Successfully connected to Daily.dev MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.close()
            except:
                pass
        if self.transport:
            try:
                await self.transport.close()
            except:
                pass
    
    async def get_daily_dev_articles(self, limit: int = 20, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """Get articles from daily.dev."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "get_daily_dev_links",
                {
                    "limit": limit,
                    "include_metadata": include_metadata
                }
            )
            
            # Parse the JSON response
            response_data = json.loads(result.content[0].text)
            
            if response_data.get("status") == "success":
                return response_data.get("articles", [])
            else:
                logger.error(f"MCP server error: {response_data.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting articles from MCP server: {e}")
            return []
    
    async def search_daily_dev(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search daily.dev for specific content."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "search_daily_dev",
                {
                    "query": query,
                    "limit": limit
                }
            )
            
            response_data = json.loads(result.content[0].text)
            
            if response_data.get("status") == "success":
                return response_data.get("articles", [])
            else:
                logger.error(f"Search error: {response_data.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching daily.dev: {e}")
            return []
    
    async def get_article_content(self, url: str) -> Optional[str]:
        """Get full content from an article URL."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "get_article_content",
                {
                    "url": url,
                    "include_summary": False
                }
            )
            
            response_data = json.loads(result.content[0].text)
            
            if response_data.get("status") == "success":
                return response_data.get("content")
            else:
                logger.error(f"Content fetch error: {response_data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting article content: {e}")
            return None


class DailyDevIntegration:
    """Integration layer between Daily.dev MCP and AI Advisor knowledge base."""
    
    def __init__(self, knowledge_base: UnifiedKnowledgeBase, mcp_server_path: str = None):
        self.kb = knowledge_base
        self.mcp_client = DailyDevMCPClient(mcp_server_path)
        self.last_sync = None
        self.sync_history = []
    
    async def sync_articles(self, limit: int = 20, fetch_content: bool = False) -> Dict[str, Any]:
        """Sync articles from daily.dev to the knowledge base."""
        
        sync_result = {
            "success": False,
            "articles_fetched": 0,
            "articles_added": 0,
            "articles_skipped": 0,
            "errors": []
        }
        
        try:
            # Connect to MCP server
            if not await self.mcp_client.connect():
                sync_result["errors"].append("Failed to connect to MCP server")
                return sync_result
            
            # Get articles from daily.dev
            articles = await self.mcp_client.get_daily_dev_articles(limit=limit)
            sync_result["articles_fetched"] = len(articles)
            
            if not articles:
                sync_result["errors"].append("No articles retrieved from daily.dev")
                return sync_result
            
            # Process each article
            for article in articles:
                try:
                    # Check if article already exists
                    article_url = article.get('url') or article.get('daily_dev_url')
                    if not article_url:
                        sync_result["articles_skipped"] += 1
                        continue
                    
                    # Check if we already have this article
                    existing_resources = self.kb.get_all_resources()
                    if any(meta.get('source_url') == article_url for meta in existing_resources.values()):
                        sync_result["articles_skipped"] += 1
                        continue
                    
                    # Prepare article data
                    title = article.get('title', 'Daily.dev Article')
                    author = article.get('author', {}).get('name', 'Daily.dev')
                    tags = ['daily.dev', 'tech', 'programming'] + article.get('tags', [])
                    
                    # Get full content if requested
                    content = ""
                    if fetch_content and article_url:
                        try:
                            content = await self.mcp_client.get_article_content(article_url)
                            if not content:
                                content = f"Article from daily.dev: {title}"
                        except Exception as e:
                            logger.warning(f"Failed to fetch content for {article_url}: {e}")
                            content = f"Article from daily.dev: {title}\n\nFailed to fetch full content."
                    else:
                        # Use available metadata as content
                        content_parts = [f"Title: {title}"]
                        if article.get('tags'):
                            content_parts.append(f"Tags: {', '.join(article['tags'])}")
                        if article.get('upvotes'):
                            content_parts.append(f"Upvotes: {article['upvotes']}")
                        if article.get('comments'):
                            content_parts.append(f"Comments: {article['comments']}")
                        content = "\n".join(content_parts)
                    
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
                        sync_result["articles_added"] += 1
                    else:
                        sync_result["articles_skipped"] += 1
                        sync_result["errors"].append(f"Failed to add article: {title}")
                
                except Exception as e:
                    sync_result["articles_skipped"] += 1
                    sync_result["errors"].append(f"Error processing article: {str(e)}")
                    continue
            
            # Update sync history
            self.last_sync = datetime.now()
            self.sync_history.append({
                "timestamp": self.last_sync.isoformat(),
                "result": sync_result
            })
            
            # Keep only last 10 sync records
            self.sync_history = self.sync_history[-10:]
            
            sync_result["success"] = True
            
        except Exception as e:
            sync_result["errors"].append(f"Sync failed: {str(e)}")
            
        finally:
            await self.mcp_client.disconnect()
        
        return sync_result
    
    async def search_and_add_articles(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search daily.dev and add matching articles to knowledge base."""
        
        search_result = {
            "success": False,
            "query": query,
            "articles_found": 0,
            "articles_added": 0,
            "errors": []
        }
        
        try:
            if not await self.mcp_client.connect():
                search_result["errors"].append("Failed to connect to MCP server")
                return search_result
            
            # Search for articles
            articles = await self.mcp_client.search_daily_dev(query, limit)
            search_result["articles_found"] = len(articles)
            
            # Add articles to knowledge base
            for article in articles:
                try:
                    article_url = article.get('url') or article.get('daily_dev_url')
                    if not article_url:
                        continue
                    
                    # Check if already exists
                    existing_resources = self.kb.get_all_resources()
                    if any(meta.get('source_url') == article_url for meta in existing_resources.values()):
                        continue
                    
                    title = article.get('title', 'Daily.dev Search Result')
                    tags = ['daily.dev', 'search', query.lower()] + article.get('tags', [])
                    
                    # Create content from available data
                    content = f"Title: {title}\nSearch Query: {query}\n"
                    if article.get('tags'):
                        content += f"Tags: {', '.join(article['tags'])}\n"
                    
                    success = self.kb.add_resource(
                        source=content,
                        source_type='url',
                        title=title,
                        author='Daily.dev Search',
                        description=f"Search result for '{query}' from daily.dev",
                        tags=tags
                    )
                    
                    if success:
                        search_result["articles_added"] += 1
                
                except Exception as e:
                    search_result["errors"].append(f"Error adding search result: {str(e)}")
                    continue
            
            search_result["success"] = True
            
        except Exception as e:
            search_result["errors"].append(f"Search failed: {str(e)}")
            
        finally:
            await self.mcp_client.disconnect()
        
        return search_result
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status and history."""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_history": self.sync_history,
            "mcp_available": MCP_AVAILABLE
        }


def create_daily_dev_interface(knowledge_base: UnifiedKnowledgeBase):
    """Create Streamlit interface for Daily.dev integration."""
    
    st.header("📰 Daily.dev Integration")
    
    if not MCP_AVAILABLE:
        st.error("MCP client not available. Install with: `pip install mcp`")
        st.info("This feature requires the Model Context Protocol client to connect to the Daily.dev scraper.")
        return
    
    # Initialize integration
    if 'daily_dev_integration' not in st.session_state:
        st.session_state.daily_dev_integration = DailyDevIntegration(knowledge_base)
    
    integration = st.session_state.daily_dev_integration
    
    # Status section
    st.subheader("📊 Sync Status")
    
    status = integration.get_sync_status()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if status["last_sync"]:
            last_sync = datetime.fromisoformat(status["last_sync"])
            st.metric("Last Sync", last_sync.strftime("%Y-%m-%d %H:%M"))
        else:
            st.metric("Last Sync", "Never")
    
    with col2:
        st.metric("Sync History", len(status["sync_history"]))
    
    with col3:
        mcp_status = "✅ Available" if status["mcp_available"] else "❌ Not Available"
        st.metric("MCP Status", mcp_status)
    
    # Sync controls
    st.subheader("🔄 Sync Articles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sync_limit = st.slider("Number of articles to sync", 5, 50, 20)
        fetch_content = st.checkbox("Fetch full article content (slower)", value=False)
    
    with col2:
        st.write("**Sync Options:**")
        st.write("• Basic sync: metadata only (fast)")
        st.write("• Full content: complete articles (slow)")
        st.write("• Automatic deduplication")
    
    if st.button("🚀 Sync Now", type="primary"):
        with st.spinner("Syncing articles from daily.dev..."):
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    integration.sync_articles(sync_limit, fetch_content)
                )
                
                if result["success"]:
                    st.success(f"✅ Sync completed! Added {result['articles_added']} new articles")
                    if result["articles_skipped"] > 0:
                        st.info(f"Skipped {result['articles_skipped']} articles (duplicates or errors)")
                else:
                    st.error("❌ Sync failed")
                
                if result["errors"]:
                    with st.expander("View Errors"):
                        for error in result["errors"]:
                            st.write(f"• {error}")
                            
            except Exception as e:
                st.error(f"Sync error: {e}")
            finally:
                loop.close()
    
    # Search and add
    st.subheader("🔍 Search & Add Articles")
    
    search_query = st.text_input("Search daily.dev for specific topics:", 
                               placeholder="react, python, machine learning...")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_limit = st.slider("Max search results", 5, 25, 10)
    
    with col2:
        if st.button("🔍 Search & Add") and search_query:
            with st.spinner(f"Searching for '{search_query}'..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        integration.search_and_add_articles(search_query, search_limit)
                    )
                    
                    if result["success"]:
                        st.success(f"Found {result['articles_found']} articles, added {result['articles_added']} new ones")
                    else:
                        st.error("Search failed")
                        
                    if result["errors"]:
                        with st.expander("View Errors"):
                            for error in result["errors"]:
                                st.write(f"• {error}")
                                
                except Exception as e:
                    st.error(f"Search error: {e}")
                finally:
                    loop.close()
    
    # Sync history
    if status["sync_history"]:
        st.subheader("📈 Recent Sync History")
        
        for sync in reversed(status["sync_history"][-5:]):  # Show last 5
            timestamp = datetime.fromisoformat(sync["timestamp"])
            result = sync["result"]
            
            with st.expander(f"Sync: {timestamp.strftime('%Y-%m-%d %H:%M')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Fetched", result["articles_fetched"])
                with col2:
                    st.metric("Added", result["articles_added"])
                with col3:
                    st.metric("Skipped", result["articles_skipped"])
                
                if result["errors"]:
                    st.write("**Errors:**")
                    for error in result["errors"]:
                        st.write(f"• {error}")
    
    # Setup instructions
    with st.expander("🛠️ Setup Instructions"):
        st.write("""
        **To use Daily.dev integration:**
        
        1. **Install MCP client:**
           ```bash
           pip install mcp
           ```
        
        2. **Save your MCP server code** as `daily_dev_mcp_server.py` in the same directory as this app
        
        3. **Install MCP server dependencies:**
           ```bash
           pip install selenium webdriver-manager beautifulsoup4 httpx fastmcp
           ```
        
        4. **Configure Chrome WebDriver:**
           - The server will automatically download ChromeDriver
           - Make sure Chrome browser is installed
        
        5. **Start syncing!** Use the buttons above to sync articles from daily.dev
        
        **Features:**
        - Automatic deduplication
        - Metadata extraction (tags, upvotes, comments)
        - Full content fetching (optional)
        - Search-based article discovery
        - Sync history tracking
        """)