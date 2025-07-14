"""
Hybrid search manager combining keyword and semantic search
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..indexing.indexer import WhooshIndexer
from ..indexing.config import IndexingConfig
from ..indexing.logger import create_search_logger, IndexingLogger
from ..ai.embedding_db import VectorDatabase
from ..ai.ai_config import AIConfig


@dataclass
class SearchResult:
    """Unified search result combining keyword and semantic search"""

    path: str
    filename: str
    file_type: str
    extension: str
    size: int
    modified_time: str

    # Keyword search specific
    keyword_score: float = 0.0
    keyword_rank: int = 0

    # Semantic search specific
    semantic_score: float = 0.0
    semantic_rank: int = 0
    chunk_text: Optional[str] = None
    chunk_id: Optional[str] = None

    # Combined score
    combined_score: float = 0.0
    search_type: str = "hybrid"  # "keyword", "semantic", or "hybrid"


class HybridSearchManager:
    """Manages both keyword (Whoosh) and semantic (Vector) search"""

    def __init__(
        self,
        indexing_config: IndexingConfig,
        ai_config: AIConfig,
        logger: Optional[IndexingLogger] = None,
    ):
        self.indexing_config = indexing_config
        self.ai_config = ai_config
        self.logger = logger or create_search_logger()

        # Initialize search engines
        self.keyword_searcher = WhooshIndexer(indexing_config, logger)

        if ai_config.enable_embeddings:
            try:
                self.vector_searcher = VectorDatabase(ai_config.embedding, logger)
            except Exception as e:
                self.logger.warning(f"Failed to initialize vector search: {e}")
                self.vector_searcher = None
        else:
            self.vector_searcher = None

    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 10,
        keyword_weight: float = 0.6,
        semantic_weight: float = 0.4,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining keyword and semantic results

        Args:
            query: Search query
            search_type: "keyword", "semantic", or "hybrid"
            limit: Maximum number of results
            keyword_weight: Weight for keyword search results (0-1)
            semantic_weight: Weight for semantic search results (0-1)

        Returns:
            List of unified search results
        """
        try:
            if search_type == "keyword":
                return self._keyword_search_only(query, limit)
            elif search_type == "semantic":
                return self._semantic_search_only(query, limit)
            else:
                return self._hybrid_search(
                    query, limit, keyword_weight, semantic_weight
                )

        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return []

    def _keyword_search_only(self, query: str, limit: int) -> List[SearchResult]:
        """Perform keyword-only search"""
        try:
            results = self.keyword_searcher.search(query, limit)

            search_results = []
            for i, result in enumerate(results):
                search_result = SearchResult(
                    path=result["path"],
                    filename=result["filename"],
                    file_type=result["file_type"],
                    extension=result["extension"],
                    size=result["size"],
                    modified_time=str(result["modified_time"]),
                    keyword_score=result["score"],
                    keyword_rank=i + 1,
                    combined_score=result["score"],
                    search_type="keyword",
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            self.logger.error(f"Keyword search failed: {e}")
            return []

    def _semantic_search_only(self, query: str, limit: int) -> List[SearchResult]:
        """Perform semantic-only search"""
        if not self.vector_searcher:
            self.logger.warning(
                "Vector search not available, falling back to keyword search"
            )
            return self._keyword_search_only(query, limit)

        try:
            results = self.vector_searcher.similarity_search(query, limit)

            search_results = []
            for i, result in enumerate(results):
                search_result = SearchResult(
                    path=result["source_path"],
                    filename=result["source_path"].split("/")[-1],  # Extract filename
                    file_type=result.get("metadata", {})
                    .get("file_metadata", {})
                    .get("file_type", "unknown"),
                    extension=result.get("metadata", {})
                    .get("file_metadata", {})
                    .get("extension", ""),
                    size=result.get("metadata", {})
                    .get("file_metadata", {})
                    .get("size", 0),
                    modified_time=result.get("metadata", {})
                    .get("file_metadata", {})
                    .get("modified_time", ""),
                    semantic_score=result["score"],
                    semantic_rank=i + 1,
                    chunk_text=result["text"],
                    chunk_id=result["chunk_id"],
                    combined_score=result["score"],
                    search_type="semantic",
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            return []

    def _hybrid_search(
        self, query: str, limit: int, keyword_weight: float, semantic_weight: float
    ) -> List[SearchResult]:
        """Perform hybrid search combining both approaches"""

        # Normalize weights
        total_weight = keyword_weight + semantic_weight
        if total_weight > 0:
            keyword_weight = keyword_weight / total_weight
            semantic_weight = semantic_weight / total_weight
        else:
            keyword_weight = 0.6
            semantic_weight = 0.4

        # Get results from both search types
        keyword_results = self._keyword_search_only(
            query, limit * 2
        )  # Get more to merge
        semantic_results = (
            self._semantic_search_only(query, limit * 2) if self.vector_searcher else []
        )

        # Combine and rank results
        combined_results = self._combine_search_results(
            keyword_results, semantic_results, keyword_weight, semantic_weight
        )

        # Return top results
        return combined_results[:limit]

    def _combine_search_results(
        self,
        keyword_results: List[SearchResult],
        semantic_results: List[SearchResult],
        keyword_weight: float,
        semantic_weight: float,
    ) -> List[SearchResult]:
        """Combine and rank results from both search types"""

        # Create a map to merge results by file path
        results_map: Dict[str, SearchResult] = {}

        # Add keyword results
        for result in keyword_results:
            results_map[result.path] = result

        # Merge semantic results
        for semantic_result in semantic_results:
            path = semantic_result.path

            if path in results_map:
                # Merge with existing keyword result
                existing = results_map[path]
                existing.semantic_score = semantic_result.semantic_score
                existing.semantic_rank = semantic_result.semantic_rank
                existing.chunk_text = semantic_result.chunk_text
                existing.chunk_id = semantic_result.chunk_id
                existing.search_type = "hybrid"

                # Calculate combined score
                existing.combined_score = (
                    keyword_weight * existing.keyword_score
                    + semantic_weight * existing.semantic_score
                )
            else:
                # Add as semantic-only result
                semantic_result.search_type = "semantic"
                semantic_result.combined_score = (
                    semantic_weight * semantic_result.semantic_score
                )
                results_map[path] = semantic_result

        # Convert to list and sort by combined score
        combined_results = list(results_map.values())
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)

        return combined_results

    def search_by_filename(
        self, filename_query: str, limit: int = 10
    ) -> List[SearchResult]:
        """Search specifically in filenames using keyword search"""
        try:
            results = self.keyword_searcher.search_by_filename(filename_query, limit)

            search_results = []
            for i, result in enumerate(results):
                search_result = SearchResult(
                    path=result["path"],
                    filename=result["filename"],
                    file_type=result["file_type"],
                    extension=result["extension"],
                    size=result["size"],
                    modified_time=str(result["modified_time"]),
                    keyword_score=result["score"],
                    keyword_rank=i + 1,
                    combined_score=result["score"],
                    search_type="filename",
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            self.logger.error(f"Filename search failed: {e}")
            return []

    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about both search indexes"""
        stats = {
            "keyword_search": self.keyword_searcher.get_index_stats(),
            "semantic_search_available": self.vector_searcher is not None,
        }

        if self.vector_searcher:
            stats["semantic_search"] = self.vector_searcher.get_database_stats()

        return stats

    def close(self):
        """Close both search engines"""
        try:
            self.keyword_searcher.close()
            if self.vector_searcher:
                self.vector_searcher.close()
            self.logger.debug("Hybrid search manager closed")
        except Exception as e:
            self.logger.error(f"Error closing hybrid search manager: {e}")
