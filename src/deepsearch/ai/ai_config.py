"""
AI and embedding configuration
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configuration for embedding models and vector storage"""

    # Embedding model settings
    model_name: str = Field(
        default="BAAI/bge-small-en-v1.5", description="HuggingFace embedding model name"
    )

    # Vector database settings
    vector_db_path: str = Field(
        default="~/.deepsearch_vectors", description="Path to store vector database"
    )

    # Chunking settings
    chunk_size: int = Field(
        default=512, description="Size of text chunks for embedding"
    )

    chunk_overlap: int = Field(default=50, description="Overlap between chunks")

    # Search settings
    similarity_top_k: int = Field(
        default=5, description="Number of similar chunks to retrieve"
    )

    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity score for results"
    )

    # Performance settings
    batch_size: int = Field(
        default=10, description="Batch size for embedding generation"
    )

    def get_vector_db_path(self) -> Path:
        """Get the expanded vector database path"""
        return Path(self.vector_db_path).expanduser()


class AIConfig(BaseModel):
    """Main AI configuration"""

    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    # Feature flags
    enable_embeddings: bool = Field(
        default=True, description="Enable embedding-based similarity search"
    )

    enable_hybrid_search: bool = Field(
        default=True, description="Enable hybrid keyword + semantic search"
    )

    # Model caching
    cache_models: bool = Field(
        default=True, description="Cache embedding models in memory"
    )
