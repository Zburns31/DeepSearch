"""
Enhanced indexing manager with vector database support
"""

import asyncio
import time
from typing import Optional, List

from .manager import SmartFileIndexer
from .config import IndexingConfig
from .extraction_standalone import extract_text_standalone
from ..ai.ai_config import AIConfig
from ..ai.chunking import DocumentChunker
from ..ai.embedding_db import VectorDatabase
from ..utils.file_utils import should_index_file, get_file_metadata


class EnhancedIndexingManager(SmartFileIndexer):
    """Enhanced indexing manager that supports both keyword and vector indexing"""

    def __init__(
        self,
        indexing_config: Optional[IndexingConfig] = None,
        ai_config: Optional[AIConfig] = None,
    ):
        # Initialize base indexer
        super().__init__(indexing_config)

        # AI configuration
        self.ai_config = ai_config or AIConfig()

        # Initialize AI components if enabled
        if self.ai_config.enable_embeddings:
            try:
                self.document_chunker = DocumentChunker(
                    chunk_size=self.ai_config.embedding.chunk_size,
                    chunk_overlap=self.ai_config.embedding.chunk_overlap,
                )

                self.vector_db = VectorDatabase(self.ai_config.embedding, self.logger)

                self.logger.info("Vector database initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize vector components: {e}")
                self.document_chunker = None
                self.vector_db = None
        else:
            self.document_chunker = None
            self.vector_db = None
            self.logger.info("Vector indexing disabled in configuration")

    async def process_file(self, file_path: str, operation: str):
        """Enhanced file processing with vector indexing"""
        start_time = time.time()

        try:
            # Handle deletions
            if operation == "delete":
                # Delete from keyword index
                keyword_success = self.whoosh_indexer.delete_document(file_path)

                # Delete from vector database if available
                vector_success = True
                if self.vector_db:
                    vector_success = self.vector_db.delete_document_chunks(file_path)

                if keyword_success and vector_success:
                    self.indexed_files.discard(file_path)
                    self.logger.debug(f"Deleted {file_path} from both indexes")

                return

            # Process additions/updates with both indexers
            await self._process_file_enhanced(file_path, operation)

        except Exception as e:
            self.logger.error(f"Enhanced file processing failed for {file_path}: {e}")
            self.stats["files_failed"] += 1
        finally:
            processing_time = time.time() - start_time
            self.performance_logger.info(
                f"Enhanced processing completed - {file_path} - {operation} - {processing_time:.2f}s - vector_enabled: {self.vector_db is not None}"
            )

    async def _process_file_enhanced(self, file_path: str, operation: str):
        """Process file for both keyword and vector indexing"""

        # Check if file should be indexed
        if not should_index_file(file_path, self.config):
            self.stats["files_skipped"] += 1
            return

        # Get file metadata
        metadata = get_file_metadata(file_path)
        if not metadata:
            self.stats["files_failed"] += 1
            return

        # Extract text content
        if self.config.use_process_pool:
            content, mime_type = await asyncio.get_event_loop().run_in_executor(
                self.process_executor, extract_text_standalone, file_path
            )
        else:
            content, mime_type = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor, self.text_extractor.extract_text, file_path
            )

        metadata.mime_type = mime_type

        # Index in keyword search (Whoosh)
        keyword_success = False
        if operation == "create" or file_path not in self.indexed_files:
            keyword_success = self.whoosh_indexer.add_document(metadata, content)
        else:
            keyword_success = self.whoosh_indexer.update_document(metadata, content)

        # Index in vector database if available and content exists
        vector_success = True
        if self.vector_db and self.document_chunker and content and content.strip():
            try:
                # First, delete existing chunks for this document
                self.vector_db.delete_document_chunks(file_path)

                # Create document chunks
                file_metadata_dict = {
                    "filename": metadata.filename,
                    "extension": metadata.extension,
                    "file_type": metadata.file_type,
                    "mime_type": metadata.mime_type,
                    "size": metadata.size,
                    "modified_time": str(metadata.modified_time),
                    "created_time": str(metadata.created_time),
                }

                chunks = self.document_chunker.chunk_document(
                    content=content, source_path=file_path, metadata=file_metadata_dict
                )

                if chunks:
                    # Add chunks to vector database
                    vector_success = self.vector_db.add_chunks(chunks)

                    if vector_success:
                        self.logger.debug(
                            f"Added {len(chunks)} chunks to vector DB for {file_path}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to add chunks to vector DB for {file_path}"
                        )
                else:
                    self.logger.debug(f"No chunks created for {file_path}")

            except Exception as e:
                self.logger.error(f"Vector indexing failed for {file_path}: {e}")
                vector_success = False

        # Update statistics and tracking
        if keyword_success:
            self.indexed_files.add(file_path)
            self.stats["files_processed"] += 1

            if vector_success:
                self.logger.debug(f"Successfully indexed {file_path} in both systems")
            else:
                self.logger.warning(f"Indexed {file_path} in keyword search only")
        else:
            self.stats["files_failed"] += 1
            self.logger.error(f"Failed to index {file_path} in keyword search")

    def get_enhanced_stats(self) -> dict:
        """Get statistics from both indexing systems"""
        base_stats = self.get_stats()

        enhanced_stats = {
            **base_stats,
            "vector_indexing_enabled": self.vector_db is not None,
            "chunking_config": (
                {
                    "chunk_size": self.ai_config.embedding.chunk_size,
                    "chunk_overlap": self.ai_config.embedding.chunk_overlap,
                }
                if self.document_chunker
                else None
            ),
        }

        # Add vector database stats if available
        if self.vector_db:
            try:
                enhanced_stats["vector_stats"] = self.vector_db.get_database_stats()
            except Exception as e:
                self.logger.debug(f"Could not get vector database stats: {e}")
                enhanced_stats["vector_stats"] = {"error": str(e)}

        return enhanced_stats

    async def bulk_index_enhanced(self, paths: List[str]):
        """Enhanced bulk indexing that builds both indexes"""
        self.logger.info("Starting enhanced bulk indexing with vector indexing")

        await self.bulk_index(paths)

        if self.vector_db:
            vector_stats = self.vector_db.get_database_stats()
            self.logger.info(
                f"Enhanced bulk indexing completed. Vector DB contains {vector_stats.get('total_chunks', 0)} chunks "
                f"from {vector_stats.get('unique_documents', 0)} documents"
            )

    async def stop_enhanced(self):
        """Stop both indexing systems"""
        try:
            # Stop base components
            await self.stop()

            # Close vector database
            if self.vector_db:
                self.vector_db.close()

            self.logger.info("Enhanced indexing manager stopped")

        except Exception as e:
            self.logger.error(f"Error stopping enhanced indexing manager: {e}")
