"""
Unit tests for Daily.dev content processor.
"""

from unittest import TestCase
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrations.dailydev_content_processor import (
    DailyDevContentProcessor, EnhancedContent, ContentType
)


class TestEnhancedContent(TestCase):
    """Test cases for EnhancedContent class."""
    
    def test_enhanced_content_initialization(self):
        """Test EnhancedContent initialization."""
        content = EnhancedContent(
            title="Test Article",
            text_content="Test content",
            source_url="https://example.com"
        )
        
        self.assertEqual(content.title, "Test Article")
        self.assertEqual(content.text_content, "Test content")
        self.assertEqual(content.source_url, "https://example.com")
        self.assertEqual(content.source_type, ContentType.DOCUMENT)
        self.assertIsNotNone(content.content_id)
        self.assertEqual(content.tags, [])
        self.assertEqual(content.metadata, {})
        self.assertEqual(content.quality_score, 0.0)
    
    def test_add_tag(self):
        """Test adding tags."""
        content = EnhancedContent()
        
        content.add_tag("python")
        self.assertIn("python", content.tags)
        
        # Adding same tag again should not duplicate
        content.add_tag("python")
        self.assertEqual(content.tags.count("python"), 1)
        
        # Adding empty tag should be ignored
        content.add_tag("")
        self.assertNotIn("", content.tags)
    
    def test_remove_tag(self):
        """Test removing tags."""
        content = EnhancedContent()
        content.add_tag("python")
        content.add_tag("javascript")
        
        content.remove_tag("python")
        self.assertNotIn("python", content.tags)
        self.assertIn("javascript", content.tags)
        
        # Removing non-existent tag should not error
        content.remove_tag("nonexistent")
    
    def test_has_tag(self):
        """Test checking for tags."""
        content = EnhancedContent()
        content.add_tag("python")
        
        self.assertTrue(content.has_tag("python"))
        self.assertFalse(content.has_tag("javascript"))
    
    def test_get_summary(self):
        """Test getting summary from metadata."""
        content = EnhancedContent()
        content.metadata['summary'] = "Test summary"
        
        self.assertEqual(content.get_summary(), "Test summary")
        
        # Should return empty string if no summary
        content.metadata = {}
        self.assertEqual(content.get_summary(), "")
    
    def test_get_author(self):
        """Test getting author from metadata."""
        content = EnhancedContent()
        content.metadata['author'] = "John Doe"
        
        self.assertEqual(content.get_author(), "John Doe")
        
        # Should return 'Unknown' if no author
        content.metadata = {}
        self.assertEqual(content.get_author(), "Unknown")
    
    def test_get_source(self):
        """Test getting source from metadata."""
        content = EnhancedContent()
        content.metadata['original_source'] = "TechCrunch"
        
        self.assertEqual(content.get_source(), "TechCrunch")
        
        # Should return 'daily.dev' if no original source
        content.metadata = {}
        self.assertEqual(content.get_source(), "daily.dev")


class TestDailyDevContentProcessor(TestCase):
    """Test cases for DailyDevContentProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        self.processor = DailyDevContentProcessor()
        
        # Sample article node for testing
        self.sample_article = {
            'id': 'test_id_123',
            'title': 'Test Article Title',
            'summary': 'This is a test article summary',
            'permalink': 'https://example.com/test-article',
            'upvotes': 25,
            'numComments': 5,
            'readTime': 8,
            'tags': ['python', 'web-development', 'tutorial'],
            'createdAt': '2024-01-15T10:30:00Z',
            'source': {
                'name': 'TechCrunch',
                'image': 'https://example.com/techcrunch.png'
            },
            'author': {
                'name': 'John Doe',
                'image': 'https://example.com/johndoe.png'
            }
        }
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        self.assertEqual(self.processor.processing_stats['articles_processed'], 0)
        self.assertEqual(self.processor.processing_stats['articles_with_errors'], 0)
        self.assertEqual(self.processor.processing_stats['average_quality_score'], 0.0)
    
    def test_convert_article_to_content(self):
        """Test converting article to content."""
        content = self.processor.convert_article_to_content(self.sample_article)
        
        # Check basic properties
        self.assertEqual(content.title, 'Test Article Title')
        self.assertEqual(content.source_url, 'https://example.com/test-article')
        self.assertEqual(content.source_type, ContentType.DOCUMENT)
        self.assertGreater(content.quality_score, 0.5)  # Should have decent quality
        
        # Check metadata
        self.assertEqual(content.metadata['dailydev_id'], 'test_id_123')
        self.assertEqual(content.metadata['upvotes'], 25)
        self.assertEqual(content.metadata['comments_count'], 5)
        self.assertEqual(content.metadata['reading_time'], 8)
        self.assertEqual(content.metadata['author'], 'John Doe')
        self.assertEqual(content.metadata['original_source'], 'TechCrunch')
        
        # Check tags
        self.assertIn('python', content.tags)
        self.assertIn('web-development', content.tags)
        self.assertIn('daily.dev', content.tags)
        self.assertIn('tech_article', content.tags)
        self.assertIn('popular', content.tags)  # 25 upvotes should be popular
        self.assertIn('discussed', content.tags)  # 5 comments should be discussed
        self.assertIn('medium_read', content.tags)  # 8 min should be medium read
        
        # Check text content includes key information
        self.assertIn('Test Article Title', content.text_content)
        self.assertIn('This is a test article summary', content.text_content)
        self.assertIn('John Doe', content.text_content)
        self.assertIn('TechCrunch', content.text_content)
        self.assertIn('python, web-development, tutorial', content.text_content)
    
    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        # Test high quality article
        high_quality_article = {
            'upvotes': 100,
            'numComments': 25,
            'readTime': 15
        }
        score = self.processor._calculate_quality_score(high_quality_article)
        self.assertGreater(score, 0.8)
        
        # Test medium quality article
        medium_quality_article = {
            'upvotes': 15,
            'numComments': 3,
            'readTime': 5
        }
        score = self.processor._calculate_quality_score(medium_quality_article)
        self.assertGreater(score, 0.5)
        self.assertLess(score, 0.8)
        
        # Test low quality article
        low_quality_article = {
            'upvotes': 1,
            'numComments': 0,
            'readTime': 1
        }
        score = self.processor._calculate_quality_score(low_quality_article)
        self.assertLess(score, 0.6)
        
        # Test article with no engagement
        no_engagement_article = {}
        score = self.processor._calculate_quality_score(no_engagement_article)
        self.assertEqual(score, 0.5)  # Base score
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        metadata = self.processor._extract_metadata(self.sample_article)
        
        # Check required fields
        self.assertEqual(metadata['dailydev_id'], 'test_id_123')
        self.assertEqual(metadata['url'], 'https://example.com/test-article')
        self.assertEqual(metadata['summary'], 'This is a test article summary')
        self.assertEqual(metadata['upvotes'], 25)
        self.assertEqual(metadata['comments_count'], 5)
        self.assertEqual(metadata['reading_time'], 8)
        self.assertEqual(metadata['source'], 'daily.dev')
        self.assertEqual(metadata['original_source'], 'TechCrunch')
        self.assertEqual(metadata['author'], 'John Doe')
        
        # Check date parsing
        self.assertIn('publication_date', metadata)
        self.assertEqual(metadata['publication_year'], 2024)
        self.assertEqual(metadata['publication_month'], 1)
    
    def test_add_tags(self):
        """Test tag addition logic."""
        content = EnhancedContent()
        self.processor._add_tags(content, self.sample_article)
        
        # Check article tags are added
        self.assertIn('python', content.tags)
        self.assertIn('web-development', content.tags)
        self.assertIn('tutorial', content.tags)
        
        # Check default tags
        self.assertIn('daily.dev', content.tags)
        self.assertIn('tech_article', content.tags)
        
        # Check source tag
        self.assertIn('source:techcrunch', content.tags)
        
        # Check engagement tags
        self.assertIn('popular', content.tags)  # 25 upvotes
        self.assertIn('discussed', content.tags)  # 5 comments
        
        # Check reading time tag
        self.assertIn('medium_read', content.tags)  # 8 minutes
    
    def test_batch_process_articles(self):
        """Test batch processing of articles."""
        articles = [self.sample_article, self.sample_article.copy()]
        articles[1]['id'] = 'test_id_456'
        articles[1]['title'] = 'Second Test Article'
        
        processed = self.processor.batch_process_articles(articles)
        
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0].title, 'Test Article Title')
        self.assertEqual(processed[1].title, 'Second Test Article')
        self.assertEqual(self.processor.processing_stats['articles_processed'], 2)
    
    def test_filter_by_quality(self):
        """Test filtering by quality score."""
        # Create content with different quality scores
        high_quality = EnhancedContent(title="High", quality_score=0.8)
        medium_quality = EnhancedContent(title="Medium", quality_score=0.6)
        low_quality = EnhancedContent(title="Low", quality_score=0.4)
        
        contents = [high_quality, medium_quality, low_quality]
        
        # Filter with minimum quality 0.6
        filtered = self.processor.filter_by_quality(contents, min_quality=0.6)
        
        self.assertEqual(len(filtered), 2)
        self.assertIn(high_quality, filtered)
        self.assertIn(medium_quality, filtered)
        self.assertNotIn(low_quality, filtered)
    
    def test_filter_by_tags(self):
        """Test filtering by tags."""
        python_content = EnhancedContent(title="Python")
        python_content.add_tag("python")
        
        js_content = EnhancedContent(title="JavaScript")
        js_content.add_tag("javascript")
        
        both_content = EnhancedContent(title="Both")
        both_content.add_tag("python")
        both_content.add_tag("javascript")
        
        contents = [python_content, js_content, both_content]
        
        # Filter for required tags
        python_filtered = self.processor.filter_by_tags(contents, required_tags=["python"])
        self.assertEqual(len(python_filtered), 2)  # python_content and both_content
        
        # Filter with excluded tags
        no_js_filtered = self.processor.filter_by_tags(contents, excluded_tags=["javascript"])
        self.assertEqual(len(no_js_filtered), 1)  # only python_content
    
    def test_detect_duplicates(self):
        """Test duplicate detection."""
        # Create content with same URL
        content1 = EnhancedContent(title="Article 1", source_url="https://example.com/same")
        content2 = EnhancedContent(title="Article 2", source_url="https://example.com/same")
        
        # Create content with same title
        content3 = EnhancedContent(title="Same Title", source_url="https://example.com/diff1")
        content4 = EnhancedContent(title="Same Title", source_url="https://example.com/diff2")
        
        # Create unique content
        content5 = EnhancedContent(title="Unique", source_url="https://example.com/unique")
        
        contents = [content1, content2, content3, content4, content5]
        duplicates = self.processor.detect_duplicates(contents)
        
        self.assertEqual(len(duplicates), 2)  # Two duplicate groups
        
        # Check URL duplicates
        url_group = next((group for group in duplicates if content1 in group), None)
        self.assertIsNotNone(url_group)
        self.assertIn(content2, url_group)
        
        # Check title duplicates
        title_group = next((group for group in duplicates if content3 in group), None)
        self.assertIsNotNone(title_group)
        self.assertIn(content4, title_group)
    
    def test_merge_duplicate_content(self):
        """Test merging duplicate content."""
        # Create duplicates with different quality scores
        low_quality = EnhancedContent(title="Article", quality_score=0.3)
        low_quality.add_tag("tag1")
        
        high_quality = EnhancedContent(title="Article", quality_score=0.8)
        high_quality.add_tag("tag2")
        
        duplicates = [low_quality, high_quality]
        merged = self.processor.merge_duplicate_content(duplicates)
        
        # Should keep the higher quality version
        self.assertEqual(merged.quality_score, 0.8)
        
        # Should merge tags from both
        self.assertIn("tag1", merged.tags)
        self.assertIn("tag2", merged.tags)
        
        # Should add duplicate metadata
        self.assertEqual(merged.metadata['duplicate_count'], 2)
        self.assertIn('merged_from', merged.metadata)
    
    def test_get_processing_stats(self):
        """Test getting processing statistics."""
        # Process some articles to generate stats
        self.processor.convert_article_to_content(self.sample_article)
        
        stats = self.processor.get_processing_stats()
        
        self.assertEqual(stats['articles_processed'], 1)
        self.assertEqual(stats['articles_with_errors'], 0)
        self.assertGreater(stats['average_quality_score'], 0)
        self.assertEqual(stats['error_rate'], 0.0)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Process an article to generate stats
        self.processor.convert_article_to_content(self.sample_article)
        self.assertGreater(self.processor.processing_stats['articles_processed'], 0)
        
        # Reset stats
        self.processor.reset_stats()
        
        self.assertEqual(self.processor.processing_stats['articles_processed'], 0)
        self.assertEqual(self.processor.processing_stats['articles_with_errors'], 0)
        self.assertEqual(self.processor.processing_stats['average_quality_score'], 0.0)
    
    def test_error_handling(self):
        """Test error handling in article processing."""
        # Create malformed article that will cause errors
        malformed_article = None
        
        content = self.processor.convert_article_to_content(malformed_article)
        
        # Should return error content
        self.assertIn("Error Processing Article", content.title)
        self.assertEqual(content.quality_score, 0.0)
        self.assertEqual(content.processing_method, 'dailydev_content_processor_error')
        self.assertEqual(self.processor.processing_stats['articles_with_errors'], 1)


if __name__ == '__main__':
    import unittest
    unittest.main()