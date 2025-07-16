from datetime import datetime
from typing import Dict, Optional
from pydantic import Field

from helpers import CustomBaseModel


class TagConfig(CustomBaseModel):
    """Configuration for a single tag"""
    priority: int = Field(default=3, ge=1, le=5, description="Priority level from 1-5")
    description: str = Field(default="", description="Description of the tag")
    is_pinned: bool = Field(default=False, description="Whether the tag is pinned")
    created_at: datetime = Field(default_factory=datetime.now, description="When the tag config was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the tag config was last updated")


class TagConfigUpdate(CustomBaseModel):
    """Update data for tag configuration"""
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level from 1-5")
    description: Optional[str] = Field(None, description="Description of the tag")
    is_pinned: Optional[bool] = Field(None, description="Whether the tag is pinned")


class TagsConfig(CustomBaseModel):
    """Configuration for all tags"""
    tags: Dict[str, TagConfig] = Field(default_factory=dict, description="Tag configurations by tag name")
    default_priority: int = Field(default=3, description="Default priority for new tags")
    config_version: str = Field(default="1.0", description="Configuration file version")
    last_backup: Optional[datetime] = Field(default=None, description="When the last backup was created")


class TagBackupInfo(CustomBaseModel):
    """Information about a backup file"""
    filename: str = Field(description="Backup filename")
    created_at: datetime = Field(description="When the backup was created")
    size: int = Field(description="Backup file size in bytes") 