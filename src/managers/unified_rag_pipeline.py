#!/usr/bin/env python3

"""
Unified RAG Pipeline for AI Advisor
Integrates YouTube videos, Daily.dev articles, and PDFs into a single knowledge base
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedRAGPipeline:
    """
    Unified RAG pipeline that combines multiple content sources:
    - YouTube videos (existing)
    - Daily.dev articles (new integration)
    - PDF documents (future support)
    """
    
    def __init__(self, knowledge_base_path: str = "data/unified_knowledge_base.json"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_db = {}
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load the unified knowledge base from file"""
        try:
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                    self.knowledge_db = json.load(f)
                logger.info(f"Loaded {len(self.knowledge_db)} items from knowledge base")
            else:
                logger.info("No existing knowledge base found, starting fresh")
                self.knowledge_db = {}
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.knowledge_db = {}
    
    def save_knowledge_base(self):
        """Save the unified knowledge base to file"""
        try:
            # Ensure directory exists
            self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup
            if self.knowledge_base_path.exists():
                backup_path = self.knowledge_base_path.with_suffix('.backup.json')
                self.knowledge_base_path.rename(backup_path)
            
            # Save new version
            with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_db, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.knowledge_db)} items to knowledge base")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def generate_content_id(self, source_url: str, title: str) -> str:
        """Generate a unique ID for content based on URL and title"""
        content_string = f"{source_url}_{title}"
        return hashlib.md5(content_string.encode()).hexdigest()[:12]
    
    def add_youtube_video(self, video_data: Dict[str, Any]) -> str:
        """Add a YouTube video to the knowledge base"""
        try:
            # Extract video ID from URL or use provided ID
            video_url = video_data.get('url', video_data.get('source_url', ''))
            title = video_data.get('title', 'Unknown Video')
            
            content_id = self.generate_content_id(video_url, title)
            
            # Standardize YouTube video format
            standardized_entry = {
                'metadata': {
                    'id': content_id,
                    'title': title,
                    'source_type': 'video',
                    'source_url': video_url,
                    'author': video_data.get('uploader', video_data.get('author', 'Unknown')),
                    'date_added': datetime.now().isoformat(),
                    'description': video_data.get('description', ''),
                    'tags': ['video', 'ai', 'education']
                },
                'content': video_data.get('transcript', video_data.get('content', '')),
                'chunks': video_data.get('chunks', []),
                'chunk_count': len(video_data.get('chunks', []))
            }
            
            self.knowledge_db[content_id] = standardized_entry
            logger.info(f"Added YouTube video: {title}")
            return content_id
            
        except Exception as e:
            logger.error(f"Error adding YouTube video: {e}")
            return None
    
    def add_dailydev_article(self, article_data: Dict[str, Any]) -> str:
        """Add a Daily.dev article to the knowledge base"""
        try:
            # Extract article information
            article_url = article_data.get('url', article_data.get('source_url', ''))
            title = article_data.get('title', 'Unknown Article')
            
            content_id = self.generate_content_id(article_url, title)
            
            # Process article content
            content = article_data.get('content', article_data.get('summary', ''))
            if not content and 'description' in article_data:
                content = article_data['description']
            
            # Create chunks from content (split by paragraphs or sentences)
            chunks = self._create_chunks(content)
            
            # Standardize Daily.dev article format
            standardized_entry = {
                'metadata': {
                    'id': content_id,
                    'title': title,
                    'source_type': 'article',
                    'source_url': article_url,
                    'author': article_data.get('author', 'Daily.dev'),
                    'original_source': article_data.get('source', 'Daily.dev'),
                    'date_added': datetime.now().isoformat(),
                    'date_published': article_data.get('createdAt', article_data.get('publishedAt', '')),
                    'description': article_data.get('summary', content[:200] + '...'),
                    'tags': article_data.get('tags', ['article', 'tech', 'daily.dev']),
                    'upvotes': article_data.get('upvotes', 0),
                    'comments': article_data.get('numComments', 0)
                },
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks)
            }
            
            self.knowledge_db[content_id] = standardized_entry
            logger.info(f"Added Daily.dev article: {title}")
            return content_id
            
        except Exception as e:
            logger.error(f"Error adding Daily.dev article: {e}")
            return None
    
    def add_pdf_document(self, pdf_data: Dict[str, Any]) -> str:
        """Add a PDF document to the knowledge base (future implementation)"""
        try:
            # Extract PDF information
            pdf_path = pdf_data.get('path', pdf_data.get('file_path', ''))
            title = pdf_data.get('title', Path(pdf_path).stem if pdf_path else 'Unknown PDF')
            
            content_id = self.generate_content_id(pdf_path, title)
            
            # Process PDF content
            content = pdf_data.get('content', pdf_data.get('text', ''))
            chunks = self._create_chunks(content)
            
            # Standardize PDF format
            standardized_entry = {
                'metadata': {
                    'id': content_id,
                    'title': title,
                    'source_type': 'pdf',
                    'source_url': pdf_path,
                    'author': pdf_data.get('author', 'Unknown'),
                    'date_added': datetime.now().isoformat(),
                    'description': pdf_data.get('description', content[:200] + '...'),
                    'tags': pdf_data.get('tags', ['pdf', 'document']),
                    'page_count': pdf_data.get('page_count', 0)
                },
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks)
            }
            
            self.knowledge_db[content_id] = standardized_entry
            logger.info(f"Added PDF document: {title}")
            return content_id
            
        except Exception as e:
            logger.error(f"Error adding PDF document: {e}")
            return None
    
    def _create_chunks(self, content: str, chunk_size: int = 500) -> List[str]:
        """Create chunks from content for better retrieval"""
        if not content:
            return []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If no paragraphs, split by sentences
        if len(chunks) <= 1 and content:
            sentences = re.split(r'[.!?]+', content)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def search_knowledge(self, query: str, n_results: int = 10, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search the unified knowledge base
        
        Args:
            query: Search query
            n_results: Number of results to return
            source_filter: Filter by source type ('video', 'article', 'pdf', None for all)
        """
        query_words = query.lower().split()
        results = []
        
        for item_id, item_data in self.knowledge_db.items():
            metadata = item_data.get('metadata', {})
            
            # Apply source filter if specified
            if source_filter and metadata.get('source_type') != source_filter:
                continue
            
            content = item_data.get('content', '')
            title = metadata.get('title', '').lower()
            
            # Calculate relevance score
            score = 0
            for word in query_words:
                # Title matches are weighted higher
                score += title.count(word) * 3
                # Content matches
                score += content.lower().count(word)
                # Tag matches
                tags = metadata.get('tags', [])
                for tag in tags:
                    if word in tag.lower():
                        score += 2
            
            if score > 0:
                # Find best matching chunk
                chunks = item_data.get('chunks', [])
                best_chunk = content[:500] if not chunks else chunks[0]
                
                if chunks:
                    for chunk in chunks[:3]:
                        chunk_lower = chunk.lower()
                        if any(word in chunk_lower for word in query_words):
                            best_chunk = chunk
                            break
                
                # Determine uploader/source for display
                source_type = metadata.get('source_type', 'unknown')
                if source_type == 'video':
                    uploader = metadata.get('author', 'Unknown')
                elif source_type == 'article':
                    uploader = metadata.get('original_source', metadata.get('author', 'Daily.dev'))
                else:
                    uploader = metadata.get('author', 'Unknown')
                
                results.append({
                    'content': best_chunk,
                    'metadata': {
                        'title': metadata.get('title', 'Unknown'),
                        'url': metadata.get('source_url', ''),
                        'uploader': uploader,
                        'source_type': source_type,
                        'author': metadata.get('author', 'Unknown'),
                        'date_added': metadata.get('date_added', ''),
                        'tags': metadata.get('tags', [])
                    },
                    'distance': 1.0 - (score / 100),  # Convert score to distance
                    'score': score
                })
        
        # Sort by score (lower distance = better match)
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge base"""
        stats = {
            'total_resources': len(self.knowledge_db),
            'total_chunks': 0,
            'by_source': {
                'youtube': {'count': 0, 'chunks': 0},
                'dailydev': {'count': 0, 'chunks': 0},
                'pdf': {'count': 0, 'chunks': 0},
                'other': {'count': 0, 'chunks': 0}
            },
            'by_author': {},
            'by_tags': {},
            'recent_additions': [],
            'topics': []
        }
        
        # Collect all entries with dates for sorting
        entries_with_dates = []
        
        for item_id, item_data in self.knowledge_db.items():
            metadata = item_data.get('metadata', {})
            chunk_count = item_data.get('chunk_count', len(item_data.get('chunks', [])))
            
            stats['total_chunks'] += chunk_count
            
            # Categorize by source type
            source_type = metadata.get('source_type', 'unknown')
            if source_type == 'video':
                stats['by_source']['youtube']['count'] += 1
                stats['by_source']['youtube']['chunks'] += chunk_count
            elif source_type == 'article':
                stats['by_source']['dailydev']['count'] += 1
                stats['by_source']['dailydev']['chunks'] += chunk_count
            elif source_type == 'pdf':
                stats['by_source']['pdf']['count'] += 1
                stats['by_source']['pdf']['chunks'] += chunk_count
            else:
                stats['by_source']['other']['count'] += 1
                stats['by_source']['other']['chunks'] += chunk_count
            
            # Track authors
            author = metadata.get('author', 'Unknown')
            stats['by_author'][author] = stats['by_author'].get(author, 0) + 1
            
            # Track tags
            tags = metadata.get('tags', [])
            for tag in tags:
                stats['by_tags'][tag] = stats['by_tags'].get(tag, 0) + 1
            
            # Collect for recent additions
            date_added = metadata.get('date_added', '')
            if date_added:
                entries_with_dates.append({
                    'title': metadata.get('title', 'Unknown'),
                    'source_type': source_type,
                    'author': author,
                    'date_added': date_added
                })
            
            # Collect topics
            title = metadata.get('title', 'Unknown')
            stats['topics'].append(title)
        
        # Sort by date and get recent additions
        entries_with_dates.sort(key=lambda x: x['date_added'], reverse=True)
        stats['recent_additions'] = entries_with_dates[:10]
        
        return stats
    
    def migrate_legacy_data(self, legacy_kb_path: str = "knowledge_base_final.json"):
        """Migrate data from legacy knowledge base format"""
        try:
            legacy_path = Path(legacy_kb_path)
            if not legacy_path.exists():
                logger.info("No legacy knowledge base found to migrate")
                return
            
            with open(legacy_path, 'r', encoding='utf-8') as f:
                legacy_data = json.load(f)
            
            migrated_count = 0
            for item_id, item_data in legacy_data.items():
                # Convert legacy format to new format
                if 'title' in item_data and 'transcript' in item_data:
                    # This is a YouTube video in legacy format
                    video_data = {
                        'url': item_id,
                        'title': item_data.get('title', 'Unknown'),
                        'uploader': item_data.get('uploader', 'Unknown'),
                        'transcript': item_data.get('transcript', ''),
                        'chunks': item_data.get('chunks', []),
                        'description': item_data.get('description', '')
                    }
                    
                    if self.add_youtube_video(video_data):
                        migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} items from legacy knowledge base")
            self.save_knowledge_base()
            
        except Exception as e:
            logger.error(f"Error migrating legacy data: {e}")
    
    def integrate_dailydev_data(self):
        """Integrate Daily.dev data from MCP server or scraper results"""
        try:
            # Try to import and use the Daily.dev MCP integration
            from integrations.dailydev_mcp import DailyDevMCP
            
            dailydev_mcp = DailyDevMCP()
            
            # Get popular articles
            popular_articles = dailydev_mcp.sync_popular_articles(limit=50)
            if popular_articles:
                for article in popular_articles:
                    self.add_dailydev_article(article)
            
            # Get recent articles
            recent_articles = dailydev_mcp.sync_recent_articles(limit=30)
            if recent_articles:
                for article in recent_articles:
                    self.add_dailydev_article(article)
            
            logger.info("Successfully integrated Daily.dev data")
            self.save_knowledge_base()
            
        except ImportError:
            logger.warning("Daily.dev MCP integration not available")
        except Exception as e:
            logger.error(f"Error integrating Daily.dev data: {e}")
    
    def bulk_add_content(self, content_list: List[Dict[str, Any]]):
        """Add multiple pieces of content in bulk"""
        added_count = 0
        
        for content in content_list:
            content_type = content.get('type', content.get('source_type', 'unknown'))
            
            if content_type == 'video':
                if self.add_youtube_video(content):
                    added_count += 1
            elif content_type == 'article':
                if self.add_dailydev_article(content):
                    added_count += 1
            elif content_type == 'pdf':
                if self.add_pdf_document(content):
                    added_count += 1
        
        logger.info(f"Bulk added {added_count} items to knowledge base")
        self.save_knowledge_base()
        return added_count
    
    def remove_content(self, content_id: str) -> bool:
        """Remove content from the knowledge base"""
        if content_id in self.knowledge_db:
            del self.knowledge_db[content_id]
            self.save_knowledge_base()
            logger.info(f"Removed content: {content_id}")
            return True
        return False
    
    def update_content(self, content_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing content in the knowledge base"""
        if content_id in self.knowledge_db:
            # Update metadata
            if 'metadata' in updates:
                self.knowledge_db[content_id]['metadata'].update(updates['metadata'])
            
            # Update content and regenerate chunks if content changed
            if 'content' in updates:
                self.knowledge_db[content_id]['content'] = updates['content']
                new_chunks = self._create_chunks(updates['content'])
                self.knowledge_db[content_id]['chunks'] = new_chunks
                self.knowledge_db[content_id]['chunk_count'] = len(new_chunks)
            
            self.save_knowledge_base()
            logger.info(f"Updated content: {content_id}")
            return True
        return False


# Convenience functions for backward compatibility
def create_unified_rag_pipeline(knowledge_base_path: str = "data/unified_knowledge_base.json") -> UnifiedRAGPipeline:
    """Create and return a unified RAG pipeline instance"""
    return UnifiedRAGPipeline(knowledge_base_path)

def migrate_and_integrate_all_sources():
    """Migrate legacy data and integrate all available sources"""
    pipeline = UnifiedRAGPipeline()
    
    # Migrate legacy YouTube data
    pipeline.migrate_legacy_data()
    
    # Integrate Daily.dev data
    pipeline.integrate_dailydev_data()
    
    return pipeline