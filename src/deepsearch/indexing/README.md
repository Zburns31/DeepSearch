# DeepSearch Indexing Module

This document explains how the DeepSearch indexing system works and what information it stores.

## How It Works - Core Components

### 1. File Monitoring & Detection (`watcher.py`)

- Uses the `watchdog` library to monitor your file system in real-time
- Detects when files are created, modified, or deleted
- Automatically queues these changes for processing
- Supports recursive directory monitoring

### 2. Text Extraction (`extractor.py`)

Extracts readable text from various file formats:

- **PDFs** (using PyPDF2)
- **Word documents** (.docx, .doc using python-docx)
- **Excel files** (.xlsx, .xls using openpyxl)
- **PowerPoint** (.pptx, .ppt using python-pptx)
- **Plain text files** (.txt, .md, .py, .js, etc.)
- Handles encoding detection for text files
- Uses ThreadPoolExecutor for parallel processing

### 3. Search Indexing (`indexer.py`)

- Creates a Whoosh search index for fast full-text search
- Stores file metadata and makes content searchable
- Supports both content search and filename search

### 4. Coordination (`manager.py`)

- The main orchestrator (`SmartFileIndexer` class)
- Manages async queues for processing files
- Coordinates between monitoring, extraction, and indexing
- Handles bulk indexing and real-time updates

### 5. Logging System (`logger.py`)

- Module-specific logging with organized directory structure
- Performance metrics tracking
- Error reporting and debugging support

## What Information Gets Stored

### In the Whoosh Index (`~/.deepsearch_index/`)

**File Metadata:**

- `path`: Full file path
- `filename`: Just the filename
- `extension`: File extension (.pdf, .txt, etc.)
- `file_type`: Type classification
- `mime_type`: MIME type
- `size`: File size in bytes
- `modified_time`: When file was last modified
- `created_time`: When file was created
- `content_hash`: Hash for duplicate detection
- `indexed_time`: When it was indexed

**Content:**

- Full extracted text content (indexed but not stored)

### In Log Files (`~/.deepsearch_logs/`)

- **`indexing/`**: Main indexing operations
- **`extraction/`**: Text extraction details and errors
- **`search/`**: Search operations and performance
- **`monitoring/`**: File system monitoring events
- **`performance/`**: Speed metrics, files/sec processed
- **`errors/`**: All error logs consolidated

## Data Flow Process

1. **File System Event** → Watchdog detects file change
2. **Queue Processing** → Event added to processing queue
3. **Text Extraction** → Content extracted based on file type
4. **Metadata Creation** → File metadata collected
5. **Index Update** → Whoosh index updated with content + metadata
6. **Logging** → All operations logged to appropriate modules

## Search Capabilities

Currently supports:

- **Full-text search** in file contents
- **Filename search**
- **File type filtering**
- **Date range queries**
- **Performance statistics**

## Configuration & Customization

The system is highly configurable via `IndexingConfig`:

- Which directories to monitor
- File size limits
- Excluded file types/directories
- Worker process counts
- Performance tuning parameters

## Key Features

### Real-time Processing

- Automatically indexes new files as they're created
- Updates index when files are modified
- Removes entries when files are deleted

### Performance Optimized

- Async processing with configurable worker pools
- Batch processing for efficiency
- ThreadPoolExecutor for parallel text extraction
- Configurable batch sizes and worker counts

### Robust Error Handling

- Individual file failures don't stop overall processing
- Comprehensive error logging
- Graceful handling of permission errors and corrupted files

### Extensible Architecture

- Clean separation of concerns
- Factory pattern for logger creation
- Modular design supporting future AI enhancements