"""
Configuration settings for the indexing system
"""

from pathlib import Path
from typing import Set, List
import os

from pydantic import BaseModel, Field, ConfigDict, field_validator


class IndexingConfig(BaseModel):
    """
    Configuration for the DeepSearch indexing system.

    Attributes:
      index_dir: Path where the Whoosh index is stored.
      max_file_size: Maximum file size (in bytes) to include in the index.
      max_workers: Number of parallel workers for extraction/indexing.
      batch_size: Number of files to process in each batch.
      excluded_extensions: File extensions to skip entirely.
      excluded_dirs: Directory names to skip.
      monitored_paths: List of directories to watch and index.
      supported_text_extensions: Text-based file extensions to index content.
      supported_document_extensions: Binary document extensions (PDF, Office, etc.).
      use_process_pool: Whether to use a ProcessPoolExecutor for extraction.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    index_dir: str = Field(
        "~/.deepsearch_index",
        description="Directory for Whoosh index (will be expanded to home).",
    )
    max_file_size: int = Field(
        100 * 1024 * 1024,
        description="Max file size (bytes) to index; defaults to 100 MB.",
    )
    max_workers: int = Field(
        4,
        description="Number of concurrent workers for extraction/indexing.",
    )
    batch_size: int = Field(
        100,
        description="How many files to process in one indexing batch.",
    )

    excluded_extensions: Set[str] = Field(
        {
            ".tmp",
            ".log",
            ".cache",
            ".DS_Store",
            ".pyc",
            ".pyo",
            ".so",
            ".dylib",
            ".app",
        },
        description="File extensions to exclude from indexing.",
    )
    excluded_dirs: Set[str] = Field(
        {
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
        },
        description="Directory names to exclude from monitoring/indexing.",
    )

    monitored_paths: List[str] = Field(
        default_factory=lambda: ["/Users"],
        description="List of paths (folders) to monitor for file changes.",
    )

    supported_text_extensions: Set[str] = Field(
        {
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
        },
        description="Text-based file extensions eligible for content extraction.",
    )
    supported_document_extensions: Set[str] = Field(
        {
            ".pdf",
            ".docx",
            ".doc",
            ".xlsx",
            ".xls",
            ".pptx",
            ".ppt",
        },
        description="Binary document extensions eligible for content extraction.",
    )

    use_process_pool: bool = Field(
        False,
        description=(
            "If True, use ProcessPoolExecutor for text extraction "
            "(can improve speed, but may encounter pickle issues)."
        ),
    )

    @field_validator("index_dir", mode="before")
    @classmethod
    def _expand_index_dir(cls, v: str) -> str:
        """
        Normalize the index directory path before validation.

        This method will:
          1. Expand a leading '~' to the user’s home directory.
          2. Substitute any environment variables (e.g. $HOME, ${PROJECT}).
          3. Resolve the final path to an absolute, canonical form.

        Args:
            v (str): Raw index directory path (may include '~' or env vars).

        Returns:
            str: Fully expanded absolute path to use for storing the Whoosh index.
        """
        path = os.path.expanduser(os.path.expandvars(v))
        return str(Path(path).resolve())

    @field_validator("monitored_paths", mode="before")
    @classmethod
    def _expand_monitored_paths(cls, v: List[str]) -> List[str]:
        """
        Normalize each monitored path before validation.

        For every entry in the monitored_paths list, this method will:
          1. Expand '~' to the home directory.
          2. Substitute environment variables (e.g. $DATA_DIR).
          3. Resolve to an absolute, canonical path.

        Args:
            v (List[str]): List of raw paths (strings) to monitor.

        Returns:
            List[str]: List of fully expanded absolute paths for monitoring.
        """
        return [
            str(Path(os.path.expanduser(os.path.expandvars(path))).resolve())
            for path in v
        ]

    def get_all_supported_extensions(self) -> Set[str]:
        """
        Return the union of text and document extensions
        that this indexer will process.
        """
        return self.supported_text_extensions | self.supported_document_extensions
