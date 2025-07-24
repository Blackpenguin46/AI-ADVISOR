"""
Hybrid search manager that combines keyword and semantic search with configurable weights.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import ISearchManager, SearchResult, BaseManager
# Import HybridKnowledgeBase - will be defined in the same file for now
# This will be refactored when the module structure is finalized
from models.data_models import SearchQuery


class SearchType(Enum):
    """Types of search available."""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class SearchConfig:
    """Configuration for search behavior."""
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6
    max_results: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    min_score_threshold: float = 0.1
    boost_recent_content: bool = True
    boost_high_quality: bool = True


class SearchCache:
    """Simple in-memory cache for search results."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[List[SearchResult], float]] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, query_key: str) -> Optional[List[SearchResult]]:
        """Get cached results if still valid."""
        if query_key in self.cache:
            results, timestamp = self.cache[query_key]
            if time.time() - timestamp < self.ttl_seconds:
                return results
            else:
                # Remove expired entry
                del self.cache[query_key]
        return None
    
    def set(self, query_key: str, results: List[SearchResult]) -> None:
        """Cache search results."""
        self.cache[query_key] = (results, time.time())
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
    
    def _generate_key(self, query: str, search_type: str, filters: Dict[str, Any]) -> str:
        """Generate cache key from query parameters."""
        import hashlib
        key_data = f"{query}:{search_type}:{str(sorted(filters.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()


class HybridSearchManager(ISearchManager, BaseManager):
    """Advanced search manager with hybrid capabilities."""
    
    def __init__(self, knowledge_base: HybridKnowledgeBase, config: Dict[str, Any] = None):
        """Initialize hybrid search manager."""
        super().__init__(config)
        self.knowledge_base = knowledge_base
        self.search_config = SearchConfig()
        self.cache = SearchCache()
        self._configure_from_dict(config or {})
        self.search_stats = {
            'total_searches': 0,
            'keyword_searches': 0,
            'semantic_searches': 0,
            'hybrid_searches': 0,
            'cache_hits': 0,
            'average_response_time': 0.0
        }
    
    def _configure_from_dict(self, config: Dict[str, Any]) -> None:
        """Configure search manager from dictionary."""
        if 'keyword_weight' in config:
            self.search_config.keyword_weight = config['keyword_weight']
        if 'semantic_weight' in config:
            self.search_config.semantic_weight = config['semantic_weight']
        if 'max_results' in config:
            self.search_config.max_results = config['max_results']
        if 'cache_enabled' in config:
            self.search_config.enable_caching = config['cache_enabled']
        if 'cache_ttl_seconds' in config:
            self.search_config.cache_ttl_seconds = config['cache_ttl_seconds']
            self.cache.ttl_seconds = config['cache_ttl_seconds']
    
    def initialize(self) -> bool:
        """Initialize the search manager."""
        try:
            # Validate configuration
            total_weight = self.search_config.keyword_weight + self.search_config.semantic_weight
            if abs(total_weight - 1.0) > 0.01:
                print(f"Warning: Search weights don't sum to 1.0 (sum={total_weight})")
                # Normalize weights
                self.search_config.keyword_weight /= total_weight
                self.search_config.semantic_weight /= total_weight
            
            self.is_initialized = True
            return True
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error("search_init_error", e, {"component": "search_manager"})
            return False
    
    def cleanup(self) -> None:
        """Cleanup search manager resources."""
        self.cache.clear()
        self.is_initialized = False
    
    def search(self, query: str, search_type: str = "hybrid", **kwargs) -> List[SearchResult]:
        """Perform search with specified type and configuration."""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        try:
            # Create search query object
            search_query = SearchQuery(
                query_text=query,
                search_type=search_type,
                max_results=kwargs.get('max_results', self.search_config.max_results),
                filters=kwargs.get('filters', {}),
                weights={
                    'keyword': self.search_config.keyword_weight,
                    'semantic': self.search_config.semantic_weight
                },
                user_id=kwargs.get('user_id'),
                project_id=kwargs.get('project_id')
            )
            
            # Check cache if enabled
            cache_key = None
            if self.search_config.enable_caching:
                cache_key = self.cache._generate_key(query, search_type, search_query.filters)
                cached_results = self.cache.get(cache_key)
                if cached_results:
                    self.search_stats['cache_hits'] += 1
                    return cached_results
            
            # Perform search based on type
            results = self._execute_search(search_query)
            
            # Apply post-processing
            results = self._post_process_results(results, search_query)
            
            # Cache results if enabled
            if self.search_config.enable_caching and cache_key:
                self.cache.set(cache_key, results)
            
            # Update statistics
            self._update_search_stats(search_type, time.time() - start_time)
            
            return results
            
        except Exception as e:
            if self.error_handler:
                return self.error_handler.handle_error("search_error", e, {
                    "query": query,
                    "search_type": search_type,
                    "kwargs": kwargs
                }) or []
            else:
                print(f"Search error: {e}")
                return []
    
    def _execute_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Execute the actual search based on query type."""
        if search_query.search_type == SearchType.KEYWORD.value:
            return self.knowledge_base.search(
                search_query.query_text,
                n_results=search_query.max_results,
                search_type="keyword",
                filters=search_query.filters
            )
        
        elif search_query.search_type == SearchType.SEMANTIC.value:
            return self.knowledge_base.search(
                search_query.query_text,
                n_results=search_query.max_results,
                search_type="semantic",
                filters=search_query.filters
            )
        
        elif search_query.search_type == SearchType.HYBRID.value:
            return self._hybrid_search(search_query)
        
        else:
            # Default to hybrid search
            search_query.search_type = SearchType.HYBRID.value
            return self._hybrid_search(search_query)
    
    def _hybrid_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining keyword and semantic results."""
        # Get results from both search methods
        keyword_results = self.knowledge_base.search(
            search_query.query_text,
            n_results=search_query.max_results,
            search_type="keyword",
            filters=search_query.filters
        )
        
        semantic_results = self.knowledge_base.search(
            search_query.query_text,
            n_results=search_query.max_results,
            search_type="semantic",
            filters=search_query.filters
        )
        
        # Combine and rerank results
        return self._combine_search_results(
            keyword_results,
            semantic_results,
            search_query.weights['keyword'],
            search_query.weights['semantic'],
            search_query.max_results
        )
    
    def _combine_search_results(self, keyword_results: List[SearchResult], 
                               semantic_results: List[SearchResult],
                               keyword_weight: float, semantic_weight: float,
                               max_results: int) -> List[SearchResult]:
        """Combine and rerank results from different search methods."""
        # Create a map to track results by content_id
        combined_results = {}
        
        # Process keyword results
        for result in keyword_results:
            combined_results[result.content_id] = result
            # Store original keyword score
            result.metadata['keyword_score'] = result.score
            result.score *= keyword_weight
        
        # Process semantic results
        for result in semantic_results:
            if result.content_id in combined_results:
                # Combine scores for content that appears in both
                existing_result = combined_results[result.content_id]
                existing_result.metadata['semantic_score'] = result.score
                existing_result.score += result.score * semantic_weight
                # Update metadata to indicate hybrid result
                existing_result.metadata['search_method'] = 'hybrid'
            else:
                # Add new semantic result
                result.metadata['semantic_score'] = result.score
                result.metadata['keyword_score'] = 0.0
                result.score *= semantic_weight
                result.metadata['search_method'] = 'semantic'
                combined_results[result.content_id] = result
        
        # Convert to list and sort by combined score
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results[:max_results]
    
    def _post_process_results(self, results: List[SearchResult], search_query: SearchQuery) -> List[SearchResult]:
        """Apply post-processing to search results."""
        processed_results = []
        
        for result in results:
            # Apply minimum score threshold
            if result.score < self.search_config.min_score_threshold:
                continue
            
            # Apply quality boost if enabled
            if self.search_config.boost_high_quality:
                quality_score = result.metadata.get('quality_score', 0.5)
                if quality_score > 0.7:
                    result.score *= 1.1  # 10% boost for high quality content
            
            # Apply recency boost if enabled
            if self.search_config.boost_recent_content:
                # This would require timestamp information in metadata
                created_at = result.metadata.get('created_at')
                if created_at:
                    # Simple recency boost logic could be added here
                    pass
            
            # Add search metadata
            result.metadata['search_query'] = search_query.query_text
            result.metadata['search_type'] = search_query.search_type
            result.metadata['search_timestamp'] = search_query.timestamp.isoformat()
            
            processed_results.append(result)
        
        return processed_results
    
    def _update_search_stats(self, search_type: str, response_time: float) -> None:
        """Update search statistics."""
        self.search_stats['total_searches'] += 1
        
        if search_type == SearchType.KEYWORD.value:
            self.search_stats['keyword_searches'] += 1
        elif search_type == SearchType.SEMANTIC.value:
            self.search_stats['semantic_searches'] += 1
        elif search_type == SearchType.HYBRID.value:
            self.search_stats['hybrid_searches'] += 1
        
        # Update average response time
        total_searches = self.search_stats['total_searches']
        current_avg = self.search_stats['average_response_time']
        self.search_stats['average_response_time'] = (
            (current_avg * (total_searches - 1) + response_time) / total_searches
        )
    
    def configure_search(self, config: Dict[str, Any]) -> None:
        """Configure search parameters and weights."""
        self._configure_from_dict(config)
        
        # Clear cache when configuration changes
        if self.search_config.enable_caching:
            self.cache.clear()
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get current search configuration."""
        return {
            'keyword_weight': self.search_config.keyword_weight,
            'semantic_weight': self.search_config.semantic_weight,
            'max_results': self.search_config.max_results,
            'cache_enabled': self.search_config.enable_caching,
            'cache_ttl_seconds': self.search_config.cache_ttl_seconds,
            'min_score_threshold': self.search_config.min_score_threshold,
            'boost_recent_content': self.search_config.boost_recent_content,
            'boost_high_quality': self.search_config.boost_high_quality
        }
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search performance statistics."""
        return self.search_stats.copy()
    
    def clear_cache(self) -> None:
        """Clear search result cache."""
        self.cache.clear()
    
    def optimize_weights(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Optimize search weights based on user feedback."""
        # This is a placeholder for a more sophisticated weight optimization algorithm
        # In practice, this could use machine learning to optimize weights based on:
        # - Click-through rates
        # - User satisfaction scores
        # - Relevance feedback
        
        if not feedback_data:
            return {
                'keyword_weight': self.search_config.keyword_weight,
                'semantic_weight': self.search_config.semantic_weight
            }
        
        # Simple optimization based on average satisfaction scores
        keyword_satisfaction = []
        semantic_satisfaction = []
        hybrid_satisfaction = []
        
        for feedback in feedback_data:
            search_method = feedback.get('search_method', 'hybrid')
            satisfaction = feedback.get('satisfaction_score', 0.5)
            
            if search_method == 'keyword':
                keyword_satisfaction.append(satisfaction)
            elif search_method == 'semantic':
                semantic_satisfaction.append(satisfaction)
            elif search_method == 'hybrid':
                hybrid_satisfaction.append(satisfaction)
        
        # Calculate average satisfaction scores
        avg_keyword = sum(keyword_satisfaction) / len(keyword_satisfaction) if keyword_satisfaction else 0.5
        avg_semantic = sum(semantic_satisfaction) / len(semantic_satisfaction) if semantic_satisfaction else 0.5
        
        # Adjust weights based on performance
        if avg_keyword > avg_semantic:
            new_keyword_weight = min(0.7, self.search_config.keyword_weight + 0.1)
            new_semantic_weight = 1.0 - new_keyword_weight
        elif avg_semantic > avg_keyword:
            new_semantic_weight = min(0.7, self.search_config.semantic_weight + 0.1)
            new_keyword_weight = 1.0 - new_semantic_weight
        else:
            # Keep current weights if performance is similar
            new_keyword_weight = self.search_config.keyword_weight
            new_semantic_weight = self.search_config.semantic_weight
        
        return {
            'keyword_weight': new_keyword_weight,
            'semantic_weight': new_semantic_weight
        }
    
    def explain_search(self, query: str, result: SearchResult) -> Dict[str, Any]:
        """Explain why a particular result was returned for a query."""
        explanation = {
            'query': query,
            'result_id': result.content_id,
            'final_score': result.score,
            'search_method': result.metadata.get('search_method', 'unknown'),
            'factors': []
        }
        
        # Explain keyword matching
        if 'keyword_score' in result.metadata:
            keyword_score = result.metadata['keyword_score']
            explanation['factors'].append({
                'type': 'keyword_matching',
                'score': keyword_score,
                'weight': self.search_config.keyword_weight,
                'contribution': keyword_score * self.search_config.keyword_weight,
                'description': f"Keyword matching contributed {keyword_score:.3f} points"
            })
        
        # Explain semantic similarity
        if 'semantic_score' in result.metadata:
            semantic_score = result.metadata['semantic_score']
            explanation['factors'].append({
                'type': 'semantic_similarity',
                'score': semantic_score,
                'weight': self.search_config.semantic_weight,
                'contribution': semantic_score * self.search_config.semantic_weight,
                'description': f"Semantic similarity contributed {semantic_score:.3f} points"
            })
        
        # Explain quality boost
        if self.search_config.boost_high_quality:
            quality_score = result.metadata.get('quality_score', 0.5)
            if quality_score > 0.7:
                explanation['factors'].append({
                    'type': 'quality_boost',
                    'score': quality_score,
                    'boost_factor': 1.1,
                    'description': f"High quality content (score: {quality_score:.3f}) received 10% boost"
                })
        
        return explanation