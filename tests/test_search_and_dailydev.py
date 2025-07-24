"""
Integration tests for Daily.dev MCP server functionality.
"""

import asyncio
import time
from unittest import TestCase
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrations.dailydev_mcp import SecureDailyDevMCPServer, MockKnowledgeBase
from integrations.dailydev_auth import DailyDevAuth
from integrations.dailydev_scraper import SecureDailyDevScraper
from integrations.dailydev_content_processor import DailyDevContentProcessor


class TestMockKnowledgeBase(TestCase):
    """Test cases for MockKnowledgeBase."""
    
    def test_mock_knowledge_base_initialization(self):
        """Test mock knowledge base initialization."""
        kb = MockKnowledgeBase()
        self.assertEqual(len(kb.contents), 0)
    
    def test_add_content(self):
        """Test adding content to mock knowledge base."""
        kb = MockKnowledgeBase()
        
        content_id = kb.add_content(
            "Test content",
            {"title": "Test"},
            "document"
        )
        
        self.assertIsNotNone(content_id)
        self.assertEqual(len(kb.contents), 1)
        self.assertEqual(kb.contents[0]['text_content'], "Test content")
    
    def test_search(self):
        """Test searching mock knowledge base."""
        kb = MockKnowledgeBase()
        
        # Add some content
        kb.add_content("Content 1", {"title": "Test 1"}, "document")
        kb.add_content("Content 2", {"title": "Test 2"}, "document")
        
        # Search
        results = kb.search("test", limit=1)
        self.assertEqual(len(results), 1)
        
        results = kb.search("test", limit=5)
        self.assertEqual(len(results), 2)


class TestSecureDailyDevMCPServer(TestCase):
    """Test cases for SecureDailyDevMCPServer."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_kb = MockKnowledgeBase()
        self.server = SecureDailyDevMCPServer(knowledge_base=self.mock_kb)
        
        # Mock authentication
        self.mock_auth = Mock(spec=DailyDevAuth)
        self.mock_auth.is_authenticated.return_value = True
        self.mock_auth.get_session_info.return_value = {
            'authenticated': True,
            'time_remaining': 3600,
            'credential_timestamp': time.time()
        }
        
        # Mock scraper
        self.mock_scraper = Mock(spec=SecureDailyDevScraper)
        self.mock_scraper.test_connection.return_value = True
        self.mock_scraper.get_stats.return_value = {
            'total_requests': 10,
            'successful_requests': 9,
            'failed_requests': 1,
            'rate_limited_requests': 0,
            'success_rate': 90.0
        }
    
    def test_server_initialization(self):
        """Test server initialization."""
        self.assertIsNotNone(self.server.content_processor)
        self.assertIsNotNone(self.server.knowledge_base)
        self.assertIsNotNone(self.server.stats)
        self.assertFalse(self.server.is_initialized)
        
        # Check initial stats
        self.assertEqual(self.server.stats['total_tool_calls'], 0)
        self.assertEqual(self.server.stats['successful_tool_calls'], 0)
        self.assertEqual(self.server.stats['articles_synced'], 0)
    
    def test_check_authentication(self):
        """Test authentication checking."""
        # Initially not authenticated
        self.assertFalse(self.server._check_authentication())
        
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Now should be authenticated
        self.assertTrue(self.server._check_authentication())
    
    def test_get_server_info(self):
        """Test getting server information."""
        info = self.server.get_server_info()
        
        self.assertEqual(info['server_name'], 'dailydev-mcp-secure')
        self.assertFalse(info['is_initialized'])
        self.assertFalse(info['is_authenticated'])
        self.assertIn('stats', info)
        self.assertIn('uptime_seconds', info)
    
    @patch('integrations.dailydev_mcp.get_auth_from_stored')
    async def test_handle_authenticate_success(self, mock_get_auth):
        """Test successful authentication handling."""
        # Mock successful authentication
        mock_get_auth.return_value = self.mock_auth
        self.server.scraper = self.mock_scraper
        
        # Call authenticate handler
        result = await self.server._handle_authenticate({"password": "test_password"})
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertIn("Authentication successful", result[0].text)
        self.assertTrue(self.server.is_initialized)
        self.assertEqual(self.server.stats['successful_authentications'], 1)
    
    @patch('integrations.dailydev_mcp.get_auth_from_stored')
    async def test_handle_authenticate_failure(self, mock_get_auth):
        """Test failed authentication handling."""
        # Mock failed authentication
        mock_get_auth.return_value = None
        
        # Call authenticate handler
        result = await self.server._handle_authenticate({"password": "wrong_password"})
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertIn("Authentication failed", result[0].text)
        self.assertFalse(self.server.is_initialized)
    
    async def test_handle_authenticate_missing_password(self):
        """Test authentication with missing password."""
        result = await self.server._handle_authenticate({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Password is required", result[0].text)
    
    async def test_handle_test_connection_not_authenticated(self):
        """Test connection test when not authenticated."""
        result = await self.server._handle_test_connection({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Not authenticated", result[0].text)
    
    async def test_handle_test_connection_success(self):
        """Test successful connection test."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        result = await self.server._handle_test_connection({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Connection Test: PASSED", result[0].text)
        self.assertIn("API Access: ✅ Working", result[0].text)
    
    async def test_handle_test_connection_failure(self):
        """Test failed connection test."""
        # Set up authentication but connection fails
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.scraper.test_connection.return_value = False
        self.server.is_initialized = True
        
        result = await self.server._handle_test_connection({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Connection Test: FAILED", result[0].text)
    
    async def test_handle_sync_articles_not_authenticated(self):
        """Test article sync when not authenticated."""
        result = await self.server._handle_sync_articles({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Not authenticated", result[0].text)
    
    async def test_handle_sync_articles_success(self):
        """Test successful article synchronization."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Mock article data
        mock_articles = [
            {
                'node': {
                    'id': 'test_1',
                    'title': 'Test Article 1',
                    'summary': 'Test summary 1',
                    'permalink': 'https://example.com/1',
                    'upvotes': 10,
                    'numComments': 2,
                    'readTime': 5,
                    'tags': ['python'],
                    'createdAt': '2024-01-01T00:00:00Z',
                    'source': {'name': 'TestSource'},
                    'author': {'name': 'TestAuthor'}
                }
            }
        ]
        
        self.server.scraper.get_feed_articles.return_value = mock_articles
        
        # Call sync handler
        result = await self.server._handle_sync_articles({
            "max_articles": 10,
            "feed_types": ["popular"],
            "min_quality": 0.3
        })
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertIn("Article Sync Complete", result[0].text)
        self.assertIn("Articles Added: 1", result[0].text)
        
        # Check knowledge base was updated
        self.assertEqual(len(self.mock_kb.contents), 1)
        
        # Check stats were updated
        self.assertEqual(self.server.stats['articles_synced'], 1)
    
    async def test_handle_search_not_authenticated(self):
        """Test search when not authenticated."""
        result = await self.server._handle_search({"query": "test"})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Not authenticated", result[0].text)
    
    async def test_handle_search_empty_query(self):
        """Test search with empty query."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        result = await self.server._handle_search({"query": ""})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Search query is required", result[0].text)
    
    async def test_handle_search_success(self):
        """Test successful search."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Mock search results
        mock_results = [
            {
                'node': {
                    'id': 'search_1',
                    'title': 'Search Result 1',
                    'summary': 'Search summary 1',
                    'permalink': 'https://example.com/search1',
                    'upvotes': 15,
                    'numComments': 3,
                    'readTime': 7,
                    'tags': ['javascript'],
                    'createdAt': '2024-01-01T00:00:00Z',
                    'source': {'name': 'SearchSource'},
                    'author': {'name': 'SearchAuthor'}
                }
            }
        ]
        
        self.server.scraper.search_articles.return_value = mock_results
        
        # Call search handler
        result = await self.server._handle_search({
            "query": "javascript",
            "limit": 10,
            "min_quality": 0.3
        })
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertIn("Search Complete", result[0].text)
        self.assertIn('Query: "javascript"', result[0].text)
        self.assertIn("Articles Added: 1", result[0].text)
        
        # Check knowledge base was updated
        self.assertEqual(len(self.mock_kb.contents), 1)
        
        # Check search-specific metadata
        added_content = self.mock_kb.contents[0]
        self.assertEqual(added_content['metadata']['search_query'], 'javascript')
        
        # Check stats were updated
        self.assertEqual(self.server.stats['searches_performed'], 1)
    
    async def test_handle_search_no_results(self):
        """Test search with no results."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Mock empty search results
        self.server.scraper.search_articles.return_value = []
        
        result = await self.server._handle_search({"query": "nonexistent"})
        
        self.assertEqual(len(result), 1)
        self.assertIn("No articles found", result[0].text)
    
    async def test_handle_sync_bookmarks_success(self):
        """Test successful bookmark synchronization."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Mock bookmark data
        mock_bookmarks = [
            {
                'node': {
                    'id': 'bookmark_1',
                    'title': 'Bookmarked Article',
                    'summary': 'Bookmark summary',
                    'permalink': 'https://example.com/bookmark1',
                    'upvotes': 20,
                    'numComments': 5,
                    'readTime': 8,
                    'tags': ['react'],
                    'createdAt': '2024-01-01T00:00:00Z',
                    'source': {'name': 'BookmarkSource'},
                    'author': {'name': 'BookmarkAuthor'}
                }
            }
        ]
        
        self.server.scraper.get_user_bookmarks.return_value = mock_bookmarks
        
        # Call bookmark sync handler
        result = await self.server._handle_sync_bookmarks({"min_quality": 0.2})
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertIn("Bookmarks Sync Complete", result[0].text)
        self.assertIn("Bookmarks Added: 1", result[0].text)
        
        # Check knowledge base was updated
        self.assertEqual(len(self.mock_kb.contents), 1)
        
        # Check bookmark-specific metadata
        added_content = self.mock_kb.contents[0]
        self.assertTrue(added_content['metadata']['is_bookmarked'])
        
        # Check stats were updated
        self.assertEqual(self.server.stats['bookmarks_synced'], 1)
    
    async def test_handle_sync_bookmarks_no_bookmarks(self):
        """Test bookmark sync with no bookmarks."""
        # Set up authentication
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        self.server.is_initialized = True
        
        # Mock empty bookmarks
        self.server.scraper.get_user_bookmarks.return_value = []
        
        result = await self.server._handle_sync_bookmarks({})
        
        self.assertEqual(len(result), 1)
        self.assertIn("No bookmarks found", result[0].text)
    
    async def test_handle_get_stats(self):
        """Test getting statistics."""
        # Set up some stats
        self.server.stats['total_tool_calls'] = 10
        self.server.stats['successful_tool_calls'] = 8
        self.server.stats['articles_synced'] = 5
        
        # Set up authentication for additional stats
        self.server.auth = self.mock_auth
        self.server.scraper = self.mock_scraper
        
        result = await self.server._handle_get_stats({
            "include_processing_stats": True,
            "include_scraper_stats": True
        })
        
        self.assertEqual(len(result), 1)
        stats_text = result[0].text
        
        # Check that key statistics are included
        self.assertIn("Integration Statistics", stats_text)
        self.assertIn("Total Tool Calls: 10", stats_text)
        self.assertIn("Successful Calls: 8", stats_text)
        self.assertIn("Articles Synced: 5", stats_text)
        self.assertIn("API Performance", stats_text)
        self.assertIn("Session Info", stats_text)
    
    async def test_handle_get_stats_minimal(self):
        """Test getting minimal statistics."""
        result = await self.server._handle_get_stats({
            "include_processing_stats": False,
            "include_scraper_stats": False
        })
        
        self.assertEqual(len(result), 1)
        stats_text = result[0].text
        
        # Should include basic stats but not processing or scraper stats
        self.assertIn("Integration Statistics", stats_text)
        self.assertIn("Server Status", stats_text)
        self.assertNotIn("Content Processing", stats_text)
        self.assertNotIn("API Performance", stats_text)


class TestMCPServerIntegration(TestCase):
    """Integration tests for MCP server functionality."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.server = SecureDailyDevMCPServer()
    
    def test_server_creation_without_mcp(self):
        """Test server creation when MCP is not available."""
        # Server should still be created but with limited functionality
        self.assertIsNotNone(self.server)
        self.assertIsNotNone(self.server.content_processor)
        self.assertIsNotNone(self.server.knowledge_base)
    
    def test_server_info_structure(self):
        """Test server info structure."""
        info = self.server.get_server_info()
        
        required_keys = [
            'server_name', 'is_initialized', 'is_authenticated',
            'mcp_available', 'stats', 'uptime_seconds'
        ]
        
        for key in required_keys:
            self.assertIn(key, info)
    
    def test_stats_tracking(self):
        """Test that statistics are properly tracked."""
        initial_stats = self.server.stats.copy()
        
        # Simulate some operations
        self.server.stats['total_tool_calls'] += 1
        self.server.stats['successful_tool_calls'] += 1
        self.server.stats['articles_synced'] += 5
        
        # Check stats were updated
        self.assertEqual(
            self.server.stats['total_tool_calls'],
            initial_stats['total_tool_calls'] + 1
        )
        self.assertEqual(
            self.server.stats['articles_synced'],
            initial_stats['articles_synced'] + 5
        )


if __name__ == '__main__':
    import unittest
    unittest.main()