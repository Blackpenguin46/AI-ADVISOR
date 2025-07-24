"""
Vector Database Manager for AI Advisor

Provides hybrid knowledge base functionality with JSON and vector storage.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class HybridKnowledgeBase:
    """Hybrid knowledge base combining JSON and vector storage."""
    
    def __init__(self, vector_db_path: str, json_kb_path: str):
        """Initialize the hybrid knowledge base."""
        self.vector_db_path = Path(vector_db_path)
        self.json_kb_path = Path(json_kb_path)
        
        # Create directories if they don't exist
        self.vector_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing knowledge base
        self.knowledge_base = self._load_json_kb()
    
    def _load_json_kb(self) -> Dict[str, Any]:
        """Load the JSON knowledge base."""
        if self.json_kb_path.exists():
            try:
                with open(self.json_kb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading knowledge base: {e}")
                return {}
        return {}
    
    def _save_json_kb(self):
        """Save the JSON knowledge base."""
        try:
            with open(self.json_kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for content."""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def add_content(self, content: str, metadata: Dict[str, Any], source_type: str = "article") -> str:
        """Add content to the knowledge base."""
        content_id = self._generate_id(content + metadata.get('title', ''))
        
        # Check if already exists
        if content_id in self.knowledge_base:
            return content_id
        
        # Add to knowledge base
        self.knowledge_base[content_id] = {
            'metadata': {
                **metadata,
                'id': content_id,
                'source_type': source_type,
                'date_added': datetime.now().isoformat(),
            },
            'content': content,
            'processing_notes': [f'Added to knowledge base on {datetime.now().strftime("%Y-%m-%d")}']
        }
        
        # Save to disk
        self._save_json_kb()
        
        return content_id
    
    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID."""
        return self.knowledge_base.get(content_id)
    
    def search_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple text-based search of content."""
        query_words = query.lower().split()
        results = []
        
        for content_id, data in self.knowledge_base.items():
            title = data['metadata'].get('title', '').lower()
            content = data.get('content', '').lower()
            
            # Score based on keyword matches
            score = 0
            for word in query_words:
                score += title.count(word) * 3
                score += content.count(word)
            
            if score > 0:
                results.append({
                    'id': content_id,
                    'score': score,
                    'metadata': data['metadata'],
                    'content': data['content'][:500] + '...' if len(data['content']) > 500 else data['content']
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            'total_items': len(self.knowledge_base),
            'storage_path': str(self.json_kb_path),
            'vector_db_path': str(self.vector_db_path)
        }