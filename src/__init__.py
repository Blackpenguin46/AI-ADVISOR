"""
Enhanced AI Advisor - Main Package

A comprehensive AI development companion with advanced features including:
- Vector-based semantic search
- Conversation memory and project tracking
- Multi-modal content support
- Development tool integration
- Real-time video processing
- Custom model fine-tuning
- Enterprise deployment features
- API endpoints and programmatic access
- Interactive learning and adaptive recommendations
"""

__version__ = "2.0.0"
__author__ = "AI Advisor Team"

from .config.settings import get_config, get_config_manager, is_feature_enabled
from .core.interfaces import *
# from .models.data_models import * # TODO: Create models directory and data_models.py

# Initialize configuration on import
config = get_config()

__all__ = [
    "get_config",
    "get_config_manager", 
    "is_feature_enabled",
    "config",
    # Add other exports as components are implemented
]