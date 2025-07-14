"""
Document chunking utilities for vector embedding
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from llama_index.core.text_splitter import SentenceSplitter
from llama_index.core import Document


@dataclass
class DocumentChunk:
    """Represents a chunk of document content"""

    text: str
    chunk_id: str
    source_path: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]

    def to_llama_document(self) -> Document:
        """Convert to LlamaIndex Document format"""
        metadata = {
            **self.metadata,
            "chunk_id": self.chunk_id,
            "source_path": self.source_path,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }

        return Document(text=self.text, metadata=metadata, id_=self.chunk_id)


class DocumentChunker:
    """Handles document chunking for vector embedding"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize LlamaIndex text splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=" ",
        )

    def chunk_document(
        self, content: str, source_path: str, metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        Chunk a document into smaller pieces for embedding

        Args:
            content: The document content to chunk
            source_path: Path to the source file
            metadata: Additional metadata about the document

        Returns:
            List of DocumentChunk objects
        """
        if not content or not content.strip():
            return []

        # Clean the content
        cleaned_content = self._clean_content(content)

        # Split into chunks using LlamaIndex
        text_chunks = self.text_splitter.split_text(cleaned_content)

        chunks = []
        current_pos = 0

        for i, chunk_text in enumerate(text_chunks):
            # Find the position of this chunk in the original text
            start_char = cleaned_content.find(chunk_text, current_pos)
            if start_char == -1:
                start_char = current_pos

            end_char = start_char + len(chunk_text)
            current_pos = end_char - self.chunk_overlap

            # Create chunk ID
            chunk_id = f"{source_path}:chunk:{i}"

            # Create the chunk
            chunk = DocumentChunk(
                text=chunk_text.strip(),
                chunk_id=chunk_id,
                source_path=source_path,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                metadata=metadata.copy(),
            )

            chunks.append(chunk)

        return chunks

    def _clean_content(self, content: str) -> str:
        """Clean document content for better chunking"""
        # Remove excessive whitespace
        content = re.sub(r"\s+", " ", content)

        # Remove special characters that might interfere with chunking
        content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", content)

        # Normalize line breaks
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        return content.strip()

    def chunk_multiple_documents(
        self, documents: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk multiple documents at once

        Args:
            documents: List of dicts with 'content', 'path', and 'metadata' keys

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(
                content=doc["content"],
                source_path=doc["path"],
                metadata=doc.get("metadata", {}),
            )
            all_chunks.extend(chunks)

        return all_chunks

    def get_chunk_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Get statistics about the chunks"""
        if not chunks:
            return {}

        chunk_lengths = [len(chunk.text) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "total_characters": sum(chunk_lengths),
            "unique_sources": len(set(chunk.source_path for chunk in chunks)),
        }
