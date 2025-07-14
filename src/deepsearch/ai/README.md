# AI Module - Vector Embeddings and Semantic Search

This module adds advanced AI capabilities to DeepSearch, enabling semantic search through document embeddings and chunking.

## Features

### Document Chunking
- **Smart Text Splitting**: Uses LlamaIndex's SentenceSplitter for intelligent document chunking
- **Configurable Chunk Size**: Adjustable chunk size and overlap for optimal embedding performance
- **Metadata Preservation**: Maintains file metadata and chunk relationships
- **Content Cleaning**: Automatic text cleaning and normalization

### Vector Database
- **Embedding Storage**: Stores document chunks as vector embeddings
- **Similarity Search**: Fast semantic search using vector similarity
- **Metadata Integration**: SQLite database for chunk metadata and relationships
- **Multiple Models**: Support for different embedding models via HuggingFace

### Hybrid Search
- **Combined Results**: Merges keyword and semantic search results
- **Weighted Scoring**: Configurable weights for keyword vs semantic results
- **Unified Interface**: Single search interface for multiple search types
- **Performance Optimized**: Parallel execution of different search methods

## Architecture

```
ai/
├── __init__.py              # Module exports
├── ai_config.py            # Configuration classes
├── chunking.py             # Document chunking logic
├── embedding_db.py         # Vector database management
└── README.md               # This file
```

## Configuration

### EmbeddingConfig
```python
from deepsearch.ai import EmbeddingConfig

config = EmbeddingConfig(
    model_name="BAAI/bge-small-en-v1.5",  # HuggingFace model
    vector_db_path="~/.deepsearch_vectors",  # Storage location
    chunk_size=512,                       # Characters per chunk
    chunk_overlap=50,                     # Overlap between chunks
    similarity_top_k=5,                   # Results per search
    similarity_threshold=0.7              # Minimum similarity score
)
```

### AIConfig
```python
from deepsearch.ai import AIConfig

ai_config = AIConfig(
    enable_embeddings=True,      # Enable vector search
    enable_hybrid_search=True,   # Enable combined search
    embedding=embedding_config   # Embedding configuration
)
```

## Usage Examples

### Basic Document Chunking
```python
from deepsearch.ai import DocumentChunker

chunker = DocumentChunker(chunk_size=512, chunk_overlap=50)

chunks = chunker.chunk_document(
    content="Your document content here...",
    source_path="/path/to/document.txt",
    metadata={"file_type": "text", "size": 1024}
)

print(f"Created {len(chunks)} chunks")
```

### Vector Database Operations
```python
from deepsearch.ai import VectorDatabase, EmbeddingConfig

config = EmbeddingConfig()
vector_db = VectorDatabase(config)

# Add chunks to database
success = vector_db.add_chunks(chunks)

# Search for similar content
results = vector_db.similarity_search(
    query="machine learning concepts",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text'][:100]}...")
```

### Hybrid Search
```python
from deepsearch.search.hybrid_search import HybridSearchManager
from deepsearch.indexing import IndexingConfig

search_manager = HybridSearchManager(
    indexing_config=IndexingConfig(),
    ai_config=AIConfig()
)

# Perform hybrid search
results = search_manager.search(
    query="python programming",
    search_type="hybrid",  # "keyword", "semantic", or "hybrid"
    limit=10
)

for result in results:
    print(f"File: {result.filename}")
    print(f"Combined Score: {result.combined_score:.3f}")
    print(f"Search Type: {result.search_type}")
```

## Data Storage

### Vector Index
- **Location**: `~/.deepsearch_vectors/vector_index/`
- **Format**: LlamaIndex vector store format
- **Contents**: Document embeddings and vector search index

### Metadata Database
- **Location**: `~/.deepsearch_vectors/metadata.db`
- **Format**: SQLite database
- **Schema**:
  ```sql
  CREATE TABLE chunk_metadata (
      chunk_id TEXT PRIMARY KEY,
      source_path TEXT NOT NULL,
      chunk_index INTEGER NOT NULL,
      start_char INTEGER,
      end_char INTEGER,
      text_preview TEXT,
      file_metadata TEXT,
      indexed_time TIMESTAMP,
      embedding_model TEXT
  );
  ```

### Model Cache
- **Location**: `~/.deepsearch_vectors/model_cache/`
- **Contents**: Downloaded HuggingFace models
- **Purpose**: Avoid re-downloading models

## Integration with Indexing

The AI module integrates seamlessly with the existing indexing system:

1. **Enhanced Manager**: `EnhancedIndexingManager` extends the base indexer
2. **Dual Indexing**: Files are indexed in both Whoosh and vector databases
3. **Synchronized Updates**: File changes update both indexes
4. **Unified Search**: Single interface for all search types

## Performance Considerations

### Memory Usage
- **Embedding Models**: ~500MB-2GB depending on model size
- **Vector Index**: ~10-50MB per 1000 documents
- **Chunk Storage**: Minimal overhead with SQLite

### Processing Speed
- **Chunking**: ~1000 chunks/second
- **Embedding**: ~100-500 chunks/second (GPU accelerated)
- **Search**: <100ms for most queries

### Optimization Tips
1. **Chunk Size**: Smaller chunks = better precision, larger chunks = better context
2. **Model Selection**: Smaller models = faster processing, larger models = better quality
3. **Batch Processing**: Process multiple files together for better throughput
4. **GPU Acceleration**: Use CUDA-enabled models for faster embedding generation

## Error Handling

The module includes comprehensive error handling:

- **Model Loading**: Graceful fallback to default models
- **Database Errors**: Transaction rollback and retry logic
- **Search Failures**: Fallback to keyword-only search
- **Chunking Issues**: Skip problematic documents with logging

## Future Enhancements

- **Multiple Embedding Models**: Support for different models per file type
- **Incremental Updates**: Only re-embed changed chunks
- **Advanced Chunking**: Semantic-aware chunking strategies
- **Query Expansion**: Automatic query enhancement for better results
- **Clustering**: Document clustering and topic modeling
- **Multilingual Support**: Language-specific embedding models
