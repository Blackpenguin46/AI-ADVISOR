"""
Configuration management system for the Enhanced AI Advisor.
Supports feature toggles, environment-specific settings, and runtime configuration.
"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    vector_db_type: str = "chromadb"  # chromadb, qdrant, pinecone
    vector_db_path: str = "./data/vector_db"
    knowledge_db_path: str = "./knowledge_base_final.json"
    user_db_path: str = "./data/users.db"
    project_db_path: str = "./data/projects.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SearchConfig:
    """Search system configuration."""
    hybrid_search_enabled: bool = True
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6
    max_results: int = 10
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


@dataclass
class ModelConfig:
    """AI model configuration."""
    default_model: str = "llama2"
    available_models: list = None
    custom_models_path: str = "./data/custom_models"
    fine_tuning_enabled: bool = False
    model_cache_size: int = 3
    context_window_size: int = 4000


@dataclass
class IntegrationConfig:
    """Integration settings."""
    ide_integration_enabled: bool = False
    git_integration_enabled: bool = False
    webhook_enabled: bool = False
    api_enabled: bool = False
    real_time_processing: bool = False


@dataclass
class SecurityConfig:
    """Security and privacy settings."""
    authentication_enabled: bool = False
    jwt_secret_key: str = ""
    session_timeout_minutes: int = 60
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    encryption_enabled: bool = False
    audit_logging: bool = False


@dataclass
class FeatureFlags:
    """Feature toggle configuration."""
    vector_search: bool = False
    conversation_memory: bool = False
    multi_modal_processing: bool = False
    project_tracking: bool = False
    real_time_video_processing: bool = False
    custom_model_training: bool = False
    enterprise_features: bool = False
    api_endpoints: bool = False
    learning_system: bool = False
    analytics: bool = False


@dataclass
class PerformanceConfig:
    """Performance and resource settings."""
    max_concurrent_requests: int = 10
    memory_limit_mb: int = 2048
    cache_size_mb: int = 512
    background_processing_enabled: bool = True
    max_background_tasks: int = 5
    response_timeout_seconds: int = 30


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"
    host: str = "localhost"
    port: int = 8501
    data_directory: str = "./data"
    
    # Component configurations
    database: DatabaseConfig = None
    search: SearchConfig = None
    models: ModelConfig = None
    integrations: IntegrationConfig = None
    security: SecurityConfig = None
    features: FeatureFlags = None
    performance: PerformanceConfig = None
    
    def __post_init__(self):
        """Initialize nested configurations with defaults."""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.search is None:
            self.search = SearchConfig()
        if self.models is None:
            self.models = ModelConfig()
            if self.models.available_models is None:
                self.models.available_models = ["llama2", "mistral", "codellama"]
        if self.integrations is None:
            self.integrations = IntegrationConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.features is None:
            self.features = FeatureFlags()
        if self.performance is None:
            self.performance = PerformanceConfig()


class ConfigManager:
    """Configuration manager with environment support and feature toggles."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: AppConfig = AppConfig()
        self._load_config()
        self._ensure_directories()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        env = os.getenv("AI_ADVISOR_ENV", "development")
        return f"./config/{env}.yaml"
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from file if exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                self._update_config_from_dict(config_data)
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
        
        # Override with environment variables
        self._load_from_environment()
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self.config, key):
                if isinstance(value, dict):
                    # Handle nested configuration objects
                    nested_config = getattr(self.config, key)
                    if nested_config is not None:
                        for nested_key, nested_value in value.items():
                            if hasattr(nested_config, nested_key):
                                setattr(nested_config, nested_key, nested_value)
                else:
                    setattr(self.config, key, value)
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Environment
        if env_str := os.getenv("AI_ADVISOR_ENV"):
            try:
                self.config.environment = Environment(env_str)
            except ValueError:
                pass
        
        # Basic settings
        self.config.debug = os.getenv("AI_ADVISOR_DEBUG", str(self.config.debug)).lower() == "true"
        self.config.log_level = os.getenv("AI_ADVISOR_LOG_LEVEL", self.config.log_level)
        self.config.host = os.getenv("AI_ADVISOR_HOST", self.config.host)
        
        if port := os.getenv("AI_ADVISOR_PORT"):
            try:
                self.config.port = int(port)
            except ValueError:
                pass
        
        # Feature flags
        for feature_name in ["vector_search", "conversation_memory", "multi_modal_processing",
                           "project_tracking", "real_time_video_processing", "custom_model_training",
                           "enterprise_features", "api_endpoints", "learning_system", "analytics"]:
            env_var = f"AI_ADVISOR_FEATURE_{feature_name.upper()}"
            if env_value := os.getenv(env_var):
                setattr(self.config.features, feature_name, env_value.lower() == "true")
        
        # Database settings
        if db_path := os.getenv("AI_ADVISOR_VECTOR_DB_PATH"):
            self.config.database.vector_db_path = db_path
        
        if kb_path := os.getenv("AI_ADVISOR_KNOWLEDGE_DB_PATH"):
            self.config.database.knowledge_db_path = kb_path
        
        # Model settings
        if model := os.getenv("AI_ADVISOR_DEFAULT_MODEL"):
            self.config.models.default_model = model
        
        # Security settings
        if jwt_key := os.getenv("AI_ADVISOR_JWT_SECRET"):
            self.config.security.jwt_secret_key = jwt_key
        
        self.config.security.authentication_enabled = os.getenv(
            "AI_ADVISOR_AUTH_ENABLED", str(self.config.security.authentication_enabled)
        ).lower() == "true"
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [
            self.config.data_directory,
            os.path.dirname(self.config.database.vector_db_path),
            os.path.dirname(self.config.database.user_db_path),
            os.path.dirname(self.config.database.project_db_path),
            self.config.models.custom_models_path,
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        return self.config
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(self.config.features, feature_name, False)
    
    def enable_feature(self, feature_name: str) -> None:
        """Enable a feature flag."""
        if hasattr(self.config.features, feature_name):
            setattr(self.config.features, feature_name, True)
    
    def disable_feature(self, feature_name: str) -> None:
        """Disable a feature flag."""
        if hasattr(self.config.features, feature_name):
            setattr(self.config.features, feature_name, False)
    
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        save_path = path or self.config_path
        config_dict = asdict(self.config)
        
        # Convert enum to string
        config_dict['environment'] = self.config.environment.value
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                yaml.dump(config_dict, f, default_flow_style=False)
            else:
                json.dump(config_dict, f, indent=2)
    
    def reload_config(self) -> None:
        """Reload configuration from file and environment."""
        self._load_config()
        self._ensure_directories()
    
    def get_database_url(self, db_type: str) -> str:
        """Get database URL for specified type."""
        if db_type == "vector":
            return self.config.database.vector_db_path
        elif db_type == "knowledge":
            return self.config.database.knowledge_db_path
        elif db_type == "user":
            return self.config.database.user_db_path
        elif db_type == "project":
            return self.config.database.project_db_path
        else:
            raise ValueError(f"Unknown database type: {db_type}")


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> AppConfig:
    """Get global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled globally."""
    return get_config_manager().is_feature_enabled(feature_name)


def initialize_config(config_path: Optional[str] = None) -> ConfigManager:
    """Initialize global configuration manager."""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager