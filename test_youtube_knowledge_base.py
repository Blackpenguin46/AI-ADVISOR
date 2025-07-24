#!/usr/bin/env python3
"""
Unit Tests for YouTube Video Knowledge Base

Tests the original video knowledge base functionality.
"""

import unittest
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_main import SimpleKnowledgeBase


class TestYouTubeKnowledgeBase(unittest.TestCase):
    """Test cases for YouTube video knowledge base."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.kb = SimpleKnowledgeBase()
        
        # Sample test data that mimics YouTube video structure
        self.sample_video_data = {
            "test_video_1": {
                "title": "RAG vs. Fine Tuning",
                "transcript": "This video explains the differences between RAG and fine-tuning for AI models. RAG uses retrieval augmented generation while fine-tuning adjusts model parameters.",
                "author": "IBM Technology",
                "url": "https://www.youtube.com/watch?v=test123"
            },
            "test_video_2": {
                "title": "What are Transformers?",
                "transcript": "Transformers are a type of neural network architecture that uses attention mechanisms for natural language processing tasks.",
                "author": "Google for Developers",
                "url": "https://www.youtube.com/watch?v=test456"
            }
        }
    
    def test_knowledge_base_loads(self):
        """Test that knowledge base loads successfully."""
        self.assertIsNotNone(self.kb.knowledge_db)
        self.assertIsInstance(self.kb.knowledge_db, dict)
        print("✅ Knowledge base loads successfully")
    
    def test_knowledge_base_has_youtube_videos(self):
        """Test that knowledge base contains YouTube videos."""
        youtube_count = 0
        
        for url, video_data in self.kb.knowledge_db.items():
            if ('youtube.com' in url or 
                'IBM Technology' in video_data.get('title', '') or
                video_data.get('title', '').startswith('RAG') or
                'What is' in video_data.get('title', '')):
                youtube_count += 1
        
        self.assertGreater(youtube_count, 0, "Knowledge base should contain YouTube videos")
        print(f"✅ Found {youtube_count} YouTube videos in knowledge base")
    
    def test_search_functionality(self):
        """Test the search functionality works."""
        # Test searching for RAG-related content
        results = self.kb.search_knowledge("RAG", n_results=5)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Search should return results for 'RAG'")
        
        # Check result structure
        if results:
            result = results[0]
            # The actual search returns different structure
            if 'metadata' in result:
                self.assertIn('title', result['metadata'])
                self.assertIn('url', result['metadata'])
            else:
                # Fallback structure check
                self.assertIn('content', result)
        
        print(f"✅ Search functionality works - found {len(results)} results for 'RAG'")
    
    def test_video_content_structure(self):
        """Test that video entries have required structure."""
        video_count = 0
        
        for url, video_data in self.kb.knowledge_db.items():
            if 'youtube.com' in url or 'IBM Technology' in video_data.get('title', ''):
                video_count += 1
                
                # Check required fields
                self.assertIn('title', video_data, f"Video {url} missing title")
                self.assertIsInstance(video_data['title'], str, f"Video {url} title should be string")
                
                # Check optional but expected fields
                if 'transcript' in video_data:
                    self.assertIsInstance(video_data['transcript'], str, f"Video {url} transcript should be string")
                
                if video_count >= 5:  # Test first 5 videos
                    break
        
        self.assertGreater(video_count, 0, "Should find video content to test")
        print(f"✅ Video content structure is valid - tested {video_count} videos")
    
    def test_search_scoring(self):
        """Test that search scoring works correctly."""
        # Search for specific terms
        rag_results = self.kb.search_knowledge("RAG retrieval", n_results=3)
        transformer_results = self.kb.search_knowledge("transformer attention", n_results=3)
        
        # Check that results are scored (if score field exists)
        for results, query in [(rag_results, "RAG"), (transformer_results, "transformer")]:
            if results:
                # Check if results have score field (newer format has 'distance')
                if 'score' in results[0]:
                    scores = [result['score'] for result in results]
                    self.assertEqual(scores, sorted(scores, reverse=True), 
                                   f"Results for '{query}' should be sorted by score")
                    
                    # All scores should be positive
                    for score in scores:
                        self.assertGreater(score, 0, f"Score for '{query}' should be positive")
                elif 'distance' in results[0]:
                    # Distance-based scoring (lower is better)
                    distances = [result['distance'] for result in results]
                    self.assertEqual(distances, sorted(distances), 
                                   f"Results for '{query}' should be sorted by distance")
                else:
                    # Just check that results exist
                    self.assertGreater(len(results), 0, f"Should have results for '{query}'")
        
        print("✅ Search scoring works correctly")
    
    def test_ai_ml_content_coverage(self):
        """Test that knowledge base covers key AI/ML topics."""
        key_topics = [
            "RAG",
            "fine-tuning", 
            "transformer",
            "neural network",
            "machine learning",
            "artificial intelligence",
            "LLM",
            "natural language"
        ]
        
        topic_coverage = {}
        
        for topic in key_topics:
            results = self.kb.search_knowledge(topic, n_results=3)
            topic_coverage[topic] = len(results)
        
        # At least half of the topics should have content
        topics_with_content = sum(1 for count in topic_coverage.values() if count > 0)
        self.assertGreater(topics_with_content, len(key_topics) // 2, 
                          "Should have content for at least half of key AI/ML topics")
        
        print(f"✅ AI/ML content coverage - {topics_with_content}/{len(key_topics)} topics have content")
        for topic, count in topic_coverage.items():
            if count > 0:
                print(f"   {topic}: {count} results")
    
    def test_knowledge_base_size(self):
        """Test that knowledge base has reasonable size."""
        kb_size = len(self.kb.knowledge_db)
        
        self.assertGreater(kb_size, 10, "Knowledge base should have more than 10 entries")
        self.assertLess(kb_size, 1000, "Knowledge base should have less than 1000 entries (sanity check)")
        
        print(f"✅ Knowledge base size is reasonable - {kb_size} total entries")
    
    def test_video_titles_quality(self):
        """Test that video titles are meaningful and descriptive."""
        video_titles = []
        
        for url, video_data in self.kb.knowledge_db.items():
            if 'youtube.com' in url or 'IBM Technology' in video_data.get('title', ''):
                title = video_data.get('title', '')
                if title:
                    video_titles.append(title)
        
        # Check title quality
        for title in video_titles[:10]:  # Test first 10 titles
            self.assertGreater(len(title), 5, f"Title '{title}' should be longer than 5 characters")
            self.assertNotEqual(title.lower(), title, f"Title '{title}' should have proper capitalization")
        
        print(f"✅ Video titles are of good quality - tested {len(video_titles)} titles")


def run_youtube_tests():
    """Run YouTube knowledge base tests."""
    print("🧪 Running YouTube Video Knowledge Base Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestYouTubeKnowledgeBase)
    
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
        print("\n🎉 All YouTube knowledge base tests passed!")
        return True
    else:
        print("\n⚠️ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_youtube_tests()
    sys.exit(0 if success else 1)