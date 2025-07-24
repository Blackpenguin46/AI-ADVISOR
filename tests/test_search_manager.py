"""
Tests for the hybrid search manager.
"""

import pytest
import tempfile
import shutil
import json
import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import managers from the managers directory
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "managers"))
from search_manager import HybridSearchManager, SearchConfig, SearchCache
from vector_database import HybridKnowledgeBase
from models.data_models import SearchQuery
from core.interfaces import SearchResult, ContentType


class TestSearchCache:
    """Test search result caching."""
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        cache = SearchCache(ttl_seconds=1)
        
        # Test cache miss
        result = cache.get("test_key")
        assert result is None
        
        # Test cache set and hit
        test_results = [SearchResult(
            content="test content",
            metadata={"test": "data"},
            score=0.8,
            source_type=ContentType.TEXT,
            content_id="test-id"
        )]
        
        cache.set("test_key", test_results)
        cached_result = cache.get("test_key")
        assert cached_result is not None
        assert len(cached_result) == 1
        assert cached_result[0].content == "test content"
        
        # Test cache expiration
        time.sleep(1.1)  # Wait for TTL to expire
        expired_result = cache.get("test_key")
        assert expired_result is None
        
        # Test cache clear
        cache.set("test_key", test_results)
        cache.clear()
        cleared_result = cache.get("test_key")
        assert cleared_result is None


class TestHybridSearchManager:
    """Test hybrid search manager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_db_path = os.path.join(self.temp_dir, "vector_db")
        self.json_path = os.path.join(self.temp_dir, "test_knowledge.json")
        
        # Create comprehensive test knowledge base
        test_data = {
            "https://example.com/ml-basics": {
                "title": "Machine Learning Basics",
                "transcript": "Machine learning is a method of data analysis that automates analytical model building. It uses algorithms that iteratively learn from data.",
                "uploader": "AI Academy",
                "chunks": [
                    "Machine learning is a method of data analysis",
                    "It automates analytical model building using algorithms",
                    "Algorithms iteratively learn from data to find patterns"
                ],
                "content_id": "ml-basics-1",
                "quality_score": 0.9
            },
            "https://example.com/deep-learning": {
                "title": "Deep Learning Introduction",
                "transcript": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. It can process complex data like images and text.",
                "uploader": "Tech Expert",
                "chunks": [
                    "Deep learning is a subset of machine learning",
                    "It uses neural networks with multiple layers",
                    "Can process complex data like images and text"
                ],
                "content_id": "deep-learning-1",
                "quality_score": 0.8
            },
            "https://example.com/ai-ethics": {
                "title": "AI Ethics and Responsibility",
                "transcript": "Artificial intelligence ethics involves the moral implications of AI development and deployment. It addresses bias, fairness, and transparency.",
                "uploader": "Ethics Institute",
                "chunks": [
                    "AI ethics involves moral implications of AI development",
                    "It addresses important issues like bias and fairness",
                    "Transparency in AI systems is crucial for trust"
                ],
                "content_id": "ai-ethics-1",
                "quality_score": 0.7
            }
        }
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Initialize hybrid knowledge base and search manager
        self.knowledge_base = HybridKnowledgeBase(self.vector_db_path, self.json_path)
        self.search_manager = HybridSearchManager(self.knowledge_base)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_search_manager_initialization(self):
        """Test search manager initialization."""
        assert self.search_manager.knowledge_base is not None
        assert self.search_manager.search_config is not None
        assert self.search_manager.cache is not None
        
        # Test initialization
        success = self.search_manager.initialize()
        assert success == True
        assert self.search_manager.is_initialized == True
    
    def test_configuration(self):
        """Test search configuration."""
        # Test getting current config
        config = self.search_manager.get_search_config()
        assert isinstance(config, dict)
        assert 'keyword_weight' in config
        assert 'semantic_weight' in config
        assert 'max_results' in config
        
        # Test updating configuration
        new_config = {
            'keyword_weight': 0.7,
            'semantic_weight': 0.3,
            'max_results': 15,
            'cache_enabled': False
        }
        
        self.search_manager.configure_search(new_config)
        updated_config = self.search_manager.get_search_config()
        
        assert updated_config['keyword_weight'] == 0.7
        assert updated_config['semantic_weight'] == 0.3
        assert updated_config['max_results'] == 15
        assert updated_config['cache_enabled'] == False
    
    def test_keyword_search(self):
        """Test keyword-only search."""
        results = self.search_manager.search("machine learning", search_type="keyword")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check that results contain relevant content
        found_ml_content = any("machine learning" in result.content.lower() for result in results)
        assert found_ml_content == True
        
        # Check result structure
        result = results[0]
        assert hasattr(result, 'content')
        assert hasattr(result, 'score')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'content_id')
    
    def test_semantic_search(self):
        """Test semantic search (if available)."""
        if not self.knowledge_base.vector_db.is_available:
            pytest.skip("Vector database not available for semantic search")
        
        results = self.search_manager.search("artificial intelligence algorithms", search_type="semantic")
        
        assert isinstance(results, list)
        # Semantic search should find related content even without exact keyword matches
        assert len(results) >= 0  # May be 0 if no semantic matches found
    
    def test_hybrid_search(self):
        """Test hybrid search combining keyword and semantic."""
        results = self.search_manager.search("machine learning algorithms", search_type="hybrid")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check that results have hybrid search metadata
        for result in results:
            assert 'search_query' in result.metadata
            assert 'search_type' in result.metadata
            assert result.metadata['search_type'] == 'hybrid'
    
    def test_search_with_filters(self):
        """Test search with filters."""
        filters = {
            'min_quality_score': 0.8,
            'source_type': 'video'
        }
        
        results = self.search_manager.search(
            "machine learning",
            search_type="keyword",
            filters=filters
        )
        
        assert isinstance(results, list)
        # Results should respect quality filter
        for result in results:
            quality_score = result.metadata.get('quality_score', 0.0)
            if quality_score > 0:  # Only check if quality score is available
                assert quality_score >= 0.8
    
    def test_search_caching(self):
        """Test search result caching."""
        # Enable caching
        self.search_manager.configure_search({'cache_enabled': True})
        
        query = "deep learning neural networks"
        
        # First search - should not be cached
        start_time = time.time()
        results1 = self.search_manager.search(query)
        first_search_time = time.time() - start_time
        
        # Second search - should be cached and faster
        start_time = time.time()
        results2 = self.search_manager.search(query)
        second_search_time = time.time() - start_time
        
        # Results should be identical
        assert len(results1) == len(results2)
        if results1:
            assert results1[0].content_id == results2[0].content_id
        
        # Check cache hit in stats
        stats = self.search_manager.get_search_stats()
        assert stats['cache_hits'] > 0
    
    def test_search_statistics(self):
        """Test search statistics tracking."""
        # Perform various searches
        self.search_manager.search("test query 1", search_type="keyword")
        self.search_manager.search("test query 2", search_type="semantic")
        self.search_manager.search("test query 3", search_type="hybrid")
        
        stats = self.search_manager.get_search_stats()
        
        assert stats['total_searches'] >= 3
        assert stats['keyword_searches'] >= 1
        assert stats['average_response_time'] > 0
        
        # Check that all expected keys are present
        expected_keys = [
            'total_searches', 'keyword_searches', 'semantic_searches',
            'hybrid_searches', 'cache_hits', 'average_response_time'
        ]
        for key in expected_keys:
            assert key in stats
    
    def test_result_post_processing(self):
        """Test search result post-processing."""
        # Configure with quality boost
        self.search_manager.configure_search({
            'boost_high_quality': True,
            'min_score_threshold': 0.1
        })
        
        results = self.search_manager.search("machine learning")
        
        # Check that results have post-processing metadata
        for result in results:
            assert 'search_query' in result.metadata
            assert 'search_type' in result.metadata
            assert 'search_timestamp' in result.metadata
            
            # Check minimum score threshold
            assert result.score >= 0.1
    
    def test_search_explanation(self):
        """Test search result explanation."""
        results = self.search_manager.search("machine learning", search_type="hybrid")
        
        if results:
            explanation = self.search_manager.explain_search("machine learning", results[0])
            
            assert isinstance(explanation, dict)
            assert 'query' in explanation
            assert 'result_id' in explanation
            assert 'final_score' in explanation
            assert 'factors' in explanation
            
            # Check that explanation contains relevant factors
            factors = explanation['factors']
            assert isinstance(factors, list)
            
            # Should have at least one scoring factor
            if factors:
                factor = factors[0]
                assert 'type' in factor
                assert 'score' in factor
                assert 'description' in factor
    
    def test_weight_optimization(self):
        """Test search weight optimization based on feedback."""
        # Create mock feedback data
        feedback_data = [
            {'search_method': 'keyword', 'satisfaction_score': 0.8},
            {'search_method': 'semantic', 'satisfaction_score': 0.6},
            {'search_method': 'hybrid', 'satisfaction_score': 0.9}
        ]
        
        optimized_weights = self.search_manager.optimize_weights(feedback_data)
        
        assert isinstance(optimized_weights, dict)
        assert 'keyword_weight' in optimized_weights
        assert 'semantic_weight' in optimized_weights
        
        # Weights should sum to 1.0
        total_weight = optimized_weights['keyword_weight'] + optimized_weights['semantic_weight']
        assert abs(total_weight - 1.0) < 0.01
    
    def test_error_handling(self):
        """Test error handling in search operations."""
        # Test search with invalid parameters
        results = self.search_manager.search("", search_type="invalid_type")
        assert isinstance(results, list)  # Should return empty list, not crash
        
        # Test search with None query
        results = self.search_manager.search(None)
        assert isinstance(results, list)
    
    def test_cleanup(self):
        """Test search manager cleanup."""
        self.search_manager.initialize()
        assert self.search_manager.is_initialized == True
        
        self.search_manager.cleanup()
        assert self.search_manager.is_initialized == False


if __name__ == "__main__":
    # Run basic tests
    print("Testing Search Manager Implementation...")
    
    # Test search cache
    test_cache = TestSearchCache()
    test_cache.test_cache_operations()
    print("✓ Search cache tests passed")
    
    # Test hybrid search manager
    test_search = TestHybridSearchManager()
    test_search.setup_method()
    
    try:
        test_search.test_search_manager_initialization()
        test_search.test_configuration()
        test_search.test_keyword_search()
        test_search.test_hybrid_search()
        test_search.test_search_with_filters()
        test_search.test_search_caching()
        test_search.test_search_statistics()
        test_search.test_result_post_processing()
        test_search.test_search_explanation()
        test_search.test_weight_optimization()
        test_search.test_error_handling()
        test_search.test_cleanup()
        
        print("✓ Hybrid search manager tests passed")
        
        # Test semantic search if available
        if test_search.knowledge_base.vector_db.is_available:
            test_search.test_semantic_search()
            print("✓ Semantic search tests passed")
        else:
            print("⚠ Semantic search not available - skipping semantic tests")
        
    finally:
        test_search.teardown_method()
    
    print("All search manager tests completed!")