"""
DeepSearch Utilities Module
"""

from .file_utils import (
    should_index_file,
    get_file_metadata,
    calculate_file_hash,
    is_text_file,
    is_document_file,
    get_file_size_human,
    safe_file_operation,
    safe_stat,
    safe_exists,
)

__all__ = [
    "should_index_file",
    "get_file_metadata",
    "calculate_file_hash",
    "is_text_file",
    "is_document_file",
    "get_file_size_human",
    "safe_file_operation",
    "safe_stat",
    "safe_exists",
]
