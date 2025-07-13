"""
Main indexing manager that coordinates all components
"""

import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

from watchdog.observers import Observer

from .config import IndexingConfig
from .extractor import TextExtractor
from .indexer import WhooshIndexer
from .logger import create_indexing_logger, create_performance_logger
from .models import IndexingJob, IndexingPriority
from .watcher import FileSystemWatcher
from .extraction_standalone import extract_text_standalone
from ..utils.file_utils import should_index_file, get_file_metadata


class SmartFileIndexer:
    """Main indexer class that coordinates everything"""

    def __init__(self, config: Optional[IndexingConfig] = None):
        self.config = config or IndexingConfig()
        self.logger = create_indexing_logger()
        self.performance_logger = create_performance_logger()
        self.text_extractor = TextExtractor(self.logger)
        self.whoosh_indexer = WhooshIndexer(self.config, self.logger)

        # Async components
        self.indexing_queue = asyncio.Queue(maxsize=10000)
        self.observer = Observer()
        self.watcher = FileSystemWatcher(self.indexing_queue)

        # Executors for CPU-bound work
        self.process_executor = ProcessPoolExecutor(max_workers=self.config.max_workers)
        self.thread_executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers * 2
        )

        self.is_running = False
        self.indexed_files: Set[str] = set()

        # Performance tracking
        self.stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "start_time": None,
        }

    async def process_file(self, file_path: str, operation: str):
        """Process a single file for indexing"""
        start_time = time.time()

        try:
            if operation == "delete":
                success = self.whoosh_indexer.delete_document(file_path)
                if success:
                    self.indexed_files.discard(file_path)
                    self.logger.debug(f"Deleted {file_path} from index")
                return

            # Check if file should be indexed
            if not should_index_file(file_path, self.config):
                self.stats["files_skipped"] += 1
                return

            # Get file metadata
            metadata = get_file_metadata(file_path)
            if not metadata:
                self.stats["files_failed"] += 1
                return

            # Extract text content (choose method based on configuration)
            if self.config.use_process_pool:
                # Use standalone function with ProcessPoolExecutor
                content, mime_type = await asyncio.get_event_loop().run_in_executor(
                    self.process_executor, extract_text_standalone, file_path
                )
            else:
                # Use ThreadPoolExecutor to avoid pickle issues
                content, mime_type = await asyncio.get_event_loop().run_in_executor(
                    self.thread_executor, self.text_extractor.extract_text, file_path
                )

            metadata.mime_type = mime_type

            # Add or update in index
            if operation == "create" or file_path not in self.indexed_files:
                success = self.whoosh_indexer.add_document(metadata, content)
                if success:
                    self.indexed_files.add(file_path)
                    self.stats["files_processed"] += 1
            else:
                success = self.whoosh_indexer.update_document(metadata, content)
                if success:
                    self.stats["files_processed"] += 1

            duration = time.time() - start_time
            self.logger.log_file_processed(file_path, metadata.size, duration)

        except Exception as e:
            self.stats["files_failed"] += 1
            self.logger.log_file_failed(file_path, e)

    async def process_queue(self):
        """Process indexing queue continuously"""
        while self.is_running:
            try:
                job = await asyncio.wait_for(self.indexing_queue.get(), timeout=1.0)
                await self.process_file(job.file_path, job.operation)
                self.indexing_queue.task_done()

                # Log progress periodically
                total_processed = (
                    self.stats["files_processed"] + self.stats["files_failed"]
                )
                if total_processed > 0 and total_processed % 100 == 0:
                    self._log_performance_stats()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing queue: {e}")

    def _log_performance_stats(self):
        """Log current performance statistics"""
        if self.stats["start_time"]:
            elapsed = time.time() - self.stats["start_time"]
            files_per_sec = (
                self.stats["files_processed"] / elapsed if elapsed > 0 else 0
            )
            mb_per_sec = (
                (self.stats.get("total_size_processed", 0) / (1024**2)) / elapsed
                if elapsed > 0
                else 0
            )

            # Log to both main logger and performance logger
            self.logger.info(
                f"Performance: {files_per_sec:.1f} files/sec, "
                f"Processed: {self.stats['files_processed']}, "
                f"Failed: {self.stats['files_failed']}, "
                f"Skipped: {self.stats['files_skipped']}"
            )

            self.performance_logger.info(
                f"STATS - Files/sec: {files_per_sec:.2f}, MB/sec: {mb_per_sec:.2f}, "
                f"Total processed: {self.stats['files_processed']}, "
                f"Total failed: {self.stats['files_failed']}, "
                f"Queue size: {self.indexing_queue.qsize()}"
            )

    async def bulk_index(self, root_paths: Optional[List[str]] = None):
        """Perform initial bulk indexing"""
        if root_paths is None:
            root_paths = self.config.monitored_paths

        self.logger.start_session()
        self.stats["start_time"] = time.time()
        self.logger.info(f"Starting bulk indexing of {root_paths}")

        # Discover all files
        all_files = []
        for root_path in root_paths:
            if not os.path.exists(root_path):
                self.logger.warning(f"Monitored path does not exist: {root_path}")
                continue

            self.logger.info(f"Scanning directory: {root_path}")

            for root, dirs, files in os.walk(root_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in self.config.excluded_dirs]

                for file in files:
                    file_path = os.path.join(root, file)
                    if should_index_file(file_path, self.config):
                        all_files.append(file_path)

                # Log progress for large directories
                if len(all_files) % 1000 == 0:
                    self.logger.log_directory_scan(root, len(all_files))

        total_files = len(all_files)
        self.logger.info(f"Found {total_files} files to index")

        if total_files == 0:
            self.logger.info("No files found to index")
            return

        # Process files in batches
        batch_count = 0
        for i in range(0, total_files, self.config.batch_size):
            batch = all_files[i : i + self.config.batch_size]
            batch_count += 1

            # Add batch to queue with low priority
            for file_path in batch:
                job = IndexingJob(
                    file_path=file_path,
                    priority=IndexingPriority.LOW,
                    operation="create",
                    timestamp=datetime.now(),
                )
                await self.indexing_queue.put(job)

            # Log progress
            if batch_count % 10 == 0:
                processed = min(i + self.config.batch_size, total_files)
                self.logger.log_progress(processed, total_files)

        # Wait for all files to be processed
        await self.indexing_queue.join()

        # Final summary
        summary = self.logger.get_session_summary()
        self.logger.log_session_summary()
        self.logger.info("Bulk indexing completed")

        return summary

    def start_monitoring(self):
        """Start file system monitoring"""
        for path in self.config.monitored_paths:
            if os.path.exists(path):
                self.observer.schedule(self.watcher, path, recursive=True)
                self.logger.info(f"Started monitoring: {path}")
            else:
                self.logger.warning(f"Cannot monitor non-existent path: {path}")

        self.observer.start()

    def stop_monitoring(self):
        """Stop file system monitoring"""
        self.observer.stop()
        self.observer.join()
        self.logger.info("Stopped file system monitoring")

    async def start(self, perform_bulk_index: bool = True):
        """Start the indexer"""
        self.is_running = True
        self.logger.info("Starting Smart File Indexer")

        # Start queue processing
        queue_task = asyncio.create_task(self.process_queue())

        # Start file system monitoring
        self.start_monitoring()

        # Perform initial bulk indexing if requested
        if perform_bulk_index:
            await self.bulk_index()

        try:
            await queue_task
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the indexer"""
        self.is_running = False
        self.stop_monitoring()

        # Wait for queue to finish
        try:
            await asyncio.wait_for(self.indexing_queue.join(), timeout=30.0)
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for queue to finish")

        # Shutdown executors
        self.process_executor.shutdown(wait=True)
        self.thread_executor.shutdown(wait=True)

        # Close the index
        self.whoosh_indexer.close()

        self.logger.info("Smart File Indexer stopped")

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search the index"""
        return self.whoosh_indexer.search(query, limit)

    def search_by_filename(self, filename_query: str, limit: int = 10) -> List[Dict]:
        """Search specifically in filenames"""
        return self.whoosh_indexer.search_by_filename(filename_query, limit)

    def get_stats(self) -> Dict:
        """Get indexer statistics"""
        index_stats = self.whoosh_indexer.get_index_stats()
        runtime_stats = {
            "files_processed": self.stats["files_processed"],
            "files_failed": self.stats["files_failed"],
            "files_skipped": self.stats["files_skipped"],
            "indexed_files_count": len(self.indexed_files),
            "queue_size": self.indexing_queue.qsize(),
            "is_running": self.is_running,
        }

        return {**index_stats, **runtime_stats}

    def optimize_index(self):
        """Optimize the search index"""
        self.whoosh_indexer.optimize_index()
