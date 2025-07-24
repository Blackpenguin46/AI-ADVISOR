"""
Core interfaces and abstract base classes for the Enhanced AI Advisor system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContentType(Enum):
    """Types of content that can be processed."""
    VIDEO = "video"
    IMAGE = "image"
    CODE = "code"
    DOCUMENT = "document"
    TEXT = "text"


class ProjectStatus(Enum):
    """Project lifecycle status."""
    CREATED = "created"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class SearchResult:
    """Standardized search result format."""
    content: str
    metadata: Dict[str, Any]
    score: float
    source_type: ContentType
    content_id: str


@dataclass
class ProcessingResult:
    """Result of content processing operations."""
    success: bool
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_method: Optional[str] = None


class IKnowledgeBase(ABC):
    """Interface for knowledge base implementations."""
    
    @abstractmethod
    def search(self, query: str, n_results: int = 5, **kwargs) -> List[SearchResult]:
        """Search the knowledge base for relevant content."""
        pass
    
    @abstractmethod
    def add_content(self, content: str, metadata: Dict[str, Any], content_type: ContentType) -> str:
        """Add new content to the knowledge base."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        pass
    
    @abstractmethod
    def update_content(self, content_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Update existing content."""
        pass
    
    @abstractmethod
    def delete_content(self, content_id: str) -> bool:
        """Delete content from the knowledge base."""
        pass


class ISearchManager(ABC):
    """Interface for search management implementations."""
    
    @abstractmethod
    def search(self, query: str, search_type: str = "hybrid", **kwargs) -> List[SearchResult]:
        """Perform search with specified type (keyword, semantic, hybrid)."""
        pass
    
    @abstractmethod
    def configure_search(self, config: Dict[str, Any]) -> None:
        """Configure search parameters and weights."""
        pass
    
    @abstractmethod
    def get_search_config(self) -> Dict[str, Any]:
        """Get current search configuration."""
        pass


class IConversationManager(ABC):
    """Interface for conversation management."""
    
    @abstractmethod
    def get_context(self, project_id: str, max_tokens: int = 4000) -> str:
        """Get conversation context for a project."""
        pass
    
    @abstractmethod
    def add_interaction(self, project_id: str, query: str, response: str, metadata: Dict[str, Any] = None) -> None:
        """Add a new interaction to the conversation history."""
        pass
    
    @abstractmethod
    def clear_context(self, project_id: str) -> None:
        """Clear conversation context for a project."""
        pass
    
    @abstractmethod
    def get_conversation_summary(self, project_id: str) -> str:
        """Get a summary of the conversation history."""
        pass


class IProjectManager(ABC):
    """Interface for project management."""
    
    @abstractmethod
    def create_project(self, name: str, description: str, owner_id: str, **kwargs) -> str:
        """Create a new project."""
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details."""
        pass
    
    @abstractmethod
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project information."""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        pass
    
    @abstractmethod
    def list_projects(self, owner_id: str) -> List[Dict[str, Any]]:
        """List projects for a user."""
        pass


class IContentProcessor(ABC):
    """Interface for content processing implementations."""
    
    @abstractmethod
    def can_process(self, content_type: ContentType) -> bool:
        """Check if this processor can handle the content type."""
        pass
    
    @abstractmethod
    def process(self, content: Any, metadata: Dict[str, Any] = None) -> ProcessingResult:
        """Process content and return structured result."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[ContentType]:
        """Get list of supported content types."""
        pass


class IIntegrationPlugin(ABC):
    """Interface for integration plugins."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """Get current context from the integrated tool."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the integration is currently available."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources when plugin is disabled."""
        pass


class ILearningManager(ABC):
    """Interface for learning and adaptation management."""
    
    @abstractmethod
    def update_user_model(self, user_id: str, interaction_data: Dict[str, Any]) -> None:
        """Update user learning model based on interactions."""
        pass
    
    @abstractmethod
    def get_recommendations(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations."""
        pass
    
    @abstractmethod
    def assess_skill_level(self, user_id: str, domain: str) -> float:
        """Assess user skill level in a domain (0.0 to 1.0)."""
        pass
    
    @abstractmethod
    def generate_curriculum(self, user_id: str, learning_goals: List[str]) -> Dict[str, Any]:
        """Generate personalized learning curriculum."""
        pass


class IAnalyticsManager(ABC):
    """Interface for analytics and insights."""
    
    @abstractmethod
    def track_event(self, event_type: str, user_id: str, data: Dict[str, Any]) -> None:
        """Track an analytics event."""
        pass
    
    @abstractmethod
    def get_usage_stats(self, time_range: str) -> Dict[str, Any]:
        """Get usage statistics for a time range."""
        pass
    
    @abstractmethod
    def get_insights(self, metric_type: str) -> Dict[str, Any]:
        """Get insights for a specific metric type."""
        pass
    
    @abstractmethod
    def generate_report(self, report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analytics report."""
        pass


class IErrorHandler(ABC):
    """Interface for error handling and recovery."""
    
    @abstractmethod
    def handle_error(self, error_type: str, error: Exception, context: Dict[str, Any]) -> Any:
        """Handle an error with appropriate fallback strategy."""
        pass
    
    @abstractmethod
    def register_fallback(self, error_type: str, fallback_func: callable) -> None:
        """Register a fallback function for an error type."""
        pass
    
    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        pass


class BaseManager(ABC):
    """Base class for all manager components."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_initialized = False
        self.error_handler: Optional[IErrorHandler] = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the manager component."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass
    
    def set_error_handler(self, error_handler: IErrorHandler) -> None:
        """Set error handler for this manager."""
        self.error_handler = error_handler
    
    def _handle_error(self, error_type: str, error: Exception, context: Dict[str, Any] = None) -> Any:
        """Handle errors using the registered error handler."""
        if self.error_handler:
            return self.error_handler.handle_error(error_type, error, context or {})
        raise error


class BaseProcessor(ABC):
    """Base class for all processor components."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the processor."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass