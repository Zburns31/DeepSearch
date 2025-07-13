#!/usr/bin/env python3
"""
Simple test script for DeepSearch indexing system
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from deepsearch.indexing import SmartFileIndexer, IndexingConfig

    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you've installed dependencies with: uv sync")
    sys.exit(1)


def test_basic_functionality():
    """Test basic functionality without async"""
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)

    try:
        # Create a simple config for testing
        config = IndexingConfig(
            monitored_paths=[str(Path.home() / "Desktop")],  # Just desktop for testing
            max_workers=1,
            batch_size=10,
        )
        print(f"✅ Config created: {config.index_dir}")

        # Create indexer
        indexer = SmartFileIndexer(config)
        print("✅ Indexer created successfully")

        # Test search (even on empty index)
        results = indexer.search("test", limit=5)
        print(f"✅ Search works (found {len(results)} results)")

        # Get stats
        stats = indexer.get_stats()
        print(f"✅ Stats: {stats.get('total_documents', 0)} documents indexed")

        print("\n🎉 All basic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_indexing():
    """Test actual indexing functionality"""
    print("\n📁 Testing File Indexing")
    print("=" * 50)

    try:
        # Create config for a small test directory
        test_path = str(Path.home() / "Desktop")  # Small directory for testing
        config = IndexingConfig(
            monitored_paths=[test_path],
            max_workers=1,
            batch_size=5,
            excluded_dirs={
                ".git",
                "__pycache__",
                "node_modules",
                ".venv",
                ".deepsearch_index",
            },
        )

        indexer = SmartFileIndexer(config)
        print(f"🔍 Will index files in: {test_path}")

        # Do a quick bulk index
        print("🚀 Starting indexing...")
        await indexer.bulk_index()

        # Get final stats
        stats = indexer.get_stats()
        print(f"📊 Indexing complete!")
        print(f"   - Documents indexed: {stats.get('total_documents', 0)}")
        print(f"   - Files processed: {stats.get('files_processed', 0)}")
        print(f"   - Files failed: {stats.get('files_failed', 0)}")

        # Test search
        if stats.get("total_documents", 0) > 0:
            print("\n🔍 Testing search...")
            results = indexer.search("*", limit=3)
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result['filename']} (score: {result['score']:.2f})")

        await indexer.stop()
        print("✅ Indexing test completed successfully!")

    except Exception as e:
        print(f"❌ Indexing test failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main test function"""
    print("🧪 DeepSearch System Test")
    print("=" * 50)

    # Test 1: Basic functionality
    if not test_basic_functionality():
        print("❌ Basic tests failed - check your installation")
        return

    # Test 2: Ask user if they want to test indexing
    print(f"\n📁 Ready to test file indexing on your Desktop folder?")
    print("This will create a search index but won't modify your files.")

    response = input("Continue with indexing test? (y/N): ").lower().strip()

    if response in ["y", "yes"]:
        # Test 2: Actual indexing
        asyncio.run(test_indexing())
    else:
        print("⏭️  Skipping indexing test")

    print(f"\n🎯 How to use the system:")
    print("=" * 50)
    print("1. Edit example.py to customize paths and settings")
    print("2. Run: python example.py")
    print("3. Or create your own script using the examples below")

    print(f"\n📋 Quick Usage Examples:")
    print(
        """
# Basic usage:
from deepsearch.indexing import SmartFileIndexer, IndexingConfig

config = IndexingConfig(monitored_paths=["/Users/yourname/Documents"])
indexer = SmartFileIndexer(config)

# Search:
results = indexer.search("python programming")
for result in results:
    print(f"{result['filename']}: {result['score']}")

# Async indexing:
await indexer.start()  # This will index and monitor files
"""
    )


if __name__ == "__main__":
    main()
