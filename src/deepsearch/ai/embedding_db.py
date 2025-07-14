"""
Vector database for storing and searching document embeddings
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import sqlite3
from datetime import datetime

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.vector_stores import SimpleVectorStore

from .ai_config import EmbeddingConfig
from .chunking import DocumentChunk
from ..indexing.logger import create_search_logger, IndexingLogger


class VectorDatabase:
    """Manages vector storage and similarity search for document chunks"""

    def __init__(
        self, config: EmbeddingConfig, logger: Optional[IndexingLogger] = None
    ):
        self.config = config
        self.logger = logger or create_search_logger()

        # Setup paths
        self.vector_db_path = config.get_vector_db_path()
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.vector_db_path / "vector_index"
        self.metadata_db_path = self.vector_db_path / "metadata.db"

        # Initialize embedding model
        self._initialize_embedding_model()

        # Initialize vector store and index
        self._initialize_vector_store()

        # Initialize metadata database
        self._initialize_metadata_db()

    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        try:
            self.logger.info(f"Embedding model configuration: {self.config.model_name}")

            # For now, use the default LlamaIndex embedding model
            # This can be extended later when specific embedding packages are available
            self.logger.info("Using default LlamaIndex embedding model")

        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def _initialize_vector_store(self):
        """Initialize the vector store and index"""
        try:
            # Create storage context
            if self.index_path.exists():
                # Load existing index
                self.storage_context = StorageContext.from_defaults(
                    persist_dir=str(self.index_path)
                )
                self.index = VectorStoreIndex.from_vector_store(
                    self.storage_context.vector_store,
                    storage_context=self.storage_context,
                )
                self.logger.info(f"Loaded existing vector index from {self.index_path}")
            else:
                # Create new index
                self.storage_context = StorageContext.from_defaults()
                self.index = VectorStoreIndex([], storage_context=self.storage_context)
                self.logger.info("Created new vector index")

        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

    def _initialize_metadata_db(self):
        """Initialize SQLite database for chunk metadata"""
        try:
            self.metadata_conn = sqlite3.connect(
                str(self.metadata_db_path), check_same_thread=False
            )

            # Create metadata table
            self.metadata_conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_metadata (
                    chunk_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    start_char INTEGER,
                    end_char INTEGER,
                    text_preview TEXT,
                    file_metadata TEXT,
                    indexed_time TIMESTAMP,
                    embedding_model TEXT
                )
            """
            )

            # Create index for faster queries
            self.metadata_conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_source_path
                ON chunk_metadata(source_path)
            """
            )

            self.metadata_conn.commit()
            self.logger.info("Metadata database initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize metadata database: {e}")
            raise

    def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """
        Add document chunks to the vector database

        Args:
            chunks: List of DocumentChunk objects to add

        Returns:
            bool: True if successful, False otherwise
        """
        if not chunks:
            return True

        try:
            # Convert chunks to LlamaIndex documents
            documents = [chunk.to_llama_document() for chunk in chunks]

            # Add to vector index
            for doc in documents:
                self.index.insert(doc)

            # Store metadata in SQLite
            for chunk in chunks:
                self._store_chunk_metadata(chunk)

            # Persist the index
            self.index.storage_context.persist(persist_dir=str(self.index_path))

            self.logger.info(f"Added {len(chunks)} chunks to vector database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add chunks to vector database: {e}")
            return False

    def _store_chunk_metadata(self, chunk: DocumentChunk):
        """Store chunk metadata in SQLite database"""
        try:
            # Create text preview (first 200 chars)
            text_preview = (
                chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            )

            self.metadata_conn.execute(
                """
                INSERT OR REPLACE INTO chunk_metadata
                (chunk_id, source_path, chunk_index, start_char, end_char,
                 text_preview, file_metadata, indexed_time, embedding_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    chunk.chunk_id,
                    chunk.source_path,
                    chunk.chunk_index,
                    chunk.start_char,
                    chunk.end_char,
                    text_preview,
                    json.dumps(chunk.metadata),
                    datetime.now(),
                    self.config.model_name,
                ),
            )

            self.metadata_conn.commit()

        except Exception as e:
            self.logger.error(
                f"Failed to store metadata for chunk {chunk.chunk_id}: {e}"
            )

    def similarity_search(
        self, query: str, top_k: Optional[int] = None, threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector database

        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of search results with metadata
        """
        try:
            top_k = top_k or self.config.similarity_top_k
            threshold = threshold or self.config.similarity_threshold

            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="no_text",  # We just want the source nodes
            )

            # Perform search
            response = query_engine.query(query)

            results = []
            for node in response.source_nodes:
                # Get additional metadata from SQLite
                chunk_metadata = self._get_chunk_metadata(node.id_)

                result = {
                    "chunk_id": node.id_,
                    "text": node.text,
                    "score": node.score if hasattr(node, "score") else 0.0,
                    "source_path": node.metadata.get("source_path"),
                    "chunk_index": node.metadata.get("chunk_index"),
                    "start_char": node.metadata.get("start_char"),
                    "end_char": node.metadata.get("end_char"),
                    "metadata": chunk_metadata,
                }

                # Apply threshold filter
                if result["score"] >= threshold:
                    results.append(result)

            self.logger.info(f"Similarity search returned {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Similarity search failed: {e}")
            return []

    def _get_chunk_metadata(self, chunk_id: str) -> Dict[str, Any]:
        """Get chunk metadata from SQLite database"""
        try:
            cursor = self.metadata_conn.execute(
                """
                SELECT file_metadata, indexed_time, embedding_model
                FROM chunk_metadata WHERE chunk_id = ?
            """,
                (chunk_id,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "file_metadata": json.loads(row[0]) if row[0] else {},
                    "indexed_time": row[1],
                    "embedding_model": row[2],
                }

            return {}

        except Exception as e:
            self.logger.debug(f"Failed to get metadata for chunk {chunk_id}: {e}")
            return {}

    def delete_document_chunks(self, source_path: str) -> bool:
        """
        Delete all chunks for a specific document

        Args:
            source_path: Path to the source document

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get chunk IDs for this document
            cursor = self.metadata_conn.execute(
                """
                SELECT chunk_id FROM chunk_metadata WHERE source_path = ?
            """,
                (source_path,),
            )

            chunk_ids = [row[0] for row in cursor.fetchall()]

            if not chunk_ids:
                return True

            # Delete from vector index
            for chunk_id in chunk_ids:
                try:
                    self.index.delete_ref_doc(chunk_id, delete_from_docstore=True)
                except Exception as e:
                    self.logger.debug(
                        f"Could not delete chunk {chunk_id} from index: {e}"
                    )

            # Delete from metadata database
            self.metadata_conn.execute(
                """
                DELETE FROM chunk_metadata WHERE source_path = ?
            """,
                (source_path,),
            )

            self.metadata_conn.commit()

            # Persist the updated index
            self.index.storage_context.persist(persist_dir=str(self.index_path))

            self.logger.info(
                f"Deleted {len(chunk_ids)} chunks for document {source_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete chunks for {source_path}: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            # Get metadata stats
            cursor = self.metadata_conn.execute(
                """
                SELECT
                    COUNT(*) as total_chunks,
                    COUNT(DISTINCT source_path) as unique_documents,
                    embedding_model
                FROM chunk_metadata
                GROUP BY embedding_model
            """
            )

            metadata_stats = cursor.fetchall()

            # Get file type distribution
            cursor = self.metadata_conn.execute(
                """
                SELECT
                    json_extract(file_metadata, '$.file_type') as file_type,
                    COUNT(*) as count
                FROM chunk_metadata
                WHERE json_extract(file_metadata, '$.file_type') IS NOT NULL
                GROUP BY file_type
            """
            )

            file_type_stats = dict(cursor.fetchall())

            return {
                "total_chunks": metadata_stats[0][0] if metadata_stats else 0,
                "unique_documents": metadata_stats[0][1] if metadata_stats else 0,
                "embedding_model": metadata_stats[0][2] if metadata_stats else None,
                "file_type_distribution": file_type_stats,
                "vector_db_path": str(self.vector_db_path),
                "index_path": str(self.index_path),
            }

        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}

    def close(self):
        """Close the database connections"""
        try:
            if hasattr(self, "metadata_conn"):
                self.metadata_conn.close()
            self.logger.debug("Vector database closed")
        except Exception as e:
            self.logger.error(f"Error closing vector database: {e}")
