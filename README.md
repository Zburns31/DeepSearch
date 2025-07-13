# DeepSearch - Intelligent File System Indexing

This project is a high-performance desktop search tool, similar to macOS Spotlight, built to provide an intelligent search layer for your local files. It works by:

- Indexing Locally: Creates a comprehensive index of your documents, PDFs, and text files.

- AI-Powered Queries: Connects to local LLMs with Ollama or remote APIs (OpenAI, etc.) to allow natural language conversations with your data.

- Finding Anything: Go beyond simple keyword matching. Ask questions, find concepts, and get exact answers from the contents of your files.

## Features

- **Real-time File Monitoring**: Uses `watchdog` to monitor file system changes and automatically index new, modified, or deleted files
- **Multi-format Support**: Extracts text from PDF, Word documents, Excel files, PowerPoint presentations, and various text formats
- **Fast Search**: Powered by Whoosh search engine for quick full-text search capabilities
- **Intelligent Filtering**: Configurable rules to exclude system files, temporary files, and irrelevant directories
- **Performance Optimized**: Async processing with configurable worker pools for efficient indexing
- **Comprehensive Logging**: Module-specific logging with dedicated directories for indexing, extraction, search, monitoring, performance metrics, and error tracking
- **Mac-specific Optimization**: Designed specifically for macOS file systems and conventions

## Architecture

The system is organized into clean, modular components:

```
deepsearch/
├── example.py             # Complete usage example
├── test_system.py         # System integration tests
├── src/
│   └── deepsearch/
│       ├── __init__.py
│       ├── indexing/
│       │   ├── __init__.py
│       │   ├── config.py                  # Configuration management
│       │   ├── extraction_standalone.py   # Standalone extraction utilities
│       │   ├── extractor.py               # Text extraction from various file types
│       │   ├── indexer.py                 # Whoosh search index management
│       │   ├── logger.py                  # Module-specific logging with factory functions
│       │   ├── manager.py                 # Main coordinator (SmartFileIndexer)
│       │   ├── models.py                  # Data models (FileMetadata, IndexingJob, etc.)
│       │   └── watcher.py                 # File system monitoring with watchdog
│       ├── ai/                            # AI integration components
│       ├── search/                        # Search interface components
│       ├── ui/                            # User interface components
│       └── utils/
│           ├── __init__.py
│           └── file_utils.py          # File utility functions
└── tests/
    ├── test_logging.py    # Logging system tests
    └── test_system.py     # System integration tests
```

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd deepsearch
   ```

2. **Install dependencies**:

   ```bash
   uv sync
   ```

3. **Activate the virtual environment**:

   ```bash
   uv shell
   ```

## Quick Start

### Basic Usage

```python
import asyncio
from deepsearch import SmartFileIndexer, IndexingConfig

async def main():
    # Create configuration
    config = IndexingConfig(
        monitored_paths=["/Users/yourname/Documents"],
        max_workers=4,
        batch_size=100
    )

    # Create and start indexer
    indexer = SmartFileIndexer(config)

    try:
        await indexer.start()
    except KeyboardInterrupt:
        await indexer.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Search Examples

```python
from deepsearch import SmartFileIndexer, IndexingConfig

# Initialize indexer
config = IndexingConfig()
indexer = SmartFileIndexer(config)

# Search for content
results = indexer.search("python programming", limit=10)
for result in results:
    print(f"{result['filename']}: {result['score']:.2f}")

# Search by filename
filename_results = indexer.search_by_filename("README", limit=5)

# Get index statistics
stats = indexer.get_stats()
print(f"Total documents: {stats['total_documents']}")
```

## Configuration

The `IndexingConfig` class provides extensive customization options:

```python
config = IndexingConfig(
    # Where to store the search index
    index_dir="~/.deepsearch_index",

    # Maximum file size to index (100MB default)
    max_file_size=100 * 1024 * 1024,

    # Number of worker processes
    max_workers=4,

    # Files to process in each batch
    batch_size=100,

    # File extensions to exclude
    excluded_extensions={".tmp", ".log", ".cache", ".DS_Store"},

    # Directories to exclude
    excluded_dirs={".git", "__pycache__", "node_modules", ".venv"},

    # Paths to monitor
    monitored_paths=["/Users/yourname/Documents", "/Users/yourname/Desktop"]
)
```

## Supported File Types

### Text Files

- Plain text (`.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, etc.)
- Configuration files (`.json`, `.yaml`, `.toml`, `.ini`, etc.)
- Source code files (various programming languages)

### Documents

- PDF files (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- Microsoft Excel (`.xlsx`, `.xls`)
- Microsoft PowerPoint (`.pptx`, `.ppt`)

## Components Overview

### SmartFileIndexer (Main Class)

The central coordinator that manages all other components:

- Handles async queue processing
- Coordinates file system monitoring
- Manages bulk indexing operations
- Provides search interface
- Uses specialized loggers for different operations

### Enhanced Architecture Features

- **Modular Design**: Clean separation of concerns across indexing, search, AI, and UI components
- **Async Processing**: Efficient handling of large file collections
- **Factory Pattern**: Standardized logger creation for consistent module-specific logging
- **Optional Dependencies**: Components can accept optional logger instances for flexibility
- **Thread Safety**: ThreadPoolExecutor used for text extraction to avoid serialization issues

### IndexingLogger

Enhanced logging system with module-specific organization:

- **Module-Specific Directories**: Separate log directories for indexing, extraction, search, monitoring, performance, and errors
- **Factory Functions**: Easy creation of specialized loggers with `create_indexing_logger()`, `create_extraction_logger()`, etc.
- **Performance Tracking**: Dedicated performance logger for timing and metrics
- **Error Segregation**: Automatic error log segregation across all modules
- **Flexible Configuration**: Custom module loggers with `create_module_logger()`
- **Organized Structure**: Logs stored in `~/.deepsearch_logs/` with subdirectories

### TextExtractor

Handles text extraction from various file formats:

- PDF text extraction using PyPDF2
- Word document processing with python-docx
- Excel file processing with openpyxl
- PowerPoint text extraction with python-pptx
- Intelligent encoding detection for text files

### WhooshIndexer

Manages the Whoosh search index:

- Creates and maintains search schema
- Handles document addition, updating, and deletion
- Provides search capabilities
- Manages index optimization

### FileSystemWatcher

Real-time file system monitoring:

- Uses watchdog for efficient file monitoring
- Handles create, modify, delete, and move operations
- Queues changes for processing
- Supports recursive directory monitoring

## Running the Example

The repository includes a complete example:

```bash
# Run the indexer
python example.py

# Run search examples
python example.py search
```

## Performance Considerations

- **Indexing Speed**: Typically processes 50-200 files per second depending on file sizes and types
- **Memory Usage**: Configurable batch sizes help control memory consumption
- **Storage**: The search index typically uses 5-10% of the original file sizes
- **CPU Usage**: Configurable worker processes allow tuning for your system

## Logging and Monitoring

DeepSearch provides comprehensive, module-specific logging:

### Log Directory Structure

All logs are organized in `~/.deepsearch_logs/` with dedicated subdirectories:

- **`indexing/`**: Main indexing operations and coordination
- **`extraction/`**: Text extraction from various file formats
- **`search/`**: Search operations and query processing
- **`monitoring/`**: File system monitoring and change detection
- **`performance/`**: Performance metrics and timing data
- **`errors/`**: Centralized error logs from all modules
- **`general/`**: General application logs

### Logger Factory Functions

```python
from deepsearch.indexing.logger import (
    create_indexing_logger,
    create_extraction_logger,
    create_search_logger,
    create_monitoring_logger,
    create_performance_logger,
    create_module_logger
)

# Create specialized loggers
indexing_logger = create_indexing_logger()
extraction_logger = create_extraction_logger()

# Create custom module logger
custom_logger = create_module_logger("my_module", "my_logger")
```

### Logging Features

- **Progress Tracking**: Real-time progress updates during bulk indexing
- **Performance Metrics**: Files per second, MB per second processing rates
- **Error Reporting**: Detailed error logs with automatic segregation
- **Session Summaries**: Complete statistics after indexing operations
- **Module Isolation**: Separate logs for different system components

## Error Handling

The system is designed to be robust:

- Individual file processing errors don't stop the overall indexing
- Graceful handling of permission errors and corrupted files
- Automatic retry mechanisms for transient errors
- Comprehensive error logging for debugging


## Troubleshooting

### Common Issues

1. **Permission Errors**: Make sure the indexer has read permissions for monitored directories
2. **Large Files**: Adjust `max_file_size` in configuration if needed
3. **Performance**: Tune `max_workers` and `batch_size` for your system
4. **Disk Space**: Monitor index directory size, especially with large document collections

### Debug Mode

Enable debug logging for specific modules:

```python
import logging

# Enable debug for all deepsearch components
logging.getLogger("deepsearch").setLevel(logging.DEBUG)

# Enable debug for specific modules
logging.getLogger("deepsearch_indexer").setLevel(logging.DEBUG)
logging.getLogger("deepsearch_extractor").setLevel(logging.DEBUG)
logging.getLogger("deepsearch_search").setLevel(logging.DEBUG)
```

### Testing the Logging System

Run the logging test to verify all components:

```bash
python tests/test_logging.py
```

This will create sample logs in all module directories to verify the logging system is working correctly.

## Future Enhancements

### Planned Features

- AI-powered semantic search integration
- Web interface for search and management
- Cloud synchronization capabilities
- Additional file format support
- Machine learning-based relevance scoring

### Recently Implemented

- ✅ **Module-specific logging system** with organized directory structure
- ✅ **Factory pattern for logger creation** with specialized loggers
- ✅ **Enhanced error handling** with centralized error logging
- ✅ **Performance tracking** with dedicated performance metrics
- ✅ **Flexible architecture** supporting optional logger dependencies
