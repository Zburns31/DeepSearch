"""
Data models for the indexing system
"""

import os
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set, List

from pydantic import BaseModel, validator, Field


class IndexingPriority(Enum):
    """Priority levels for indexing operations"""

    IMMEDIATE = 0  # User-accessed files
    HIGH = 1  # Recently modified files
    NORMAL = 2  # New files
    LOW = 3  # Bulk scan files


class FileMetadata(BaseModel):
    """Pydantic model for file metadata validation"""

    path: str
    filename: str
    extension: str
    size: int
    modified_time: datetime
    created_time: datetime
    file_type: str
    mime_type: str
    content_hash: Optional[str] = None
    indexed_time: Optional[datetime] = None

    @validator("path")
    def validate_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"Path does not exist: {v}")
        return v

    @validator("size")
    def validate_size(cls, v):
        if v < 0:
            raise ValueError("File size cannot be negative")
        return v


@dataclass
class IndexingJob:
    """Represents a file indexing job"""

    file_path: str
    priority: IndexingPriority
    operation: str  # 'create', 'update', 'delete'
    timestamp: datetime

    def __lt__(self, other):
        return self.priority.value < other.priority.value
