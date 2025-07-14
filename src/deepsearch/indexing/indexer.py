"""
Whoosh-based search indexer
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from whoosh import fields, index
from whoosh.qparser import QueryParser

from .config import IndexingConfig
from .logger import create_search_logger, IndexingLogger
from .models import FileMetadata


class WhooshIndexer:
    """Manages Whoosh search index"""

    def __init__(self, config: IndexingConfig, logger: Optional[IndexingLogger] = None):
        self.config = config
        self.logger = logger or create_search_logger()
        # Expand the ~ to the actual home directory
        self.index_dir = Path(config.index_dir).expanduser()
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Define schema
        self.schema = fields.Schema(
            path=fields.ID(stored=True, unique=True),
            filename=fields.TEXT(stored=True),
            content=fields.TEXT(stored=False),  # Don't store content, just index it
            extension=fields.KEYWORD(stored=True),
            file_type=fields.KEYWORD(stored=True),
            mime_type=fields.KEYWORD(stored=True),
            size=fields.NUMERIC(stored=True),
            modified_time=fields.DATETIME(stored=True),
            created_time=fields.DATETIME(stored=True),
            content_hash=fields.ID(stored=True),
            indexed_time=fields.DATETIME(stored=True),
        )

        # Create or open index
        self._initialize_index()

    def _initialize_index(self):
        """Initialize the Whoosh index"""
        try:
            if index.exists_in(str(self.index_dir)):
                self.ix = index.open_dir(str(self.index_dir))
                self.logger.info(f"Opened existing index at {self.index_dir}")
            else:
                self.ix = index.create_in(str(self.index_dir), self.schema)
                self.logger.info(f"Created new index at {self.index_dir}")
        except Exception as e:
            self.logger.error(f"Failed to initialize index: {e}")
            raise

    def add_document(self, metadata: FileMetadata, content: str) -> bool:
        """
        Add a document to the index

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.ix.writer() as writer:
                writer.add_document(
                    path=metadata.path,
                    filename=metadata.filename,
                    content=content,
                    extension=metadata.extension,
                    file_type=metadata.file_type,
                    mime_type=metadata.mime_type,
                    size=metadata.size,
                    modified_time=metadata.modified_time,
                    created_time=metadata.created_time,
                    content_hash=metadata.content_hash,
                    indexed_time=datetime.now(),
                )
            return True
        except Exception as e:
            self.logger.log_file_failed(metadata.path, e)
            return False

    def update_document(self, metadata: FileMetadata, content: str) -> bool:
        """
        Update a document in the index

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.ix.writer() as writer:
                writer.update_document(
                    path=metadata.path,
                    filename=metadata.filename,
                    content=content,
                    extension=metadata.extension,
                    file_type=metadata.file_type,
                    mime_type=metadata.mime_type,
                    size=metadata.size,
                    modified_time=metadata.modified_time,
                    created_time=metadata.created_time,
                    content_hash=metadata.content_hash,
                    indexed_time=datetime.now(),
                )
            return True
        except Exception as e:
            self.logger.log_file_failed(metadata.path, e)
            return False

    def delete_document(self, file_path: str) -> bool:
        """
        Delete a document from the index

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.ix.writer() as writer:
                deleted = writer.delete_by_term("path", file_path)
                return deleted > 0
        except Exception as e:
            self.logger.log_file_failed(file_path, e)
            return False

    def document_exists(self, file_path: str) -> bool:
        """Check if a document exists in the index"""
        try:
            with self.ix.searcher() as searcher:
                query = QueryParser("path", self.ix.schema).parse(f'"{file_path}"')
                results = searcher.search(query, limit=1)
                return len(results) > 0
        except Exception as e:
            self.logger.debug(f"Error checking document existence for {file_path}: {e}")
            return False

    def get_document_hash(self, file_path: str) -> Optional[str]:
        """Get the stored content hash for a document"""
        # Note: This is a simplified version - in practice you'd need to
        # properly handle Whoosh Hit objects
        try:
            # For now, just return None - we can implement proper hash checking later
            return None
        except Exception as e:
            self.logger.debug(f"Error getting document hash for {file_path}: {e}")
            return None

    def search(self, query_string: str, limit: int = 10) -> List[Dict]:
        """
        Search the index

        Args:
            query_string: The search query
            limit: Maximum number of results to return

        Returns:
            List of search results as dictionaries
        """
        try:
            with self.ix.searcher() as searcher:
                # Parse query with multiple fields
                parser = QueryParser("content", self.ix.schema)
                query = parser.parse(query_string)
                results = searcher.search(query, limit=limit)

                return [
                    {
                        "path": result["path"],
                        "filename": result["filename"],
                        "extension": result["extension"],
                        "file_type": result["file_type"],
                        "mime_type": result["mime_type"],
                        "size": result["size"],
                        "modified_time": result["modified_time"],
                        "created_time": result["created_time"],
                        "indexed_time": result["indexed_time"],
                        "score": result.score,
                    }
                    for result in results
                ]
        except Exception as e:
            self.logger.error(f"Search failed for query '{query_string}': {e}")
            return []

    def search_by_filename(self, filename_query: str, limit: int = 10) -> List[Dict]:
        """Search specifically in filenames"""
        try:
            with self.ix.searcher() as searcher:
                parser = QueryParser("filename", self.ix.schema)
                query = parser.parse(filename_query)
                results = searcher.search(query, limit=limit)

                return [
                    {
                        "path": result["path"],
                        "filename": result["filename"],
                        "extension": result["extension"],
                        "file_type": result["file_type"],
                        "size": result["size"],
                        "modified_time": result["modified_time"],
                        "score": result.score,
                    }
                    for result in results
                ]
        except Exception as e:
            self.logger.error(
                f"Filename search failed for query '{filename_query}': {e}"
            )
            return []

    def get_index_stats(self) -> Dict:
        """Get statistics about the index"""
        try:
            with self.ix.searcher() as searcher:
                doc_count = searcher.doc_count()

                # Get some basic stats by searching all documents
                total_size = 0
                file_types = {}

                # Use a wildcard query to get all documents
                from whoosh.query import Every

                all_docs = searcher.search(Every(), limit=None)

                for doc in all_docs:
                    total_size += doc.get("size", 0)
                    file_type = doc.get("file_type", "unknown")
                    file_types[file_type] = file_types.get(file_type, 0) + 1

                return {
                    "total_documents": doc_count,
                    "total_size_gb": total_size / (1024**3),
                    "file_types": file_types,
                    "index_path": str(self.index_dir),
                }
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {e}")
            return {}

    def optimize_index(self):
        """Optimize the index for better performance"""
        try:
            with self.ix.writer() as writer:
                writer.commit(optimize=True)
            self.logger.info("Index optimization completed")
        except Exception as e:
            self.logger.error(f"Index optimization failed: {e}")

    def close(self):
        """Close the index"""
        try:
            if hasattr(self, "ix"):
                self.ix.close()
                self.logger.debug("Index closed")
        except Exception as e:
            self.logger.error(f"Error closing index: {e}")
