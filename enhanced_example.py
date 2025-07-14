#!/usr/bin/env python3
"""
Enhanced example usage of the DeepSearch system with vector embeddings
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepsearch.indexing import IndexingConfig
from deepsearch.indexing.enhanced_manager import EnhancedIndexingManager
from deepsearch.ai import AIConfig, EmbeddingConfig
from deepsearch.search.hybrid_search import HybridSearchManager


async def main():
    """Enhanced example showing hybrid search capabilities"""

    print("🔍 DeepSearch Enhanced Example")
    print("=" * 50)

    # Configure indexing
    indexing_config = IndexingConfig(
        monitored_paths=[
            str(Path.home() / "Documents"),
            # str(Path.home() / "Desktop"),
            # Add your specific paths here
        ],
        max_workers=2,
        batch_size=50,
    )

    # Configure AI/ML features
    ai_config = AIConfig(
        enable_embeddings=True,
        enable_hybrid_search=True,
        embedding=EmbeddingConfig(
            chunk_size=512,
            chunk_overlap=50,
            similarity_top_k=5,
            similarity_threshold=0.7,
        ),
    )

    print(f"📁 Monitoring paths: {indexing_config.monitored_paths}")
    print(
        f"🤖 Vector embeddings: {'✅ Enabled' if ai_config.enable_embeddings else '❌ Disabled'}"
    )
    print(
        f"🔗 Hybrid search: {'✅ Enabled' if ai_config.enable_hybrid_search else '❌ Disabled'}"
    )
    print()

    # Initialize the enhanced indexing system
    try:
        indexer = EnhancedIndexingManager(
            indexing_config=indexing_config, ai_config=ai_config
        )

        print("🚀 Starting enhanced indexing...")

        # Perform initial bulk indexing
        await indexer.bulk_index_enhanced(indexing_config.monitored_paths)

        # Show statistics
        stats = indexer.get_enhanced_stats()
        print("\n📊 Indexing Statistics:")
        print(f"   • Files processed: {stats['files_processed']}")
        print(f"   • Files failed: {stats['files_failed']}")
        print(
            f"   • Vector indexing: {'✅' if stats['vector_indexing_enabled'] else '❌'}"
        )

        if "vector_stats" in stats:
            vector_stats = stats["vector_stats"]
            print(f"   • Total chunks: {vector_stats.get('total_chunks', 0)}")
            print(f"   • Unique documents: {vector_stats.get('unique_documents', 0)}")

        # Initialize hybrid search
        search_manager = HybridSearchManager(
            indexing_config=indexing_config, ai_config=ai_config
        )

        print("\n🔍 Testing Search Capabilities:")
        print("-" * 30)

        # Example searches
        test_queries = [
            "machine learning",
            "python programming",
            "data analysis",
            "project management",
        ]

        for query in test_queries:
            print(f"\n🔎 Searching for: '{query}'")

            # Keyword search only
            keyword_results = search_manager.search(
                query=query, search_type="keyword", limit=3
            )

            # Semantic search only (if available)
            semantic_results = search_manager.search(
                query=query, search_type="semantic", limit=3
            )

            # Hybrid search
            hybrid_results = search_manager.search(
                query=query, search_type="hybrid", limit=3
            )

            print(f"   📝 Keyword results: {len(keyword_results)}")
            print(f"   🧠 Semantic results: {len(semantic_results)}")
            print(f"   🔗 Hybrid results: {len(hybrid_results)}")

            # Show top hybrid result if available
            if hybrid_results:
                top_result = hybrid_results[0]
                print(f"   🏆 Top result: {Path(top_result.path).name}")
                print(f"      Score: {top_result.combined_score:.3f}")
                if top_result.chunk_text:
                    preview = (
                        top_result.chunk_text[:100] + "..."
                        if len(top_result.chunk_text) > 100
                        else top_result.chunk_text
                    )
                    print(f"      Preview: {preview}")

        # Search statistics
        search_stats = search_manager.get_search_stats()
        print(f"\n📈 Search System Status:")
        print(f"   • Keyword search: ✅ Ready")
        print(
            f"   • Semantic search: {'✅ Ready' if search_stats['semantic_search_available'] else '❌ Not available'}"
        )

        print("\n✨ Enhanced indexing complete!")
        print(
            "💡 You can now use the hybrid search capabilities for both keyword and semantic search."
        )

        # Cleanup
        await indexer.stop_enhanced()
        search_manager.close()

    except Exception as e:
        print(f"❌ Error during enhanced indexing: {e}")
        import traceback

        traceback.print_exc()


async def simple_search_example():
    """Simple search example without indexing"""

    print("\n🔍 Simple Search Example")
    print("=" * 30)

    # Basic configuration for search only
    indexing_config = IndexingConfig()
    ai_config = AIConfig(enable_embeddings=True)

    try:
        search_manager = HybridSearchManager(
            indexing_config=indexing_config, ai_config=ai_config
        )

        # Example search
        query = "python programming"
        results = search_manager.search(query, limit=5)

        print(f"🔎 Search results for '{query}':")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {Path(result.path).name}")
            print(f"      Score: {result.combined_score:.3f}")
            print(f"      Type: {result.search_type}")

        search_manager.close()

    except Exception as e:
        print(f"❌ Search error: {e}")


if __name__ == "__main__":
    print("Choose an option:")
    print("1. Full enhanced indexing with vector embeddings")
    print("2. Simple search example")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(simple_search_example())
    else:
        print("Invalid choice. Running full example...")
        asyncio.run(main())
