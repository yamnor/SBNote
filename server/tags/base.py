from abc import ABC, abstractmethod
from typing import List, Optional

from .models import TagConfig, TagsConfig, TagBackupInfo


class BaseTags(ABC):
    """Abstract base class for tag management system"""
    
    @abstractmethod
    def get_tag_config(self, tag_name: str) -> Optional[TagConfig]:
        """Get configuration for a specific tag"""
        pass
    
    @abstractmethod
    def get_all_tags_config(self) -> TagsConfig:
        """Get configuration for all tags"""
        pass
    
    @abstractmethod
    def update_tag_config(self, tag_name: str, config: TagConfig) -> TagConfig:
        """Update configuration for a specific tag"""
        pass
    
    @abstractmethod
    def delete_tag_config(self, tag_name: str) -> bool:
        """Delete configuration for a specific tag"""
        pass
    
    @abstractmethod
    def create_backup(self) -> str:
        """Create backup of current configuration"""
        pass
    
    @abstractmethod
    def list_backups(self) -> List[TagBackupInfo]:
        """List available backup files"""
        pass
    
    @abstractmethod
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore configuration from backup"""
        pass 