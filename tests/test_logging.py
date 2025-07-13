#!/usr/bin/env python3
"""
Test script for the new logging system with module-specific directories
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from deepsearch.indexing.logger import (
    create_indexing_logger,
    create_extraction_logger,
    create_search_logger,
    create_monitoring_logger,
    create_performance_logger,
    create_module_logger,
)


def test_logging_system():
    """Test all logger types"""
    print("Testing logging system...")

    # Test indexing logger
    indexing_logger = create_indexing_logger()
    indexing_logger.info("Testing indexing logger")
    indexing_logger.warning("This is a warning from indexing")

    # Test extraction logger
    extraction_logger = create_extraction_logger()
    extraction_logger.info("Testing extraction logger")
    extraction_logger.error("This is an error from extraction")

    # Test search logger
    search_logger = create_search_logger()
    search_logger.info("Testing search logger")
    search_logger.debug("This is a debug message from search")

    # Test monitoring logger
    monitoring_logger = create_monitoring_logger()
    monitoring_logger.info("Testing monitoring logger")
    monitoring_logger.warning("System status check")

    # Test performance logger
    performance_logger = create_performance_logger()
    performance_logger.info("Testing performance logger")
    performance_logger.info("Operation took 1.23 seconds")

    # Test custom module logger
    custom_logger = create_module_logger("test_module", "test_logger")
    custom_logger.info("Testing custom module logger")
    custom_logger.error("Custom module error")

    print("\nLogging test completed!")
    print("Check the following directories for log files:")
    print("- ~/.deepsearch_logs/indexing/")
    print("- ~/.deepsearch_logs/extraction/")
    print("- ~/.deepsearch_logs/search/")
    print("- ~/.deepsearch_logs/monitoring/")
    print("- ~/.deepsearch_logs/performance/")
    print("- ~/.deepsearch_logs/test_module/")
    print("- ~/.deepsearch_logs/errors/")


if __name__ == "__main__":
    test_logging_system()
