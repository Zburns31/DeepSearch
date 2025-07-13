"""
DeepSearch Indexing Module

This module provides intelligent file indexing capabilities using Whoosh
and file system monitoring with watchdog.
"""

from .config import IndexingConfig
from .logger import IndexingLogger
from .models import FileMetadata, IndexingJob, IndexingPriority
from .extractor import TextExtractor
from .indexer import WhooshIndexer
from .watcher import FileSystemWatcher
from .manager import SmartFileIndexer

__all__ = [
    "IndexingConfig",
    "IndexingLogger",
    "FileMetadata",
    "IndexingJob",
    "IndexingPriority",
    "TextExtractor",
    "WhooshIndexer",
    "FileSystemWatcher",
    "SmartFileIndexer",
]
