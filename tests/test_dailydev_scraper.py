"""
Unit tests for Daily.dev scraper functionality.
"""

import time
import json
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrations.dailydev_scraper import SecureDailyDevScraper, RateLimiter
from integrations.dailydev_auth import DailyDevAuth


class TestRateLimiter(TestCase):
    """Test cases for RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(min_interval=2.0)
        self.assertEqual(limiter.min_interval, 2.0)
        self.assertEqual(limiter.last_request_time, 0)
    
    def test_rate_limiter_no_wait_first_request(self):
        """Test that first request doesn't wait."""
        limiter = RateLimiter(min_interval=1.0)
        
        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()
        
        # Should not wait on first request
        self.assertLess(end_time - start_time, 0.1)
    
    def test_rate_limiter_waits_on_rapid_requests(self):
        """Test that rapid requests are rate limited."""
        limiter = RateLimiter(min_interval=0.5)
        
        # First request
        limiter.wait_if_needed()
        
        # Second request should wait
        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()
        
        # Should have waited approximately the interval
        self.assertGreaterEqual(end_time - start_time, 0.4)


class TestSecureDailyDevScraper(TestCase):
    """Test cases for SecureDailyDevScraper class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock auth
        self.mock_auth = Mock(spec=DailyDevAuth)
        self.mock_auth.is_authenticated.return_value = True
        self.mock_auth.get_auth_cookies.return_value = {'session': 'test_session'}
        self.mock_auth.get_auth_headers.return_value = {'User-Agent': 'test_agent'}
        self.mock_auth.get_session_info.return_value = {
            'authenticated': True,
            'time_remaining': 3600
        }
        
        # Create scraper with mock auth
        self.scraper = SecureDailyDevScraper(self.mock_auth)
    
    def test_scraper_initialization(self):
        """Test scraper initialization."""
        self.assertEqual(self.scraper.auth, self.mock_auth)
        self.assertEqual(self.scraper.base_url, "https://app.daily.dev")
        self.assertEqual(self.scraper.api_url, "https://app.daily.dev/api")
        self.assertIsNotNone(self.scraper.rate_limiter)
        self.assertIsNotNone(self.scraper.session)
        
        # Check stats initialization
        expected_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0
        }
        self.assertEqual(self.scraper.stats, expected_stats)
    
    def test_setup_session_with_auth(self):
        """Test session setup with authentication."""
        # Session should have cookies and headers from auth
        self.mock_auth.get_auth_cookies.assert_called_once()
        self.mock_auth.get_auth_headers.assert_called_once()
        
        # Check that common headers are set
        self.assertIn('Content-Type', self.scraper.session.headers)
        self.assertIn('Accept', self.scraper.session.headers)
    
    def test_setup_session_without_auth(self):
        """Test session setup without authentication."""
        # Create scraper with unauthenticated mock
        unauth_mock = Mock(spec=DailyDevAuth)
        unauth_mock.is_authenticated.return_value = False
        
        scraper = SecureDailyDevScraper(unauth_mock)
        
        # Should not call auth methods
        unauth_mock.get_auth_cookies.assert_not_called()
        unauth_mock.get_auth_headers.assert_not_called()
    
    @patch('requests.Session.post')
    def test_make_graphql_request_success(self, mock_post):
        """Test successful GraphQL request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'test': 'success'}
        }
        mock_post.return_value = mock_response
        
        # Make request
        query = "query Test { test }"
        variables = {'var1': 'value1'}
        
        result = self.scraper._make_graphql_request(query, variables)
        
        # Check result
        self.assertEqual(result, {'data': {'test': 'success'}})
        
        # Check stats
        self.assertEqual(self.scraper.stats['total_requests'], 1)
        self.assertEqual(self.scraper.stats['successful_requests'], 1)
        self.assertEqual(self.scraper.stats['failed_requests'], 0)
        
        # Check request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], self.scraper.graphql_url)
        self.assertEqual(call_args[1]['json']['query'], query)
        self.assertEqual(call_args[1]['json']['variables'], variables)
    
    @patch('requests.Session.post')
    def test_make_graphql_request_with_errors(self, mock_post):
        """Test GraphQL request with GraphQL errors."""
        # Mock response with GraphQL errors
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errors': [{'message': 'Test error'}]
        }
        mock_post.return_value = mock_response
        
        # Make request
        result = self.scraper._make_graphql_request("query Test { test }")
        
        # Should return None due to errors
        self.assertIsNone(result)
        self.assertEqual(self.scraper.stats['failed_requests'], 1)
    
    @patch('requests.Session.post')
    def test_make_graphql_request_http_error(self, mock_post):
        """Test GraphQL request with HTTP error."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Make request
        result = self.scraper._make_graphql_request("query Test { test }")
        
        # Should return None due to HTTP error
        self.assertIsNone(result)
        self.assertEqual(self.scraper.stats['failed_requests'], 1)
    
    @patch('requests.Session.post')
    def test_make_graphql_request_rate_limited(self, mock_post):
        """Test GraphQL request with rate limiting."""
        # Mock rate limited response, then success
        rate_limited_response = Mock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {'Retry-After': '1'}
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'data': {'test': 'success'}}
        
        mock_post.side_effect = [rate_limited_response, success_response]
        
        # Make request (should retry after rate limit)
        with patch('time.sleep') as mock_sleep:
            result = self.scraper._make_graphql_request("query Test { test }")
        
        # Should eventually succeed
        self.assertEqual(result, {'data': {'test': 'success'}})
        self.assertEqual(self.scraper.stats['rate_limited_requests'], 1)
        self.assertEqual(self.scraper.stats['successful_requests'], 1)
        
        # Should have slept for retry (may be called multiple times due to rate limiter)
        self.assertGreater(mock_sleep.call_count, 0)
        # Check that one of the calls was for the retry-after value
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        self.assertIn(1, sleep_calls)
    
    def test_make_graphql_request_unauthenticated(self):
        """Test GraphQL request when not authenticated."""
        # Create scraper with unauthenticated mock
        unauth_mock = Mock(spec=DailyDevAuth)
        unauth_mock.is_authenticated.return_value = False
        
        scraper = SecureDailyDevScraper(unauth_mock)
        
        # Make request
        result = scraper._make_graphql_request("query Test { test }")
        
        # Should return None
        self.assertIsNone(result)
    
    @patch.object(SecureDailyDevScraper, '_make_graphql_request')
    def test_get_feed_articles(self, mock_graphql):
        """Test getting feed articles."""
        # Mock GraphQL response
        mock_response = {
            'data': {
                'page': {
                    'edges': [
                        {
                            'node': {
                                'id': '1',
                                'title': 'Test Article',
                                'permalink': 'https://example.com/article1'
                            }
                        }
                    ]
                }
            }
        }
        mock_graphql.return_value = mock_response
        
        # Get articles
        articles = self.scraper.get_feed_articles(page=0, page_size=10, feed_type="popular")
        
        # Check result
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['node']['title'], 'Test Article')
        
        # Check GraphQL call
        mock_graphql.assert_called_once()
        call_args = mock_graphql.call_args
        self.assertIn('Feed', call_args[0][0])  # Query contains 'Feed'
        
        variables = call_args[0][1]
        self.assertEqual(variables['first'], 10)
        self.assertEqual(variables['ranking'], 'POPULARITY')
    
    @patch.object(SecureDailyDevScraper, '_make_graphql_request')
    def test_search_articles(self, mock_graphql):
        """Test searching articles."""
        # Mock GraphQL response
        mock_response = {
            'data': {
                'search': {
                    'edges': [
                        {
                            'node': {
                                'id': '1',
                                'title': 'Search Result',
                                'permalink': 'https://example.com/search1'
                            }
                        }
                    ]
                }
            }
        }
        mock_graphql.return_value = mock_response
        
        # Search articles
        results = self.scraper.search_articles("test query", limit=5)
        
        # Check result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['node']['title'], 'Search Result')
        
        # Check GraphQL call
        mock_graphql.assert_called_once()
        call_args = mock_graphql.call_args
        self.assertIn('SearchPosts', call_args[0][0])  # Query contains 'SearchPosts'
        
        variables = call_args[0][1]
        self.assertEqual(variables['query'], 'test query')
        self.assertEqual(variables['first'], 5)
    
    @patch.object(SecureDailyDevScraper, '_make_graphql_request')
    def test_get_user_bookmarks(self, mock_graphql):
        """Test getting user bookmarks."""
        # Mock GraphQL response
        mock_response = {
            'data': {
                'bookmarks': {
                    'edges': [
                        {
                            'node': {
                                'id': '1',
                                'title': 'Bookmarked Article',
                                'permalink': 'https://example.com/bookmark1'
                            }
                        }
                    ]
                }
            }
        }
        mock_graphql.return_value = mock_response
        
        # Get bookmarks
        bookmarks = self.scraper.get_user_bookmarks()
        
        # Check result
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0]['node']['title'], 'Bookmarked Article')
        
        # Check GraphQL call
        mock_graphql.assert_called_once()
        call_args = mock_graphql.call_args
        self.assertIn('UserBookmarks', call_args[0][0])  # Query contains 'UserBookmarks'
    
    @patch('requests.Session.get')
    def test_get_article_content(self, mock_get):
        """Test getting article content."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Article content</html>"
        mock_get.return_value = mock_response
        
        # Get content
        content = self.scraper.get_article_content("https://example.com/article")
        
        # Check result
        self.assertEqual(content, "<html>Article content</html>")
        self.assertEqual(self.scraper.stats['successful_requests'], 1)
    
    @patch.object(SecureDailyDevScraper, '_make_graphql_request')
    def test_test_connection_success(self, mock_graphql):
        """Test successful connection test."""
        # Mock successful response
        mock_graphql.return_value = {'data': {'feed': {'edges': []}}}
        
        # Test connection
        result = self.scraper.test_connection()
        
        # Should succeed
        self.assertTrue(result)
        mock_graphql.assert_called_once()
    
    @patch.object(SecureDailyDevScraper, '_make_graphql_request')
    def test_test_connection_failure(self, mock_graphql):
        """Test failed connection test."""
        # Mock failed response
        mock_graphql.return_value = None
        
        # Test connection
        result = self.scraper.test_connection()
        
        # Should fail
        self.assertFalse(result)
    
    def test_get_stats(self):
        """Test getting scraper statistics."""
        # Set some stats
        self.scraper.stats['total_requests'] = 10
        self.scraper.stats['successful_requests'] = 8
        self.scraper.stats['failed_requests'] = 2
        
        # Get stats
        stats = self.scraper.get_stats()
        
        # Check stats
        self.assertEqual(stats['total_requests'], 10)
        self.assertEqual(stats['successful_requests'], 8)
        self.assertEqual(stats['failed_requests'], 2)
        self.assertEqual(stats['success_rate'], 80.0)
        self.assertTrue(stats['authenticated'])
        self.assertIn('session_info', stats)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Set some stats
        self.scraper.stats['total_requests'] = 10
        self.scraper.stats['successful_requests'] = 8
        
        # Reset stats
        self.scraper.reset_stats()
        
        # Check stats are reset
        expected_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0
        }
        self.assertEqual(self.scraper.stats, expected_stats)
    
    def test_refresh_authentication(self):
        """Test refreshing authentication."""
        # Should succeed when authenticated
        result = self.scraper.refresh_authentication()
        self.assertTrue(result)
        
        # Should fail when not authenticated
        self.mock_auth.is_authenticated.return_value = False
        result = self.scraper.refresh_authentication()
        self.assertFalse(result)


if __name__ == '__main__':
    import unittest
    unittest.main()