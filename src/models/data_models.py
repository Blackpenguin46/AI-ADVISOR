"""
Enhanced data models for the AI Advisor system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import ContentType, ProjectStatus


@dataclass
class UserProfile:
    """User profile with learning and preference tracking."""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: Optional[str] = None
    skill_level: Dict[str, float] = field(default_factory=dict)  # Domain -> proficiency score (0.0-1.0)
    learning_goals: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: List['Interaction'] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)  # Project IDs
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_skill_level(self, domain: str, score: float) -> None:
        """Update skill level for a domain."""
        self.skill_level[domain] = max(0.0, min(1.0, score))
        self.updated_at = datetime.now()
    
    def add_learning_goal(self, goal: str) -> None:
        """Add a learning goal."""
        if goal not in self.learning_goals:
            self.learning_goals.append(goal)
            self.updated_at = datetime.now()


@dataclass
class Interaction:
    """User interaction record."""
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: Optional[str] = None
    query: str = ""
    response: str = ""
    feedback_score: Optional[float] = None  # 0.0-1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def set_feedback(self, score: float) -> None:
        """Set user feedback score."""
        self.feedback_score = max(0.0, min(1.0, score))


@dataclass
class Milestone:
    """Project milestone."""
    milestone_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, cancelled
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def complete(self) -> None:
        """Mark milestone as completed."""
        self.status = "completed"
        self.completed_at = datetime.now()


@dataclass
class Conversation:
    """Conversation thread."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    interactions: List[Interaction] = field(default_factory=list)
    context_summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_interaction(self, interaction: Interaction) -> None:
        """Add interaction to conversation."""
        self.interactions.append(interaction)
        self.updated_at = datetime.now()
    
    def get_recent_context(self, max_interactions: int = 10) -> List[Interaction]:
        """Get recent interactions for context."""
        return self.interactions[-max_interactions:]


@dataclass
class Project:
    """Enhanced project model with tracking capabilities."""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    owner_id: str = ""
    collaborators: List[str] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.CREATED
    milestones: List[Milestone] = field(default_factory=list)
    conversations: List[Conversation] = field(default_factory=list)
    integrations: Dict[str, Any] = field(default_factory=dict)  # Integration configs
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_milestone(self, title: str, description: str = "", due_date: Optional[datetime] = None) -> Milestone:
        """Add a milestone to the project."""
        milestone = Milestone(title=title, description=description, due_date=due_date)
        self.milestones.append(milestone)
        self.updated_at = datetime.now()
        return milestone
    
    def get_active_conversation(self) -> Optional[Conversation]:
        """Get the most recent conversation."""
        if self.conversations:
            return self.conversations[-1]
        return None
    
    def create_conversation(self) -> Conversation:
        """Create a new conversation for this project."""
        conversation = Conversation(project_id=self.project_id)
        self.conversations.append(conversation)
        self.updated_at = datetime.now()
        return conversation


@dataclass
class EnhancedContent:
    """Enhanced content model with embeddings and metadata."""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: ContentType = ContentType.TEXT
    source_url: Optional[str] = None
    title: str = ""
    text_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0.0-1.0
    processing_method: str = "unknown"
    chunk_index: int = 0  # For content that's been chunked
    parent_content_id: Optional[str] = None  # For chunks
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the content."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def set_embeddings(self, embeddings: List[float]) -> None:
        """Set content embeddings."""
        self.embeddings = embeddings
        self.updated_at = datetime.now()


@dataclass
class SearchQuery:
    """Search query with configuration."""
    query_text: str = ""
    search_type: str = "hybrid"  # keyword, semantic, hybrid
    max_results: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=lambda: {"keyword": 0.4, "semantic": 0.6})
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelInfo:
    """Information about AI models."""
    model_id: str = ""
    model_name: str = ""
    model_type: str = "llm"  # llm, embedding, vision, etc.
    version: str = "1.0.0"
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_custom: bool = False
    base_model: Optional[str] = None
    training_data_info: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def update_performance(self, metric_name: str, value: float) -> None:
        """Update performance metric."""
        self.performance_metrics[metric_name] = value


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""
    integration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    integration_type: str = ""  # git, ide, webhook, etc.
    name: str = ""
    enabled: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    credentials: Dict[str, str] = field(default_factory=dict)  # Encrypted
    last_sync: Optional[datetime] = None
    status: str = "inactive"  # active, inactive, error
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def activate(self) -> None:
        """Activate the integration."""
        self.enabled = True
        self.status = "active"
        self.updated_at = datetime.now()
    
    def deactivate(self, error_message: Optional[str] = None) -> None:
        """Deactivate the integration."""
        self.enabled = False
        self.status = "error" if error_message else "inactive"
        self.error_message = error_message
        self.updated_at = datetime.now()


@dataclass
class AnalyticsEvent:
    """Analytics event for tracking usage and performance."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""  # query, response, feedback, etc.
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    
    @classmethod
    def create_query_event(cls, user_id: str, query: str, project_id: Optional[str] = None) -> 'AnalyticsEvent':
        """Create a query analytics event."""
        return cls(
            event_type="query",
            user_id=user_id,
            project_id=project_id,
            data={"query": query, "query_length": len(query)}
        )
    
    @classmethod
    def create_response_event(cls, user_id: str, response_time: float, success: bool) -> 'AnalyticsEvent':
        """Create a response analytics event."""
        return cls(
            event_type="response",
            user_id=user_id,
            data={"response_time": response_time, "success": success}
        )


@dataclass
class SystemHealth:
    """System health status."""
    component: str = ""
    status: str = "unknown"  # healthy, warning, error, unknown
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.status == "healthy"


@dataclass
class BackgroundTask:
    """Background task tracking."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""  # video_processing, model_training, etc.
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0  # 0.0-1.0
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = "running"
        self.started_at = datetime.now()
    
    def complete(self, result: Any = None) -> None:
        """Mark task as completed."""
        self.status = "completed"
        self.progress = 1.0
        self.result = result
        self.completed_at = datetime.now()
    
    def fail(self, error_message: str) -> None:
        """Mark task as failed."""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def update_progress(self, progress: float) -> None:
        """Update task progress."""
        self.progress = max(0.0, min(1.0, progress))