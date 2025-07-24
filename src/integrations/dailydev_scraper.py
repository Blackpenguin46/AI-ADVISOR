"""
Secure Daily.dev scraper with GraphQL API integration.

This module provides secure methods for scraping Daily.dev content
using authenticated GraphQL requests with rate limiting and error handling.
"""

import json
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .dailydev_auth import DailyDevAuth


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, min_interval: float = 1.0):
        """Initialize rate limiter."""
        self.min_interval = min_interval
        self.last_request_time = 0
    
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class SecureDailyDevScraper:
    """Secure scraper for Daily.dev articles using authenticated requests."""
    
    def __init__(self, auth: DailyDevAuth = None):
        """Initialize the scraper with authentication."""
        self.auth = auth or DailyDevAuth()
        self.session = requests.Session()
        self.base_url = "https://app.daily.dev"
        self.api_url = "https://app.daily.dev/api"
        self.graphql_url = f"{self.api_url}/graphql"
        
        # Rate limiting
        self.rate_limiter = RateLimiter(min_interval=1.0)
        
        # Request statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0
        }
        
        # Apply authentication if available
        self._setup_session()
    
    def _setup_session(self) -> None:
        """Set up the requests session with authentication."""
        if self.auth.is_authenticated():
            self.session.cookies.update(self.auth.get_auth_cookies())
            self.session.headers.update(self.auth.get_auth_headers())
            
            # Add common headers
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': self.base_url,
                'Referer': f"{self.base_url}/"
            })
    
    def _make_graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a GraphQL request with error handling and rate limiting."""
        if not self.auth.is_authenticated():
            print("Not authenticated. Please login first.")
            return None
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Prepare request payload
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            self.stats['total_requests'] += 1
            
            response = self.session.post(
                self.graphql_url,
                json=payload,
                timeout=30
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                self.stats['rate_limited_requests'] += 1
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_graphql_request(query, variables)
            
            if response.status_code == 200:
                self.stats['successful_requests'] += 1
                data = response.json()
                
                # Check for GraphQL errors
                if 'errors' in data:
                    print(f"GraphQL errors: {data['errors']}")
                    self.stats['failed_requests'] += 1
                    return None
                
                return data
            else:
                self.stats['failed_requests'] += 1
                print(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.stats['failed_requests'] += 1
            print("Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.stats['failed_requests'] += 1
            print(f"Failed to parse JSON response: {e}")
            return None
    
    def get_feed_articles(self, page: int = 0, page_size: int = 20, 
                         feed_type: str = "popular") -> List[Dict[str, Any]]:
        """Get articles from Daily.dev feed."""
        # GraphQL query for feed articles
        query = """
        query Feed($first: Int, $after: String, $ranking: Ranking, $supportedTypes: [String!]) {
          page: feed(first: $first, after: $after, ranking: $ranking, supportedTypes: $supportedTypes) {
            edges {
              node {
                id
                title
                permalink
                summary
                createdAt
                readTime
                upvotes
                numComments
                tags
                source {
                  name
                  image
                }
                author {
                  name
                  image
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        # Map feed type to GraphQL ranking
        ranking_map = {
            "popular": "POPULARITY",
            "recent": "TIME",
            "trending": "POPULARITY"  # Fallback to popularity for trending
        }
        
        variables = {
            "first": page_size,
            "after": None if page == 0 else f"page_{page}",
            "ranking": ranking_map.get(feed_type.lower(), "POPULARITY"),
            "supportedTypes": ["article", "video:youtube"]
        }
        
        response = self._make_graphql_request(query, variables)
        
        if response and 'data' in response and 'page' in response['data']:
            return response['data']['page']['edges']
        else:
            print(f"Failed to fetch {feed_type} articles")
            return []
    
    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for articles on Daily.dev."""
        # GraphQL query for search
        search_query = """
        query SearchPosts($query: String!, $first: Int) {
          search: searchPosts(query: $query, first: $first) {
            edges {
              node {
                id
                title
                permalink
                summary
                createdAt
                readTime
                upvotes
                numComments
                tags
                source {
                  name
                  image
                }
                author {
                  name
                  image
                }
              }
            }
          }
        }
        """
        
        variables = {
            "query": query,
            "first": limit
        }
        
        response = self._make_graphql_request(search_query, variables)
        
        if response and 'data' in response and 'search' in response['data']:
            return response['data']['search']['edges']
        else:
            print(f"Search failed for query: {query}")
            return []
    
    def get_user_bookmarks(self) -> List[Dict[str, Any]]:
        """Get user's bookmarked articles."""
        # GraphQL query for bookmarks
        bookmarks_query = """
        query UserBookmarks($first: Int) {
          bookmarks: userBookmarks(first: $first) {
            edges {
              node {
                id
                title
                permalink
                summary
                createdAt
                readTime
                upvotes
                numComments
                tags
                source {
                  name
                  image
                }
                author {
                  name
                  image
                }
              }
            }
          }
        }
        """
        
        variables = {"first": 100}  # Get up to 100 bookmarks
        
        response = self._make_graphql_request(bookmarks_query, variables)
        
        if response and 'data' in response and 'bookmarks' in response['data']:
            return response['data']['bookmarks']['edges']
        else:
            print("Failed to fetch bookmarks")
            return []
    
    def get_article_content(self, article_url: str) -> Optional[str]:
        """Get full article content from URL."""
        if not self.auth.is_authenticated():
            print("Not authenticated. Please login first.")
            return None
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            self.stats['total_requests'] += 1
            
            response = self.session.get(article_url, timeout=30)
            
            if response.status_code == 200:
                self.stats['successful_requests'] += 1
                # This is a simplified content extraction
                # In practice, you might want to use BeautifulSoup or similar
                # to extract the main article content
                return response.text
            else:
                self.stats['failed_requests'] += 1
                print(f"Failed to fetch article content: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            print(f"Error fetching article content: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Daily.dev API."""
        if not self.auth.is_authenticated():
            print("Not authenticated. Cannot test connection.")
            return False
        
        # Simple test query
        test_query = """
        query TestConnection {
          feed(first: 1) {
            edges {
              node {
                id
                title
              }
            }
          }
        }
        """
        
        response = self._make_graphql_request(test_query)
        
        if response and 'data' in response:
            print("✅ Connection test successful!")
            return True
        else:
            print("❌ Connection test failed!")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'authenticated': self.auth.is_authenticated(),
            'session_info': self.auth.get_session_info()
        }
    
    def reset_stats(self) -> None:
        """Reset request statistics."""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0
        }
    
    def refresh_authentication(self) -> bool:
        """Refresh authentication and update session."""
        if self.auth.is_authenticated():
            self._setup_session()
            return True
        else:
            print("Authentication expired. Please login again.")
            return False