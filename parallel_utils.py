#!/usr/bin/env python3
"""
Common utilities for parallel processing operations
Provides shared functionality for parallel processing tasks
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track and report progress for long-running operations."""
    
    def __init__(self, total_items: int, description: str = "Processing"):
        self.total_items = total_items
        self.completed_items = 0
        self.description = description
        self.start_time = time.time()
        self.last_report_time = 0
        self.report_interval = 1.0  # seconds
        
        logger.info(f"Starting {description} of {total_items} items")
    
    def update(self, increment: int = 1, item_name: str = None):
        """Update progress and optionally report status."""
        self.completed_items += increment
        current_time = time.time()
        
        # Report progress periodically
        if (current_time - self.last_report_time) >= self.report_interval or self.completed_items == self.total_items:
            self.report(item_name)
            self.last_report_time = current_time
    
    def report(self, item_name: str = None):
        """Report current progress."""
        if self.total_items == 0:
            percentage = 0
        else:
            percentage = (self.completed_items / self.total_items) * 100
        
        elapsed_time = time.time() - self.start_time
        
        if self.completed_items > 0:
            estimated_total_time = elapsed_time * self.total_items / self.completed_items
            remaining_time = estimated_total_time - elapsed_time
            time_info = f", ETA: {remaining_time:.1f}s"
        else:
            time_info = ""
        
        item_info = f" - {item_name}" if item_name else ""
        
        logger.info(f"{self.description}: {self.completed_items}/{self.total_items} "
                   f"({percentage:.1f}%){time_info}{item_info}")
    
    def complete(self):
        """Mark as completed and report final stats."""
        total_time = time.time() - self.start_time
        logger.info(f"{self.description} completed: {self.completed_items}/{self.total_items} "
                   f"in {total_time:.2f}s")


class OperationTimer:
    """Simple timer for measuring operation duration."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if exc_type is None:
            logger.info(f"{self.operation_name} completed in {duration:.2f}s")
        else:
            logger.error(f"{self.operation_name} failed after {duration:.2f}s: {exc_val}")
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time


def validate_parallel_config(
    max_workers: Optional[int] = None,
    operation_cost: str = "medium"
) -> Dict[str, Any]:
    """
    Validate and optimize parallel processing configuration.
    
    Args:
        max_workers: Requested number of workers
        operation_cost: Cost level of operations ("low", "medium", "high")
    
    Returns:
        Dict with validated configuration
    """
    cpu_count = os.cpu_count() or 1
    
    # Determine optimal worker count based on operation cost
    if operation_cost == "low":
        # I/O bound operations can use more workers
        suggested_workers = min(32, cpu_count * 2)
    elif operation_cost == "medium":
        # Mixed operations
        suggested_workers = min(16, cpu_count + 4)
    else:  # high cost
        # CPU intensive operations should use fewer workers
        suggested_workers = min(8, cpu_count)
    
    # Use requested workers if specified, otherwise use suggested
    final_workers = max_workers if max_workers is not None else suggested_workers
    
    # Ensure at least 1 worker and not more than CPU count for CPU-bound work
    if operation_cost == "high":
        final_workers = min(final_workers, cpu_count)
    
    final_workers = max(1, final_workers)
    
    return {
        "max_workers": final_workers,
        "operation_cost": operation_cost,
        "cpu_count": cpu_count,
        "suggested_workers": suggested_workers
    }


def create_batch_from_configs(
    configs: List[Dict[str, Any]],
    batch_size: Optional[int] = None
) -> List[List[Dict[str, Any]]]:
    """
    Split configurations into batches for processing.
    
    Args:
        configs: List of configuration dictionaries
        batch_size: Size of each batch, auto-calculated if None
    
    Returns:
        List of batch lists
    """
    if not configs:
        return []
    
    # Auto-calculate batch size if not provided
    if batch_size is None:
        cpu_count = os.cpu_count() or 1
        # Aim for 2-4 batches to keep memory usage reasonable
        batch_size = max(1, len(configs) // (cpu_count * 2))
        batch_size = min(batch_size, 50)  # Reasonable upper limit
    
    batches = []
    for i in range(0, len(configs), batch_size):
        batch = configs[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"Split {len(configs)} configs into {len(batches)} batches of "
               f"average size {len(configs) / len(batches):.1f}")
    
    return batches


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize processing results.
    
    Args:
        results: List of result dictionaries
    
    Returns:
        Summary dict with statistics
    """
    if not results:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "errors": []
        }
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    # Collect errors
    errors = []
    for result in failed:
        error_info = {
            "item": result.get("name", result.get("path", "unknown")),
            "error": result.get("error", "Unknown error")
        }
        errors.append(error_info)
    
    success_rate = (len(successful) / len(results)) * 100 if results else 0
    
    return {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": success_rate,
        "errors": errors
    }


def safe_execute(operation: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely execute an operation and return standardized result.
    
    Args:
        operation: Function to execute
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
    
    Returns:
        Dict with success status and result/error
    """
    try:
        result = operation(*args, **kwargs)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Operation {operation.__name__} failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def filter_valid_paths(paths: List[str]) -> List[str]:
    """
    Filter list of paths to only include existing files/directories.
    
    Args:
        paths: List of file/directory paths
    
    Returns:
        List of existing paths
    """
    valid_paths = []
    for path in paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            logger.warning(f"Path does not exist: {path}")
    
    invalid_count = len(paths) - len(valid_paths)
    if invalid_count > 0:
        logger.info(f"Filtered out {invalid_count} invalid paths, "
                   f"{len(valid_paths)} valid paths remaining")
    
    return valid_paths


def get_optimal_batch_size(item_count: int, operation_cost: str = "medium") -> int:
    """
    Calculate optimal batch size for parallel processing.
    
    Args:
        item_count: Number of items to process
        operation_cost: Cost level of operations
    
    Returns:
        Optimal batch size
    """
    cpu_count = os.cpu_count() or 1
    
    if operation_cost == "low":
        # For I/O operations, larger batches are better
        base_size = cpu_count * 4
    elif operation_cost == "medium":
        # Mixed operations
        base_size = cpu_count * 2
    else:  # high cost
        # For CPU-intensive operations, smaller batches
        base_size = cpu_count
    
    # Ensure reasonable bounds
    optimal_size = max(1, min(base_size, item_count // 2, 100))
    
    logger.debug(f"Optimal batch size for {item_count} items "
                f"({operation_cost} cost): {optimal_size}")
    
    return optimal_size


# Configuration constants for different operation types
OPERATION_CONFIGS = {
    "file_copy": {
        "cost": "low",
        "default_workers_factor": 2.0,
        "description": "File copying operations"
    },
    "jar_analysis": {
        "cost": "medium", 
        "default_workers_factor": 1.0,
        "description": "JAR file analysis"
    },
    "jar_validation": {
        "cost": "low",
        "default_workers_factor": 2.0,
        "description": "JAR validation"
    },
    "appimage_validation": {
        "cost": "medium",
        "default_workers_factor": 1.0,
        "description": "AppImage validation"
    },
    "appimage_creation": {
        "cost": "high",
        "default_workers_factor": 0.5,
        "description": "AppImage creation"
    }
}


def get_operation_config(operation_type: str) -> Dict[str, Any]:
    """
    Get configuration for a specific operation type.
    
    Args:
        operation_type: Type of operation
    
    Returns:
        Configuration dict
    """
    return OPERATION_CONFIGS.get(operation_type, {
        "cost": "medium",
        "default_workers_factor": 1.0,
        "description": "Generic operation"
    })


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test ProgressTracker
    tracker = ProgressTracker(10, "Test operation")
    for i in range(10):
        time.sleep(0.1)
        tracker.update(1, f"item_{i}")
    tracker.complete()
    
    # Test OperationTimer
    with OperationTimer("Test timer"):
        time.sleep(0.2)
    
    # Test path filtering
    test_paths = ["/tmp/test1", "/tmp/test2", "/nonexistent/path"]
    valid_paths = filter_valid_paths(test_paths)
    print(f"Valid paths: {valid_paths}")
    
    # Test batch creation
    configs = [{"id": i} for i in range(25)]
    batches = create_batch_from_configs(configs, batch_size=7)
    print(f"Created {len(batches)} batches")