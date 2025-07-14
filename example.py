#!/usr/bin/env python3
"""
Example usage of the DeepSearch indexing system
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepsearch.indexing import SmartFileIndexer, IndexingConfig


async def main():
    """Example usage of the Smart File Indexer"""

    # Create configuration
    config = IndexingConfig(
        # Where to store the Whoosh index (will expand ~ and ENV vars)
        index_dir=str(Path.home() / ".deepsearch_index"),
        # Folders to monitor for changes
        monitored_paths=[
            str(Path("/Users/zacburns/Documents/Undergrad Notes/")),
            # str(Path.home() / "Documents"),
            # str(Path.home() / "Desktop"),
        ],
        # Skip these directories entirely
        excluded_dirs={
            ".git",
            "__pycache__",
            "node_modules",
            ".Trash",
        },
        # Skip these file extensions entirely
        excluded_extensions={
            ".tmp",
            ".log",
            ".cache",
        },
        # Only extract text from these extensions
        supported_text_extensions={
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
        },
        # Only extract binary docs from these extensions
        supported_document_extensions={
            ".pdf",
            ".docx",
            ".pptx",
        },
        # Concurrency tuning
        max_workers=2,  # lower for testing
        batch_size=50,
        max_file_size=100 * 1024 * 1024,  # 100 MB
        use_process_pool=False,
    )

    print("Starting DeepSearch File Indexer...")
    print(f"  Index directory: {config.index_dir}")
    print(f"  Monitoring paths: {config.monitored_paths}")
    print(f"  Skipping extensions: {config.excluded_extensions}")
    print(f"  Supported for text: {config.supported_text_extensions}")
    print(f"  Supported for docs: {config.supported_document_extensions}")
    print("Press Ctrl+C to stop\n")

    # Create indexer
    indexer = SmartFileIndexer(config)

    try:
        # Start the indexer (does initial bulk index then watches)
        await indexer.start(perform_bulk_index=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        await indexer.stop()

    print("Indexer stopped\n")


def search_example():
    """Example of searching the index"""
    # Use Pydantic defaults at runtime, ignore the linter here
    cfg = IndexingConfig()  # type: ignore[call]
    idx = SmartFileIndexer(cfg)

    queries = ["python", "configuration", "README", "project"]
    print("Search Examples:")
    print("=" * 50)

    for q in queries:
        print(f"\nSearching for: '{q}'")
        results = idx.search(q, limit=5)
        if results:
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r['filename']} (score {r['score']:.2f})")
                print(f"     → {r['path']}")
        else:
            print("  No results found")

    stats = idx.get_stats()
    print("\nIndex Statistics:")
    print(f"  Total documents:    {stats.get('total_documents', 0)}")
    print(f"  Total size (GB):    {stats.get('total_size_gb', 0):.2f}")
    print(f"  Files processed:    {stats.get('files_processed', 0)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        search_example()
    else:
        asyncio.run(main())
