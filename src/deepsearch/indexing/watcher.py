"""
File system monitoring using watchdog
"""

import asyncio
from datetime import datetime

from watchdog.events import FileSystemEventHandler

from .models import IndexingJob, IndexingPriority


class FileSystemWatcher(FileSystemEventHandler):
    """Handles file system events using watchdog"""

    def __init__(self, indexing_queue: asyncio.Queue):
        self.indexing_queue = indexing_queue
        super().__init__()

    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            file_path = str(event.src_path)
            asyncio.create_task(
                self._add_to_queue(file_path, "create", IndexingPriority.HIGH)
            )

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            file_path = str(event.src_path)
            asyncio.create_task(
                self._add_to_queue(file_path, "update", IndexingPriority.HIGH)
            )

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory:
            file_path = str(event.src_path)
            asyncio.create_task(
                self._add_to_queue(file_path, "delete", IndexingPriority.HIGH)
            )

    def on_moved(self, event):
        """Handle file move/rename events"""
        if not event.is_directory:
            # Handle as delete + create
            src_path = str(event.src_path)
            dest_path = str(event.dest_path)
            asyncio.create_task(
                self._add_to_queue(src_path, "delete", IndexingPriority.HIGH)
            )
            asyncio.create_task(
                self._add_to_queue(dest_path, "create", IndexingPriority.HIGH)
            )

    async def _add_to_queue(
        self, file_path: str, operation: str, priority: IndexingPriority
    ):
        """Add indexing job to queue"""
        job = IndexingJob(
            file_path=file_path,
            priority=priority,
            operation=operation,
            timestamp=datetime.now(),
        )
        try:
            await self.indexing_queue.put(job)
        except Exception as e:
            # If queue is full or there's another error, we'll just skip this event
            # In a production system, you might want to handle this differently
            pass
