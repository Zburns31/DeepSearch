"""
Configuration settings for the indexing system
"""

import os
from typing import Set, List
from pydantic import BaseModel, validator, Field


class IndexingConfig(BaseModel):
    """Configuration for the indexing system"""

    index_dir: str = "~/.deepsearch_index"
    max_file_size: int = Field(
        default=100 * 1024 * 1024, description="Max file size in bytes (100MB)"
    )
    max_workers: int = Field(default=4, description="Number of worker processes")
    batch_size: int = Field(default=100, description="Files to process in batch")
    excluded_extensions: Set[str] = {
        ".tmp",
        ".log",
        ".cache",
        ".DS_Store",
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
        ".app",
    }
    excluded_dirs: Set[str] = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".virtualenv",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "Library",
        "System",
        ".Trash",
        ".npm",
        ".cache",
    }
    monitored_paths: List[str] = ["/Users"]

    # File type support
    supported_text_extensions: Set[str] = {
        ".txt",
        ".md",
        ".py",
        ".js",
        ".html",
        ".css",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
    }
    supported_document_extensions: Set[str] = {
        ".pdf",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
    }

    @validator("index_dir")
    def expand_path(cls, v):
        return os.path.expanduser(v)

    @validator("monitored_paths", each_item=True)
    def expand_monitored_paths(cls, v):
        return os.path.expanduser(v)

    # Performance settings
    use_process_pool: bool = Field(
        default=False,
        description="Use ProcessPoolExecutor for text extraction (faster but may have pickle issues)",
    )

    def get_all_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions"""
        return self.supported_text_extensions | self.supported_document_extensions
