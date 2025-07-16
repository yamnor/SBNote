import json
import os
import shutil
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from helpers import get_env
from logger import logger

from .base import BaseTags
from .models import TagConfig, TagsConfig, TagBackupInfo


class FileSystemTags(BaseTags):
    """File system implementation for tag management"""
    
    def __init__(self):
        self.base_path = get_env("SBNOTE_PATH", mandatory=True)
        self.config_path = os.path.join(self.base_path, "tags", "config.json")
        self.backup_path = os.path.join(self.base_path, "tags", "backup")
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.backup_path, exist_ok=True)
        
        # Load initial configuration
        self._load_config()
    
    def get_tag_config(self, tag_name: str) -> Optional[TagConfig]:
        """Get configuration for a specific tag"""
        config = self._load_config()
        return config.tags.get(tag_name)
    
    def get_all_tags_config(self) -> TagsConfig:
        """Get configuration for all tags"""
        return self._load_config()
    
    def update_tag_config(self, tag_name: str, config: TagConfig) -> TagConfig:
        """Update configuration for a specific tag"""
        tags_config = self._load_config()
        
        # Update the tag configuration
        config.updated_at = datetime.now()
        tags_config.tags[tag_name] = config
        
        # Save the updated configuration
        self._save_config(tags_config)
        
        logger.info(f"Updated tag configuration for '{tag_name}'")
        return config
    
    def delete_tag_config(self, tag_name: str) -> bool:
        """Delete configuration for a specific tag"""
        tags_config = self._load_config()
        
        if tag_name in tags_config.tags:
            del tags_config.tags[tag_name]
            self._save_config(tags_config)
            logger.info(f"Deleted tag configuration for '{tag_name}'")
            return True
        
        return False
    
    def create_backup(self) -> str:
        """Create backup of current configuration"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"config_{timestamp}.json"
        backup_path = os.path.join(self.backup_path, backup_filename)
        
        # Load current configuration
        config = self._load_config()
        config.last_backup = datetime.now()
        
        # Save backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config.dict(), f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Created tag configuration backup: {backup_filename}")
        return backup_filename
    
    def list_backups(self) -> List[TagBackupInfo]:
        """List available backup files"""
        backups = []
        
        if os.path.exists(self.backup_path):
            for filename in os.listdir(self.backup_path):
                if filename.endswith('.json') and filename.startswith('config_'):
                    backup_path = os.path.join(self.backup_path, filename)
                    stat = os.stat(backup_path)
                    
                    # Extract timestamp from filename
                    timestamp_str = filename.replace('config_', '').replace('.json', '')
                    try:
                        created_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                    except ValueError:
                        created_at = datetime.fromtimestamp(stat.st_mtime)
                    
                    backups.append(TagBackupInfo(
                        filename=filename,
                        created_at=created_at,
                        size=stat.st_size
                    ))
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore configuration from backup"""
        backup_path = os.path.join(self.backup_path, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_filename}")
            return False
        
        try:
            # Read backup file
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate and create TagsConfig object
            restored_config = TagsConfig(**backup_data)
            
            # Save as current configuration
            self._save_config(restored_config)
            
            logger.info(f"Restored tag configuration from backup: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_filename}: {e}")
            return False
    
    def _load_config(self) -> TagsConfig:
        """Load tags configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return TagsConfig(**data)
            except Exception as e:
                logger.error(f"Failed to load tags configuration: {e}")
                # Return default configuration if loading fails
                return TagsConfig()
        
        # Return default configuration if file doesn't exist
        return TagsConfig()
    
    def _save_config(self, config: TagsConfig):
        """Save tags configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.dict(), f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save tags configuration: {e}")
            raise 