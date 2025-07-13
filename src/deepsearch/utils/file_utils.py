"""
File utility functions for the indexing system
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..indexing.config import IndexingConfig
from ..indexing.models import FileMetadata


def should_index_file(file_path: str, config: IndexingConfig) -> bool:
    """
    Check if file should be indexed based on configuration rules

    Args:
        file_path: Path to the file
        config: Indexing configuration

    Returns:
        bool: True if file should be indexed, False otherwise
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        return False

    # Check file extension
    if path.suffix.lower() in config.excluded_extensions:
        return False

    # Check if in excluded directory
    for excluded_dir in config.excluded_dirs:
        if excluded_dir in path.parts:
            return False

    # Check file size
    try:
        if path.stat().st_size > config.max_file_size:
            return False
    except OSError:
        return False

    return True


def get_file_metadata(file_path: str) -> Optional[FileMetadata]:
    """
    Get metadata for a file

    Args:
        file_path: Path to the file

    Returns:
        FileMetadata object or None if failed
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return None

        stat = path.stat()

        # Calculate content hash for duplicate detection
        content_hash = calculate_file_hash(file_path)
        if content_hash is None:
            return None

        return FileMetadata(
            path=str(path.resolve()),
            filename=path.name,
            extension=path.suffix.lower(),
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            created_time=datetime.fromtimestamp(stat.st_ctime),
            file_type=path.suffix.lower()[1:] if path.suffix else "unknown",
            mime_type="",  # Will be filled by text extractor
            content_hash=content_hash,
        )
    except Exception:
        return None


def calculate_file_hash(file_path: str, chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate MD5 hash of file content

    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read for large files

    Returns:
        MD5 hash string or None if failed
    """
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None


def is_text_file(file_path: str) -> bool:
    """
    Check if file is likely a text file based on extension

    Args:
        file_path: Path to the file

    Returns:
        bool: True if likely a text file
    """
    text_extensions = {
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
        ".log",
        ".csv",
        ".tsv",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".kt",
        ".swift",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".pl",
        ".r",
        ".scala",
        ".clj",
        ".hs",
        ".elm",
        ".fs",
        ".ml",
        ".ex",
        ".exs",
        ".lua",
        ".dart",
        ".ts",
    }

    return Path(file_path).suffix.lower() in text_extensions


def is_document_file(file_path: str) -> bool:
    """
    Check if file is a supported document type

    Args:
        file_path: Path to the file

    Returns:
        bool: True if supported document type
    """
    doc_extensions = {
        ".pdf",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
    }

    return Path(file_path).suffix.lower() in doc_extensions


def get_file_size_human(size_bytes: int) -> str:
    """
    Convert file size in bytes to human readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def safe_file_operation(func):
    """
    Decorator for safe file operations that handles common exceptions
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (OSError, IOError, PermissionError):
            return None

    return wrapper


@safe_file_operation
def safe_stat(file_path: str):
    """Safely get file stats"""
    return os.stat(file_path)


@safe_file_operation
def safe_exists(file_path: str):
    """Safely check if file exists"""
    return os.path.exists(file_path)
