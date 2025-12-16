#!/usr/bin/env python3
"""
Simplified parallel processing module
Provides efficient parallel operations without over-engineering
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def should_use_parallelism(item_count: int, operation_cost: str = "low") -> bool:
    """
    Determine if parallelism is beneficial based on item count and operation cost.

    Args:
        item_count: Number of items to process
        operation_cost: "low", "medium", or "high" - estimated CPU/IO cost per operation

    Returns:
        True if parallelism should be used, False otherwise
    """
    thresholds = {
        "low": 10,     # File copying, simple validation
        "medium": 5,   # JAR analysis, dependency checking
        "high": 2      # Java downloads, AppImage creation
    }

    return item_count >= thresholds.get(operation_cost, 5)


def process_items_parallel(
    items: List[Any],
    processor_func: Callable,
    operation_name: str,
    operation_cost: str = "low",
    max_workers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Unified parallel processing function that eliminates repetitive patterns.

    Args:
        items: List of items to process
        processor_func: Function that processes a single item
        operation_name: Name for logging and reporting
        operation_cost: Estimated cost per operation ("low", "medium", "high")
        max_workers: Maximum worker threads

    Returns:
        Dict with results and statistics
    """
    if not items:
        return {"total": 0, "successful": 0, "failed": 0, "results": []}

    # Determine if parallelism is beneficial
    use_parallel = should_use_parallelism(len(items), operation_cost)

    if not use_parallel:
        # Process synchronously for small/simple operations
        logger.info(f"Processing {len(items)} {operation_name} items synchronously")
        return _process_items_sync(items, processor_func, operation_name)

    # Process in parallel for larger operations
    max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
    logger.info(f"Processing {len(items)} {operation_name} items in parallel with {max_workers} workers")

    results = []
    successful = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(processor_func, item): item for item in items}

        # Collect results as they complete
        for future in as_completed(future_to_item):
            try:
                result = future.result()
                results.append(result)
                if result.get("success", False):
                    successful += 1
            except Exception as e:
                logger.error(f"Task failed unexpectedly: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "item": future_to_item[future]
                })

    failed = len(results) - successful
    logger.info(f"{operation_name} completed: {successful} successful, {failed} failed")

    return {
        "total": len(items),
        "successful": successful,
        "failed": failed,
        "results": results
    }


def _process_items_sync(
    items: List[Any],
    processor_func: Callable,
    operation_name: str
) -> Dict[str, Any]:
    """Process items synchronously."""
    results = []
    successful = 0

    for i, item in enumerate(items, 1):
        try:
            result = processor_func(item)
            results.append(result)
            if result.get("success", False):
                successful += 1
        except Exception as e:
            logger.error(f"Failed to process {operation_name} item {i}: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "item": item
            })

    failed = len(results) - successful
    return {
        "total": len(items),
        "successful": successful,
        "failed": failed,
        "results": results
    }


# Standalone processor functions (extracted from nested functions)

def copy_file_operation(src_dest_tuple: tuple) -> Dict[str, Any]:
    """Process a single file copy operation."""
    src, dest = src_dest_tuple
    try:
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(src, dest)

        return {
            "success": True,
            "src": src,
            "dest": dest,
            "size": dest_path.stat().st_size,
        }
    except Exception as e:
        return {
            "success": False,
            "src": src,
            "dest": dest,
            "error": str(e),
        }


def analyze_jar_operation(jar_path: str) -> Dict[str, Any]:
    """Analyze a single JAR file."""
    try:
        jar_file = Path(jar_path)
        if not jar_file.exists():
            return {"jar_path": jar_path, "success": False, "error": "File not found"}

        # Real JAR analysis - extract basic information
        import zipfile
        analysis = {
            "size": jar_file.stat().st_size,
            "dependencies_found": 0,
            "main_class": None,
            "manifest_info": {},
        }

        with zipfile.ZipFile(jar_path, "r") as zf:
            # Check for manifest
            if "META-INF/MANIFEST.MF" in zf.namelist():
                try:
                    manifest_content = zf.read("META-INF/MANIFEST.MF").decode("utf-8", errors="ignore")
                    analysis["manifest_info"]["has_manifest"] = True

                    for line in manifest_content.split("\n"):
                        if line.startswith("Main-Class:"):
                            analysis["main_class"] = line.split(":", 1)[1].strip()
                            break
                except Exception:
                    analysis["manifest_info"]["has_manifest"] = False
            else:
                analysis["manifest_info"]["has_manifest"] = False

            # Count entries as a basic dependency indicator
            analysis["dependencies_found"] = len([name for name in zf.namelist() if name.endswith('.jar')])

        return {"jar_path": jar_path, "success": True, "analysis": analysis}

    except Exception as e:
        return {"jar_path": jar_path, "success": False, "error": str(e)}


def validate_jar_operation(jar_path: str) -> Dict[str, Any]:
    """Validate a single JAR file."""
    try:
        jar_file = Path(jar_path)

        # Basic validation checks
        validation = {
            "exists": jar_file.exists(),
            "readable": os.access(jar_path, os.R_OK) if jar_file.exists() else False,
            "is_jar": jar_path.lower().endswith(".jar"),
            "has_size": jar_file.stat().st_size > 0 if jar_file.exists() else False,
        }

        # Try to validate JAR structure
        if validation["exists"] and validation["is_jar"]:
            try:
                import zipfile
                with zipfile.ZipFile(jar_path, "r") as zf:
                    # Test that we can read the JAR
                    test_read = zf.namelist()
                    validation["zip_structure_valid"] = len(test_read) > 0
            except Exception:
                validation["zip_structure_valid"] = False
        else:
            validation["zip_structure_valid"] = False

        validation["overall_valid"] = all([
            validation["exists"],
            validation["readable"],
            validation["is_jar"],
            validation["has_size"],
            validation.get("zip_structure_valid", False)
        ])

        return {"jar_path": jar_path, "success": True, "validation": validation}

    except Exception as e:
        return {"jar_path": jar_path, "success": False, "error": str(e)}


def validate_appimage_operation(appimage_path: str) -> Dict[str, Any]:
    """Validate a single AppImage file."""
    try:
        appimage_file = Path(appimage_path)

        if not appimage_file.exists():
            return {"appimage_path": appimage_path, "success": False, "error": "File not found"}

        # Basic file validation
        file_validation = {
            "exists": True,
            "is_executable": os.access(appimage_path, os.X_OK),
            "has_executable_extension": appimage_path.lower().endswith(('.appimage', '.AppImage')),
            "size": appimage_file.stat().st_size,
        }

        # Basic AppImage structure validation
        try:
            with open(appimage_path, "rb") as f:
                header = f.read(8)
                file_validation["elf_header_valid"] = header.startswith(b'\x7fELF')
        except Exception:
            file_validation["elf_header_valid"] = False

        # Overall validation status
        file_validation["overall_valid"] = all([
            file_validation["exists"],
            file_validation["is_executable"],
            file_validation["has_executable_extension"],
            file_validation["elf_header_valid"]
        ])

        status = "passed" if file_validation["overall_valid"] else "failed"

        return {
            "appimage_path": appimage_path,
            "success": True,
            "file_validation": file_validation,
            "overall_status": status,
        }

    except Exception as e:
        return {"appimage_path": appimage_path, "success": False, "error": str(e)}


# Main processor class with unified interface
class ParallelProcessor:
    """Simplified parallel processor with unified interface."""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers
        logger.info("ParallelProcessor initialized")

    def parallel_file_copy(self, file_operations: List[tuple]) -> Dict[str, Any]:
        """Copy multiple files in parallel using unified processing."""
        return process_items_parallel(
            items=file_operations,
            processor_func=copy_file_operation,
            operation_name="file copy",
            operation_cost="low",
            max_workers=self.max_workers
        )

    def parallel_dependency_analysis(self, jar_files: List[str]) -> Dict[str, Any]:
        """Analyze multiple JAR files in parallel."""
        return process_items_parallel(
            items=jar_files,
            processor_func=analyze_jar_operation,
            operation_name="JAR analysis",
            operation_cost="medium",
            max_workers=self.max_workers
        )

    def parallel_jar_validation(self, jar_files: List[str]) -> Dict[str, Any]:
        """Validate multiple JAR files in parallel."""
        return process_items_parallel(
            items=jar_files,
            processor_func=validate_jar_operation,
            operation_name="JAR validation",
            operation_cost="low",
            max_workers=self.max_workers
        )

    def parallel_appimage_validation(self, appimage_paths: List[str]) -> Dict[str, Any]:
        """Validate multiple AppImages in parallel."""
        return process_items_parallel(
            items=appimage_paths,
            processor_func=validate_appimage_operation,
            operation_name="AppImage validation",
            operation_cost="medium",
            max_workers=self.max_workers
        )

    def execute_parallel_tasks(
        self,
        task_functions: List[Callable],
        task_args: List[tuple]
    ) -> List[Any]:
        """Execute multiple different tasks in parallel."""
        if len(task_functions) != len(task_args):
            raise ValueError("task_functions and task_args must have same length")

        def execute_task_wrapper(args):
            func, arg_tuple = args
            try:
                return {
                    "success": True,
                    "result": func(*arg_tuple),
                    "task_name": func.__name__,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "task_name": func.__name__,
                }

        combined_tasks = list(zip(task_functions, task_args))
        results = process_items_parallel(
            items=combined_tasks,
            processor_func=execute_task_wrapper,
            operation_name="task execution",
            operation_cost="high",
            max_workers=self.max_workers
        )

        return results["results"]


# Convenience functions for common operations
def parallel_file_operations(operations: List[tuple], max_workers: Optional[int] = None) -> Dict[str, Any]:
    """Convenient function for parallel file operations."""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_file_copy(operations)


def parallel_jar_analysis(jar_files: List[str], max_workers: Optional[int] = None) -> Dict[str, Any]:
    """Convenient function for parallel JAR analysis."""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_dependency_analysis(jar_files)


def parallel_appimage_validation(appimage_paths: List[str], max_workers: Optional[int] = None) -> Dict[str, Any]:
    """Convenient function for parallel AppImage validation."""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_appimage_validation(appimage_paths)


if __name__ == "__main__":
    # Setup logging for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Example usage
    processor = ParallelProcessor()

    # Test file operations
    file_ops = [
        ("/tmp/test1.txt", "/tmp/copy1.txt"),
        ("/tmp/test2.txt", "/tmp/copy2.txt"),
    ]

    print("Testing parallel file operations...")
    result = processor.parallel_file_copy(file_ops)
    print(f"Result: {result['successful']}/{result['total']} successful")
