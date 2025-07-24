"""
Content processing system for Daily.dev articles.

This module handles the transformation of Daily.dev articles into
knowledge base format with quality scoring and metadata extraction.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class ContentType(Enum):
    """Content type enumeration."""
    DOCUMENT = "document"
    VIDEO = "video"
    IMAGE = "image"
    CODE = "code"


@dataclass
class EnhancedContent:
    """Enhanced content model for knowledge base integration."""
    content_id: str = ""
    source_type: ContentType = ContentType.DOCUMENT
    source_url: Optional[str] = None
    title: str = ""
    text_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    processing_method: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.content_id:
            self.content_id = str(uuid.uuid4())
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't already exist."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag if it exists."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if content has a specific tag."""
        return tag in self.tags
    
    def get_summary(self) -> str:
        """Get a summary of the content."""
        return self.metadata.get('summary', '')
    
    def get_author(self) -> str:
        """Get the author of the content."""
        return self.metadata.get('author', 'Unknown')
    
    def get_source(self) -> str:
        """Get the original source of the content."""
        return self.metadata.get('original_source', 'daily.dev')


class DailyDevContentProcessor:
    """Content processor for Daily.dev articles."""
    
    def __init__(self):
        """Initialize the content processor."""
        self.processing_stats = {
            'articles_processed': 0,
            'articles_with_errors': 0,
            'average_quality_score': 0.0,
            'total_quality_score': 0.0
        }
    
    def convert_article_to_content(self, article_node: Dict[str, Any]) -> EnhancedContent:
        """Convert Daily.dev article node to EnhancedContent format."""
        try:
            # Extract basic information
            title = article_node.get('title', 'Untitled')
            summary = article_node.get('summary', '')
            permalink = article_node.get('permalink', '')
            
            # Create main text content
            text_content = self._build_text_content(title, summary, article_node)
            
            # Extract and process metadata
            metadata = self._extract_metadata(article_node)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(article_node)
            
            # Create enhanced content
            content = EnhancedContent(
                title=title,
                text_content=text_content,
                source_type=ContentType.DOCUMENT,
                source_url=permalink,
                metadata=metadata,
                quality_score=quality_score,
                processing_method='dailydev_content_processor'
            )
            
            # Add tags
            self._add_tags(content, article_node)
            
            # Update processing stats
            self._update_stats(quality_score)
            
            return content
            
        except Exception as e:
            print(f"Error processing article: {e}")
            self.processing_stats['articles_with_errors'] += 1
            
            # Return minimal content on error
            title = 'Error Processing Article'
            source_url = ''
            
            # Safely extract title and URL if article_node is not None
            if article_node and isinstance(article_node, dict):
                title = article_node.get('title', 'Error Processing Article')
                source_url = article_node.get('permalink', '')
            
            return EnhancedContent(
                title=title,
                text_content=f"Error processing article: {str(e)}",
                source_url=source_url,
                quality_score=0.0,
                processing_method='dailydev_content_processor_error'
            )
    
    def _build_text_content(self, title: str, summary: str, article_node: Dict[str, Any]) -> str:
        """Build the main text content from article data."""
        content_parts = [title]
        
        if summary:
            content_parts.append(f"\nSummary: {summary}")
        
        # Add author information if available
        author_info = self._extract_author_info(article_node)
        if author_info:
            content_parts.append(f"\nAuthor: {author_info}")
        
        # Add source information
        source_info = self._extract_source_info(article_node)
        if source_info:
            content_parts.append(f"\nSource: {source_info}")
        
        # Add tags as keywords
        tags = article_node.get('tags', [])
        if tags:
            content_parts.append(f"\nTags: {', '.join(tags)}")
        
        # Add engagement metrics as context
        upvotes = article_node.get('upvotes', 0)
        comments = article_node.get('numComments', 0)
        reading_time = article_node.get('readTime', 0)
        
        if upvotes > 0 or comments > 0 or reading_time > 0:
            engagement_parts = []
            if upvotes > 0:
                engagement_parts.append(f"{upvotes} upvotes")
            if comments > 0:
                engagement_parts.append(f"{comments} comments")
            if reading_time > 0:
                engagement_parts.append(f"{reading_time} min read")
            
            if engagement_parts:
                content_parts.append(f"\nEngagement: {', '.join(engagement_parts)}")
        
        return '\n'.join(content_parts)
    
    def _extract_metadata(self, article_node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from article node."""
        metadata = {
            'dailydev_id': article_node.get('id'),
            'url': article_node.get('permalink', ''),
            'summary': article_node.get('summary', ''),
            'upvotes': article_node.get('upvotes', 0),
            'comments_count': article_node.get('numComments', 0),
            'reading_time': article_node.get('readTime', 0),
            'created_at': article_node.get('createdAt'),
            'source': 'daily.dev',
            'processed_at': datetime.now().isoformat()
        }
        
        # Add source information
        if 'source' in article_node and article_node['source']:
            source = article_node['source']
            metadata['original_source'] = source.get('name', 'Unknown')
            if 'image' in source:
                metadata['source_image'] = source['image']
        
        # Add author information
        if 'author' in article_node and article_node['author']:
            author = article_node['author']
            metadata['author'] = author.get('name', 'Unknown')
            if 'image' in author:
                metadata['author_image'] = author['image']
        
        # Add publication date
        if 'createdAt' in article_node:
            try:
                # Parse ISO date string
                created_at = datetime.fromisoformat(article_node['createdAt'].replace('Z', '+00:00'))
                metadata['publication_date'] = created_at.isoformat()
                metadata['publication_year'] = created_at.year
                metadata['publication_month'] = created_at.month
            except (ValueError, AttributeError):
                pass
        
        return metadata
    
    def _extract_author_info(self, article_node: Dict[str, Any]) -> Optional[str]:
        """Extract author information from article node."""
        if 'author' in article_node and article_node['author']:
            return article_node['author'].get('name', 'Unknown')
        return None
    
    def _extract_source_info(self, article_node: Dict[str, Any]) -> Optional[str]:
        """Extract source information from article node."""
        if 'source' in article_node and article_node['source']:
            return article_node['source'].get('name', 'Unknown')
        return None
    
    def _calculate_quality_score(self, article_node: Dict[str, Any]) -> float:
        """Calculate quality score based on engagement metrics."""
        upvotes = article_node.get('upvotes', 0)
        comments = article_node.get('numComments', 0)
        reading_time = article_node.get('readTime', 0)
        
        # Base score
        score = 0.5
        
        # Engagement scoring (upvotes)
        if upvotes >= 5:
            score += 0.05
        if upvotes >= 10:
            score += 0.05
        if upvotes >= 25:
            score += 0.05
        if upvotes >= 50:
            score += 0.05
        if upvotes >= 100:
            score += 0.1
        
        # Discussion scoring (comments)
        if comments >= 2:
            score += 0.025
        if comments >= 5:
            score += 0.025
        if comments >= 10:
            score += 0.05
        if comments >= 20:
            score += 0.05
        
        # Content depth scoring (reading time)
        if reading_time >= 3:
            score += 0.025
        if reading_time >= 5:
            score += 0.025
        if reading_time >= 10:
            score += 0.05
        if reading_time >= 15:
            score += 0.05
        
        # Bonus for well-rounded articles (good engagement across metrics)
        if upvotes >= 10 and comments >= 3 and reading_time >= 5:
            score += 0.1
        
        # Ensure score is between 0 and 1
        return min(1.0, max(0.0, score))
    
    def _add_tags(self, content: EnhancedContent, article_node: Dict[str, Any]) -> None:
        """Add tags to the content."""
        # Add article tags
        tags = article_node.get('tags', [])
        for tag in tags:
            if tag:  # Skip empty tags
                content.add_tag(tag.lower())
        
        # Add Daily.dev specific tags
        content.add_tag('daily.dev')
        content.add_tag('tech_article')
        
        # Add source-based tags
        if 'source' in article_node and article_node['source']:
            source_name = article_node['source'].get('name', '').lower()
            if source_name:
                content.add_tag(f"source:{source_name}")
        
        # Add engagement-based tags
        upvotes = article_node.get('upvotes', 0)
        comments = article_node.get('numComments', 0)
        
        if upvotes >= 50:
            content.add_tag('highly_upvoted')
        elif upvotes >= 10:
            content.add_tag('popular')
        
        if comments >= 10:
            content.add_tag('highly_discussed')
        elif comments >= 3:
            content.add_tag('discussed')
        
        # Add reading time tags
        reading_time = article_node.get('readTime', 0)
        if reading_time >= 10:
            content.add_tag('long_read')
        elif reading_time >= 5:
            content.add_tag('medium_read')
        elif reading_time > 0:
            content.add_tag('quick_read')
        
        # Add recency tags
        if 'createdAt' in article_node:
            try:
                created_at = datetime.fromisoformat(article_node['createdAt'].replace('Z', '+00:00'))
                days_old = (datetime.now(created_at.tzinfo) - created_at).days
                
                if days_old <= 1:
                    content.add_tag('recent')
                elif days_old <= 7:
                    content.add_tag('this_week')
                elif days_old <= 30:
                    content.add_tag('this_month')
            except (ValueError, AttributeError):
                pass
    
    def _update_stats(self, quality_score: float) -> None:
        """Update processing statistics."""
        self.processing_stats['articles_processed'] += 1
        self.processing_stats['total_quality_score'] += quality_score
        
        # Calculate average quality score
        if self.processing_stats['articles_processed'] > 0:
            self.processing_stats['average_quality_score'] = (
                self.processing_stats['total_quality_score'] / 
                self.processing_stats['articles_processed']
            )
    
    def batch_process_articles(self, article_nodes: List[Dict[str, Any]]) -> List[EnhancedContent]:
        """Process multiple articles in batch."""
        processed_articles = []
        
        for article_node in article_nodes:
            try:
                content = self.convert_article_to_content(article_node)
                processed_articles.append(content)
            except Exception as e:
                print(f"Error processing article in batch: {e}")
                self.processing_stats['articles_with_errors'] += 1
        
        return processed_articles
    
    def filter_by_quality(self, contents: List[EnhancedContent], 
                         min_quality: float = 0.6) -> List[EnhancedContent]:
        """Filter content by minimum quality score."""
        return [content for content in contents if content.quality_score >= min_quality]
    
    def filter_by_tags(self, contents: List[EnhancedContent], 
                      required_tags: List[str] = None, 
                      excluded_tags: List[str] = None) -> List[EnhancedContent]:
        """Filter content by tags."""
        filtered_contents = contents
        
        if required_tags:
            filtered_contents = [
                content for content in filtered_contents
                if any(content.has_tag(tag) for tag in required_tags)
            ]
        
        if excluded_tags:
            filtered_contents = [
                content for content in filtered_contents
                if not any(content.has_tag(tag) for tag in excluded_tags)
            ]
        
        return filtered_contents
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self.processing_stats,
            'error_rate': (
                self.processing_stats['articles_with_errors'] / 
                max(1, self.processing_stats['articles_processed'])
            ) * 100
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            'articles_processed': 0,
            'articles_with_errors': 0,
            'average_quality_score': 0.0,
            'total_quality_score': 0.0
        }
    
    def detect_duplicates(self, contents: List[EnhancedContent]) -> List[List[EnhancedContent]]:
        """Detect duplicate content based on URL and title similarity."""
        duplicates = []
        processed_urls = set()
        processed_titles = set()
        
        for content in contents:
            url = content.source_url
            title = content.title.lower().strip()
            
            # Check for URL duplicates
            if url and url in processed_urls:
                # Find existing duplicate group or create new one
                found_group = False
                for group in duplicates:
                    if any(c.source_url == url for c in group):
                        group.append(content)
                        found_group = True
                        break
                
                if not found_group:
                    # Find the original content with this URL
                    original = next((c for c in contents if c.source_url == url), None)
                    if original:
                        duplicates.append([original, content])
            
            # Check for title duplicates (similar titles)
            elif title and title in processed_titles:
                # Find existing duplicate group or create new one
                found_group = False
                for group in duplicates:
                    if any(c.title.lower().strip() == title for c in group):
                        group.append(content)
                        found_group = True
                        break
                
                if not found_group:
                    # Find the original content with this title
                    original = next((c for c in contents if c.title.lower().strip() == title), None)
                    if original:
                        duplicates.append([original, content])
            
            if url:
                processed_urls.add(url)
            if title:
                processed_titles.add(title)
        
        return duplicates
    
    def merge_duplicate_content(self, duplicate_group: List[EnhancedContent]) -> EnhancedContent:
        """Merge duplicate content, keeping the highest quality version."""
        if not duplicate_group:
            raise ValueError("Cannot merge empty duplicate group")
        
        if len(duplicate_group) == 1:
            return duplicate_group[0]
        
        # Sort by quality score (highest first)
        sorted_content = sorted(duplicate_group, key=lambda x: x.quality_score, reverse=True)
        best_content = sorted_content[0]
        
        # Merge tags from all duplicates
        all_tags = set(best_content.tags)
        for content in sorted_content[1:]:
            all_tags.update(content.tags)
        
        best_content.tags = list(all_tags)
        
        # Add duplicate information to metadata
        best_content.metadata['duplicate_count'] = len(duplicate_group)
        best_content.metadata['merged_from'] = [
            content.content_id for content in sorted_content[1:]
        ]
        
        return best_content