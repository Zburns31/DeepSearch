"""
AI module for DeepSearch

This module provides:
- Document chunking for vector embeddings
- Vector database storage and similarity search
- Configuration for AI/ML components
"""

from .ai_config import AIConfig, EmbeddingConfig
from .chunking import DocumentChunker, DocumentChunk
from .embedding_db import VectorDatabase

__all__ = [
    "AIConfig",
    "EmbeddingConfig",
    "DocumentChunker",
    "DocumentChunk",
    "VectorDatabase",
]
