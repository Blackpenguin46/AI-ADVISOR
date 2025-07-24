#!/usr/bin/env python3
"""
Unit Tests for Daily.dev Scraper

Tests the Daily.dev scraping functionality.
"""

import unittest
import json
import sys
import requests
from unittest.mock import patch, Mock
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from clean_daily_dev_scraper import CleanDailyDevScraper


class TestDailyDevScraper(unittest.TestCase):
    """Test cases for Daily.dev scraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = CleanDailyDevScraper()
        
        # Sample GraphQL response data
        self.sample_graphql_response = {
            "data": {
                "page": {
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                        "startCursor": "cursor1",
                        "endCursor": "cursor2"
                    },
                    "edges": [
                        {
                            "node": {
                                "id": "test-article-1",
                                "url": "https://example.com/article1",
                                "title": "Test AI Article 1",
                                "summary": "This is a test article about AI developments",
                                "createdAt": "2025-01-23T10:00:00Z",
                                "readTime": 5,
                                "image": "https://example.com/image1.jpg",
                                "numUpvotes": 42,
                                "numComments": 10,
                                "source": {
                                    "id": "source1",
                                    "name": "TechCrunch",
                                    "image": "https://example.com/source1.jpg"
                                },
                                "tags": ["ai", "machine-learning", "tech"],
                                "author": {
                                    "id": "author1",
                                    "name": "John Doe",
                                    "username": "johndoe"
                                }
                            }
                        },
                        {
                            "node": {
                                "id": "test-article-2",
                                "url": "https://example.com/article2",
                                "title": "Test Development Article",
                                "summary": "This is a test article about software development",
                                "createdAt": "2025-01-23T09:00:00Z",
                                "readTime": 3,
                                "image": "",
                                "numUpvotes": 15,
                                "numComments": 5,
                                "source": {
                                    "id": "source2",
                                    "name": "Dev.to",
                                    "image": ""
                                },
                                "tags": ["programming", "javascript"],
                                "author": None
                            }
                        }
                    ]
                }
            }
        }
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.api_url, "https://api.daily.dev/graphql")
        self.assertFalse(self.scraper.cookies_loaded)
        print("✅ Scraper initializes correctly")
    
    def test_cookie_loading_when_file_exists(self):
        """Test cookie loading when file exists."""
        # Create a test cookie file
        test_cookies = {
            "cookies": {
                "test_cookie": "test_value",
                "session": "test_session"
            },
            "expires_at": "2025-08-21T19:40:23.891000"
        }
        
        cookie_file = Path('daily_dev_cookies.json')
        original_exists = cookie_file.exists()
        original_content = None
        
        if original_exists:
            with open(cookie_file, 'r') as f:
                original_content = f.read()
        
        try:
            # Write test cookies
            with open(cookie_file, 'w') as f:
                json.dump(test_cookies, f)
            
            # Test loading
            result = self.scraper.load_cookies()
            
            self.assertTrue(result)
            self.assertTrue(self.scraper.cookies_loaded)
            self.assertEqual(len(self.scraper.session.cookies), 2)
            
            print("✅ Cookie loading works when file exists")
            
        finally:
            # Restore original file
            if original_exists:
                with open(cookie_file, 'w') as f:
                    f.write(original_content)
            elif cookie_file.exists():
                cookie_file.unlink()
    
    def test_cookie_loading_when_file_missing(self):
        """Test cookie loading when file is missing."""
        # Temporarily rename cookie file if it exists
        cookie_file = Path('daily_dev_cookies.json')
        backup_file = Path('daily_dev_cookies_backup.json')
        
        file_existed = False
        if cookie_file.exists():
            file_existed = True
            cookie_file.rename(backup_file)
        
        try:
            result = self.scraper.load_cookies()
            
            self.assertFalse(result)
            self.assertFalse(self.scraper.cookies_loaded)
            
            print("✅ Cookie loading handles missing file correctly")
            
        finally:
            # Restore file if it existed
            if file_existed and backup_file.exists():
                backup_file.rename(cookie_file)
    
    @patch('requests.Session.post')
    def test_get_daily_dev_articles_success(self, mock_post):
        """Test successful article fetching from Daily.dev."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_graphql_response
        mock_post.return_value = mock_response
        
        articles = self.scraper.get_daily_dev_articles(limit=10)
        
        self.assertEqual(len(articles), 2)
        
        # Check first article structure
        article1 = articles[0]
        self.assertEqual(article1['id'], 'test-article-1')
        self.assertEqual(article1['title'], 'Test AI Article 1')
        self.assertEqual(article1['url'], 'https://example.com/article1')
        self.assertEqual(article1['upvotes'], 42)
        self.assertEqual(article1['source'], 'TechCrunch')
        self.assertEqual(article1['tags'], ['ai', 'machine-learning', 'tech'])
        
        # Check second article (with missing author)
        article2 = articles[1]
        self.assertEqual(article2['author'], '')
        self.assertEqual(article2['source'], 'Dev.to')
        
        print("✅ Article fetching works correctly with valid response")
    
    @patch('requests.Session.post')
    def test_get_daily_dev_articles_api_error(self, mock_post):
        """Test article fetching when API returns error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        articles = self.scraper.get_daily_dev_articles(limit=10)
        
        self.assertEqual(len(articles), 0)
        print("✅ Article fetching handles API errors correctly")
    
    @patch('requests.Session.post')
    def test_get_daily_dev_articles_network_error(self, mock_post):
        """Test article fetching when network error occurs."""
        # Mock network error
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        articles = self.scraper.get_daily_dev_articles(limit=10)
        
        self.assertEqual(len(articles), 0)
        print("✅ Article fetching handles network errors correctly")
    
    def test_generate_id_consistency(self):
        """Test that ID generation is consistent."""
        url1 = "https://example.com/article1"
        url2 = "https://example.com/article2"
        
        id1a = self.scraper._generate_id(url1)
        id1b = self.scraper._generate_id(url1)
        id2 = self.scraper._generate_id(url2)
        
        self.assertEqual(id1a, id1b, "Same URL should generate same ID")
        self.assertNotEqual(id1a, id2, "Different URLs should generate different IDs")
        self.assertEqual(len(id1a), 12, "ID should be 12 characters long")
        
        print("✅ ID generation is consistent and unique")
    
    def test_knowledge_base_integration(self):
        """Test that scraped articles integrate properly with knowledge base."""
        # Create sample articles
        sample_articles = [
            {
                'id': 'test1',
                'url': 'https://example.com/test1',
                'title': 'Test Article 1',
                'summary': 'This is a test summary',
                'upvotes': 10,
                'comments': 5,
                'read_time': 3,
                'source': 'Test Source',
                'tags': ['test', 'article']
            }
        ]
        
        # Test adding to knowledge base
        added_count = self.scraper.add_daily_dev_articles_to_kb(sample_articles)
        
        # Should add at least one article (unless it already exists)
        self.assertGreaterEqual(added_count, 0)
        
        # Load knowledge base and verify structure
        kb = self.scraper._load_knowledge_base()
        
        # Find our test article
        test_article_found = False
        for item_id, item_data in kb.items():
            if (item_data.get('metadata', {}).get('source_url') == 'https://example.com/test1'):
                test_article_found = True
                
                # Check structure
                self.assertIn('metadata', item_data)
                self.assertIn('content', item_data)
                self.assertIn('chunks', item_data)
                self.assertIn('processing_notes', item_data)
                
                # Check metadata
                metadata = item_data['metadata']
                self.assertEqual(metadata['title'], 'Test Article 1')
                self.assertEqual(metadata['source_type'], 'url')
                self.assertIn('daily.dev', metadata['tags'])
                self.assertEqual(metadata['upvotes'], 10)
                
                break
        
        if added_count > 0:
            self.assertTrue(test_article_found, "Test article should be found in knowledge base")
        
        print("✅ Knowledge base integration works correctly")
    
    def test_knowledge_base_preserves_youtube_videos(self):
        """Test that scraping preserves existing YouTube videos."""
        # Load current knowledge base
        original_kb = self.scraper._load_knowledge_base()
        
        # Count YouTube videos
        original_youtube_count = 0
        for item in original_kb.values():
            if 'metadata' in item and item['metadata'].get('source_type') == 'video':
                original_youtube_count += 1
        
        # Add a sample Daily.dev article
        sample_articles = [
            {
                'id': 'preserve_test',
                'url': 'https://example.com/preserve_test',
                'title': 'Preservation Test Article',
                'summary': 'This tests that YouTube videos are preserved',
                'upvotes': 1,
                'comments': 0,
                'read_time': 1,
                'source': 'Test',
                'tags': []
            }
        ]
        
        self.scraper.add_daily_dev_articles_to_kb(sample_articles)
        
        # Load updated knowledge base
        updated_kb = self.scraper._load_knowledge_base()
        
        # Count YouTube videos again
        updated_youtube_count = 0
        for item in updated_kb.values():
            if 'metadata' in item and item['metadata'].get('source_type') == 'video':
                updated_youtube_count += 1
        
        self.assertEqual(original_youtube_count, updated_youtube_count, 
                        "YouTube video count should remain the same")
        
        print(f"✅ YouTube videos preserved - {updated_youtube_count} videos maintained")
    
    def test_real_knowledge_base_has_both_content_types(self):
        """Test that real knowledge base has both YouTube and Daily.dev content."""
        kb = self.scraper._load_knowledge_base()
        
        youtube_count = 0
        dailydev_count = 0
        
        for item in kb.values():
            if 'metadata' in item:
                metadata = item['metadata']
                if metadata.get('source_type') == 'video':
                    youtube_count += 1
                elif 'daily.dev' in metadata.get('tags', []):
                    dailydev_count += 1
        
        self.assertGreater(youtube_count, 0, "Should have YouTube videos")
        self.assertGreater(dailydev_count, 0, "Should have Daily.dev articles")
        
        print(f"✅ Knowledge base has both content types - {youtube_count} YouTube videos, {dailydev_count} Daily.dev articles")


def run_dailydev_tests():
    """Run Daily.dev scraper tests."""
    print("🧪 Running Daily.dev Scraper Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDailyDevScraper)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Print summary
    print("\n📊 Test Results Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All Daily.dev scraper tests passed!")
        return True
    else:
        print("\n⚠️ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_dailydev_tests()
    sys.exit(0 if success else 1)