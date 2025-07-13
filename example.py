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
        # Customize these paths for your system
        monitored_paths=[
            str(Path.home() / "Documents"),
            # str(Path.home() / "Desktop"),
            # Add more paths as needed
        ],
        max_workers=2,  # Reduce for testing
        batch_size=50,
        # You can customize excluded directories and file types
        excluded_dirs={
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            ".virtualenv",
            ".tox",
            ".pytest_cache",
            ".mypy_cache",
            "Library",
            "System",
            ".Trash",
            ".npm",
            ".cache",
            ".deepsearch_index",  # Don't index our own index
        },
    )

    # Create indexer
    indexer = SmartFileIndexer(config)

    print("Starting DeepSearch File Indexer...")
    print(f"Monitoring paths: {config.monitored_paths}")
    print("Press Ctrl+C to stop\n")

    try:
        # Start the indexer (this will do initial bulk indexing)
        await indexer.start(perform_bulk_index=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        await indexer.stop()

    print("Indexer stopped")


def search_example():
    """Example of searching the index"""
    config = IndexingConfig()
    indexer = SmartFileIndexer(config)

    # Example searches
    queries = ["python", "configuration", "README", "project"]

    print("Search Examples:")
    print("=" * 50)

    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = indexer.search(query, limit=5)

        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']}")
                print(f"     Path: {result['path']}")
                print(f"     Score: {result['score']:.2f}")
        else:
            print("  No results found")

    # Get index statistics
    stats = indexer.get_stats()
    print(f"\nIndex Statistics:")
    print(f"  Total documents: {stats.get('total_documents', 0)}")
    print(f"  Total size: {stats.get('total_size_gb', 0):.2f} GB")
    print(f"  Files processed: {stats.get('files_processed', 0)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        # Run search example
        search_example()
    else:
        # Run the main indexer
        asyncio.run(main())
