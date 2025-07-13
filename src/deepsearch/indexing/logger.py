"""
Specialized logging module for indexing operations
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class IndexingLogger:
    """Specialized logger for indexing operations with metrics tracking"""

    def __init__(self, name: str = "deepsearch_indexer", module_name: str = "general"):
        self.logger = logging.getLogger(name)
        self.module_name = module_name
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

        # Metrics tracking
        self.metrics = {
            "files_processed": 0,
            "files_failed": 0,
            "total_size_processed": 0,
            "start_time": None,
            "errors": [],
        }

    def _setup_handlers(self):
        """Setup logging handlers with module-specific directories"""
        # Create main log directory structure
        base_log_dir = Path.home() / ".deepsearch_logs"
        base_log_dir.mkdir(exist_ok=True)

        # Create module-specific subdirectories
        module_dirs = {
            "indexing": base_log_dir / "indexing",
            "extraction": base_log_dir / "extraction",
            "search": base_log_dir / "search",
            "monitoring": base_log_dir / "monitoring",
            "general": base_log_dir / "general",
            "performance": base_log_dir / "performance",
            "errors": base_log_dir / "errors",
        }

        # Create all subdirectories
        for dir_path in module_dirs.values():
            dir_path.mkdir(exist_ok=True)

        # Determine which directory to use based on module name
        if self.module_name in module_dirs:
            log_dir = module_dirs[self.module_name]
        else:
            log_dir = module_dirs["general"]

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(module_name)s] - %(message)s"
        )

        simple_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # Module-specific file handler
        module_log_file = log_dir / f"{self.module_name}.log"
        file_handler = logging.FileHandler(module_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Error-specific handler (all errors go to errors directory)
        error_log_file = module_dirs["errors"] / f"{self.module_name}_errors.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Performance handler (if this is a performance-related logger)
        if (
            "performance" in self.module_name.lower()
            or "stats" in self.module_name.lower()
        ):
            perf_log_file = (
                module_dirs["performance"] / f"{self.module_name}_performance.log"
            )
            perf_handler = logging.FileHandler(perf_log_file)
            perf_handler.setLevel(logging.INFO)
            perf_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(perf_handler)

        # Add custom filter to include module_name in log records
        class ModuleFilter(logging.Filter):
            def __init__(self, module_name):
                super().__init__()
                self.module_name = module_name

            def filter(self, record):
                record.module_name = self.module_name
                return True

        module_filter = ModuleFilter(self.module_name)
        file_handler.addFilter(module_filter)
        error_handler.addFilter(module_filter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)

    def start_session(self):
        """Start a new indexing session"""
        self.metrics["start_time"] = time.time()
        self.metrics["files_processed"] = 0
        self.metrics["files_failed"] = 0
        self.metrics["total_size_processed"] = 0
        self.metrics["errors"] = []
        self.logger.info("Starting indexing session")

    def log_file_processed(self, file_path: str, size: int, duration: float):
        """Log successful file processing"""
        self.metrics["files_processed"] += 1
        self.metrics["total_size_processed"] += size
        self.logger.debug(f"Processed {file_path} ({size} bytes) in {duration:.2f}s")

    def log_file_failed(self, file_path: str, error: Exception):
        """Log failed file processing"""
        self.metrics["files_failed"] += 1
        self.metrics["errors"].append((file_path, str(error)))
        self.logger.error(f"Failed to process {file_path}: {error}")

    def log_progress(self, processed: int, total: int):
        """Log indexing progress"""
        percentage = (processed / total) * 100 if total > 0 else 0
        self.logger.info(f"Progress: {processed}/{total} files ({percentage:.1f}%)")

    def log_directory_scan(self, directory: str, file_count: int):
        """Log directory scanning progress"""
        self.logger.info(f"Scanning directory: {directory} ({file_count} files found)")

    def log_indexing_stats(self, files_per_second: float, mb_per_second: float):
        """Log performance statistics"""
        self.logger.info(
            f"Performance: {files_per_second:.1f} files/sec, "
            f"{mb_per_second:.1f} MB/sec"
        )

    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        elapsed = (
            time.time() - self.metrics["start_time"]
            if self.metrics["start_time"]
            else 0
        )

        total_files = self.metrics["files_processed"] + self.metrics["files_failed"]

        return {
            "files_processed": self.metrics["files_processed"],
            "files_failed": self.metrics["files_failed"],
            "total_size_gb": self.metrics["total_size_processed"] / (1024**3),
            "elapsed_time": elapsed,
            "files_per_second": (
                self.metrics["files_processed"] / elapsed if elapsed > 0 else 0
            ),
            "mb_per_second": (
                (self.metrics["total_size_processed"] / (1024**2)) / elapsed
                if elapsed > 0
                else 0
            ),
            "error_rate": (
                self.metrics["files_failed"] / total_files if total_files > 0 else 0
            ),
            "recent_errors": self.metrics["errors"][-10:],  # Last 10 errors
        }

    def log_session_summary(self):
        """Log the session summary"""
        summary = self.get_session_summary()
        self.logger.info(f"Session Summary: {summary}")

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)


# Factory functions for different logger types
def create_indexing_logger() -> IndexingLogger:
    """Create a logger for indexing operations"""
    return IndexingLogger("deepsearch_indexer", "indexing")


def create_extraction_logger() -> IndexingLogger:
    """Create a logger for text extraction operations"""
    return IndexingLogger("deepsearch_extractor", "extraction")


def create_search_logger() -> IndexingLogger:
    """Create a logger for search operations"""
    return IndexingLogger("deepsearch_search", "search")


def create_monitoring_logger() -> IndexingLogger:
    """Create a logger for file system monitoring"""
    return IndexingLogger("deepsearch_monitor", "monitoring")


def create_performance_logger() -> IndexingLogger:
    """Create a logger for performance metrics"""
    return IndexingLogger("deepsearch_performance", "performance")


def create_module_logger(
    module_name: str, logger_name: Optional[str] = None
) -> IndexingLogger:
    """Create a logger for a specific module"""
    if logger_name is None:
        logger_name = f"deepsearch_{module_name}"
    return IndexingLogger(logger_name, module_name)


def get_log_directory_info() -> dict:
    """Get information about the logging directory structure"""
    base_log_dir = Path.home() / ".deepsearch_logs"

    log_info = {
        "base_directory": str(base_log_dir),
        "subdirectories": {
            "indexing": str(base_log_dir / "indexing"),
            "extraction": str(base_log_dir / "extraction"),
            "search": str(base_log_dir / "search"),
            "monitoring": str(base_log_dir / "monitoring"),
            "general": str(base_log_dir / "general"),
            "performance": str(base_log_dir / "performance"),
            "errors": str(base_log_dir / "errors"),
        },
    }

    # Check which directories exist and have log files
    for name, path in log_info["subdirectories"].items():
        dir_path = Path(path)
        if dir_path.exists():
            log_files = list(dir_path.glob("*.log"))
            log_info["subdirectories"][name] = {
                "path": path,
                "exists": True,
                "log_files": [f.name for f in log_files],
                "file_count": len(log_files),
            }
        else:
            log_info["subdirectories"][name] = {
                "path": path,
                "exists": False,
                "log_files": [],
                "file_count": 0,
            }

    return log_info
