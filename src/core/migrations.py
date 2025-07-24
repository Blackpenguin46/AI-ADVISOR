"""
Database schema migration system for backward compatibility and upgrades.
"""

import os
import json
import sqlite3
import shutil
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .interfaces import IErrorHandler


@dataclass
class MigrationInfo:
    """Information about a migration."""
    version: str
    description: str
    timestamp: datetime
    applied: bool = False


class Migration(ABC):
    """Base class for database migrations."""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.now()
    
    @abstractmethod
    def up(self, connection: Any) -> bool:
        """Apply the migration."""
        pass
    
    @abstractmethod
    def down(self, connection: Any) -> bool:
        """Rollback the migration."""
        pass
    
    @abstractmethod
    def validate(self, connection: Any) -> bool:
        """Validate that migration was applied correctly."""
        pass


class KnowledgeBaseMigration(Migration):
    """Migration for knowledge base format changes."""
    
    def __init__(self, version: str, description: str, transform_func: Callable):
        super().__init__(version, description)
        self.transform_func = transform_func
    
    def up(self, connection: str) -> bool:
        """Apply knowledge base migration."""
        try:
            # Load existing knowledge base
            if not os.path.exists(connection):
                return True  # No existing data to migrate
            
            with open(connection, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Apply transformation
            transformed_data = self.transform_func(data)
            
            # Backup original
            backup_path = f"{connection}.backup.{self.version}"
            shutil.copy2(connection, backup_path)
            
            # Save transformed data
            with open(connection, 'w', encoding='utf-8') as f:
                json.dump(transformed_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Migration {self.version} failed: {e}")
            return False
    
    def down(self, connection: str) -> bool:
        """Rollback knowledge base migration."""
        try:
            backup_path = f"{connection}.backup.{self.version}"
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, connection)
                return True
            return False
        except Exception as e:
            print(f"Rollback {self.version} failed: {e}")
            return False
    
    def validate(self, connection: str) -> bool:
        """Validate knowledge base migration."""
        try:
            with open(connection, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Basic validation - ensure it's valid JSON and has expected structure
            return isinstance(data, dict) and len(data) > 0
        except Exception:
            return False


class SQLiteMigration(Migration):
    """Migration for SQLite database schema changes."""
    
    def __init__(self, version: str, description: str, up_sql: str, down_sql: str = ""):
        super().__init__(version, description)
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def up(self, connection: sqlite3.Connection) -> bool:
        """Apply SQLite migration."""
        try:
            cursor = connection.cursor()
            cursor.executescript(self.up_sql)
            connection.commit()
            return True
        except Exception as e:
            print(f"Migration {self.version} failed: {e}")
            connection.rollback()
            return False
    
    def down(self, connection: sqlite3.Connection) -> bool:
        """Rollback SQLite migration."""
        if not self.down_sql:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.executescript(self.down_sql)
            connection.commit()
            return True
        except Exception as e:
            print(f"Rollback {self.version} failed: {e}")
            connection.rollback()
            return False
    
    def validate(self, connection: sqlite3.Connection) -> bool:
        """Validate SQLite migration."""
        try:
            cursor = connection.cursor()
            # Basic validation - check if we can query the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return True
        except Exception:
            return False


class MigrationManager:
    """Manages database migrations and version control."""
    
    def __init__(self, data_directory: str, error_handler: Optional[IErrorHandler] = None):
        self.data_directory = Path(data_directory)
        self.error_handler = error_handler
        self.migrations: Dict[str, List[Migration]] = {
            'knowledge_base': [],
            'user_db': [],
            'project_db': [],
            'vector_db': []
        }
        self._register_default_migrations()
    
    def _register_default_migrations(self) -> None:
        """Register default migrations for system upgrade."""
        
        # Knowledge base migrations
        self.register_migration('knowledge_base', KnowledgeBaseMigration(
            "1.0.0", 
            "Add content_id and embeddings support",
            self._add_content_ids_transform
        ))
        
        self.register_migration('knowledge_base', KnowledgeBaseMigration(
            "1.1.0",
            "Add quality scores and processing metadata",
            self._add_quality_scores_transform
        ))
        
        # User database migrations
        self.register_migration('user_db', SQLiteMigration(
            "1.0.0",
            "Create initial user tables",
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                skill_profile TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                data TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
            """
        ))
        
        # Project database migrations
        self.register_migration('project_db', SQLiteMigration(
            "1.0.0",
            "Create initial project tables",
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                status TEXT DEFAULT 'created',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS project_conversations (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (project_id) REFERENCES projects (id)
            );
            
            CREATE TABLE IF NOT EXISTS project_milestones (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_project ON project_conversations(project_id);
            CREATE INDEX IF NOT EXISTS idx_milestones_project ON project_milestones(project_id);
            """
        ))
    
    def _add_content_ids_transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add content IDs to existing knowledge base entries."""
        import uuid
        
        transformed = {}
        for url, content in data.items():
            if isinstance(content, dict):
                # Add content_id if not present
                if 'content_id' not in content:
                    content['content_id'] = str(uuid.uuid4())
                
                # Initialize embeddings field
                if 'embeddings' not in content:
                    content['embeddings'] = None
                
                # Add processing metadata
                if 'processing_metadata' not in content:
                    content['processing_metadata'] = {
                        'method': 'legacy',
                        'version': '1.0.0',
                        'timestamp': datetime.now().isoformat()
                    }
                
                transformed[url] = content
            else:
                # Handle legacy format
                transformed[url] = {
                    'content_id': str(uuid.uuid4()),
                    'title': f"Legacy content {url}",
                    'content': str(content),
                    'embeddings': None,
                    'processing_metadata': {
                        'method': 'legacy',
                        'version': '1.0.0',
                        'timestamp': datetime.now().isoformat()
                    }
                }
        
        return transformed
    
    def _add_quality_scores_transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add quality scores to knowledge base entries."""
        for url, content in data.items():
            if isinstance(content, dict):
                # Add quality score if not present
                if 'quality_score' not in content:
                    # Simple heuristic based on content length and structure
                    text_content = content.get('transcript', '') or content.get('content', '')
                    if len(text_content) > 1000:
                        content['quality_score'] = 0.8
                    elif len(text_content) > 500:
                        content['quality_score'] = 0.6
                    else:
                        content['quality_score'] = 0.4
                
                # Add tags if not present
                if 'tags' not in content:
                    content['tags'] = []
        
        return data
    
    def register_migration(self, db_type: str, migration: Migration) -> None:
        """Register a migration for a database type."""
        if db_type not in self.migrations:
            self.migrations[db_type] = []
        
        self.migrations[db_type].append(migration)
        # Sort by version
        self.migrations[db_type].sort(key=lambda m: m.version)
    
    def get_current_version(self, db_type: str) -> str:
        """Get current version of a database."""
        version_file = self.data_directory / f"{db_type}_version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.0.0"
    
    def set_current_version(self, db_type: str, version: str) -> None:
        """Set current version of a database."""
        version_file = self.data_directory / f"{db_type}_version.txt"
        version_file.write_text(version)
    
    def get_pending_migrations(self, db_type: str) -> List[Migration]:
        """Get list of pending migrations for a database type."""
        current_version = self.get_current_version(db_type)
        pending = []
        
        for migration in self.migrations.get(db_type, []):
            if migration.version > current_version:
                pending.append(migration)
        
        return pending
    
    def apply_migrations(self, db_type: str, db_path: str) -> bool:
        """Apply all pending migrations for a database type."""
        pending = self.get_pending_migrations(db_type)
        if not pending:
            return True
        
        print(f"Applying {len(pending)} migrations for {db_type}...")
        
        # Get database connection
        connection = self._get_connection(db_type, db_path)
        if connection is None:
            return False
        
        try:
            for migration in pending:
                print(f"Applying migration {migration.version}: {migration.description}")
                
                if migration.up(connection):
                    if migration.validate(connection):
                        self.set_current_version(db_type, migration.version)
                        print(f"Migration {migration.version} applied successfully")
                    else:
                        print(f"Migration {migration.version} validation failed")
                        return False
                else:
                    print(f"Migration {migration.version} failed")
                    return False
            
            return True
        
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error("migration_error", e, {"db_type": db_type})
            else:
                print(f"Migration error: {e}")
            return False
        
        finally:
            self._close_connection(db_type, connection)
    
    def rollback_migration(self, db_type: str, db_path: str, target_version: str) -> bool:
        """Rollback migrations to a target version."""
        current_version = self.get_current_version(db_type)
        
        # Find migrations to rollback
        to_rollback = []
        for migration in reversed(self.migrations.get(db_type, [])):
            if migration.version > target_version and migration.version <= current_version:
                to_rollback.append(migration)
        
        if not to_rollback:
            return True
        
        print(f"Rolling back {len(to_rollback)} migrations for {db_type}...")
        
        connection = self._get_connection(db_type, db_path)
        if connection is None:
            return False
        
        try:
            for migration in to_rollback:
                print(f"Rolling back migration {migration.version}")
                
                if migration.down(connection):
                    # Update version to previous migration
                    prev_version = "0.0.0"
                    for m in self.migrations[db_type]:
                        if m.version < migration.version:
                            prev_version = m.version
                    
                    self.set_current_version(db_type, prev_version)
                    print(f"Migration {migration.version} rolled back successfully")
                else:
                    print(f"Rollback of migration {migration.version} failed")
                    return False
            
            return True
        
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error("rollback_error", e, {"db_type": db_type})
            else:
                print(f"Rollback error: {e}")
            return False
        
        finally:
            self._close_connection(db_type, connection)
    
    def _get_connection(self, db_type: str, db_path: str) -> Any:
        """Get database connection based on type."""
        if db_type == 'knowledge_base':
            return db_path  # File path for JSON operations
        else:
            # SQLite connection
            try:
                return sqlite3.connect(db_path)
            except Exception as e:
                print(f"Failed to connect to {db_type}: {e}")
                return None
    
    def _close_connection(self, db_type: str, connection: Any) -> None:
        """Close database connection."""
        if db_type != 'knowledge_base' and hasattr(connection, 'close'):
            connection.close()
    
    def get_migration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all migrations."""
        status = {}
        
        for db_type in self.migrations:
            current_version = self.get_current_version(db_type)
            pending = self.get_pending_migrations(db_type)
            
            status[db_type] = {
                'current_version': current_version,
                'latest_version': self.migrations[db_type][-1].version if self.migrations[db_type] else "0.0.0",
                'pending_migrations': len(pending),
                'migrations': [
                    {
                        'version': m.version,
                        'description': m.description,
                        'applied': m.version <= current_version
                    }
                    for m in self.migrations[db_type]
                ]
            }
        
        return status
    
    def initialize_databases(self, config: Dict[str, str]) -> bool:
        """Initialize all databases with migrations."""
        success = True
        
        for db_type, db_path in config.items():
            if db_type in self.migrations:
                print(f"Initializing {db_type} database...")
                if not self.apply_migrations(db_type, db_path):
                    print(f"Failed to initialize {db_type}")
                    success = False
                else:
                    print(f"{db_type} initialized successfully")
        
        return success