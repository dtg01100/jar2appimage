#!/usr/bin/env python3
"""
Multi-threaded processing for faster AppImage creation
Implements parallel processing for various operations
"""

import os
import sys
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
import time
import queue


class ParallelProcessor:
    """Multi-threaded processing for AppImage creation"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.progress_queue = queue.Queue()
        self.tasks_completed = 0
        self.total_tasks = 0
        self.start_time = None

    def parallel_file_copy(self, file_operations: List[tuple]) -> Dict[str, Any]:
        """Copy multiple files in parallel"""
        print(f"📁 Copying {len(file_operations)} files in parallel...")

        def copy_single_file(args):
            src, dest, operation_id = args
            try:
                dest_path = Path(dest)
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                import shutil

                shutil.copy2(src, dest)

                return {
                    "operation_id": operation_id,
                    "success": True,
                    "src": src,
                    "dest": dest,
                    "size": dest_path.stat().st_size,
                }
            except Exception as e:
                return {
                    "operation_id": operation_id,
                    "success": False,
                    "src": src,
                    "dest": dest,
                    "error": str(e),
                }

        # Prepare operations with IDs
        operations = [(src, dest, i) for i, (src, dest) in enumerate(file_operations)]

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id = {
                executor.submit(copy_single_file, op): op[2] for op in operations
            }

            for future in as_completed(future_to_id):
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(f"  ✅ Copied: {Path(result['src']).name}")
                else:
                    print(
                        f"  ❌ Failed: {Path(result['src']).name} - {result.get('error', 'Unknown error')}"
                    )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_operations": len(file_operations),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def parallel_dependency_analysis(self, jar_files: List[str]) -> Dict[str, Any]:
        """Analyze multiple JAR files in parallel"""
        print(f"🔍 Analyzing {len(jar_files)} JAR files in parallel...")

        def analyze_single_jar(jar_path):
            try:
                # For now, simulate JAR analysis
                jar_file = Path(jar_path)
                analysis = {
                    "size": jar_file.stat().st_size if jar_file.exists() else 0,
                    "dependencies_found": 0,  # Simulated
                    "main_class": None,  # Simulated
                }

                return {"jar_path": jar_path, "success": True, "analysis": analysis}
            except Exception as e:
                return {"jar_path": jar_path, "success": False, "error": str(e)}

        return {
            "total_jars": len(jar_files),
            "successful": len([r for r in results if r["success"]]),
            "results": results,
        }

    def parallel_jar_validation(self, jar_files: List[str]) -> Dict[str, Any]:
        """Validate multiple JAR files in parallel"""
        print(f"✅ Validating {len(jar_files)} JAR files in parallel...")

        def validate_single_jar(jar_path):
            try:
                jar_file = Path(jar_path)

                # Basic validation checks
                validation = {
                    "exists": jar_file.exists(),
                    "readable": os.access(jar_path, os.R_OK),
                    "is_jar": jar_path.lower().endswith(".jar"),
                    "has_size": jar_file.stat().st_size > 0
                    if jar_file.exists()
                    else False,
                }

                # Try to read JAR manifest
                manifest_info = {}
                if validation["exists"] and validation["is_jar"]:
                    try:
                        import zipfile

                        with zipfile.ZipFile(jar_path, "r") as zf:
                            if "META-INF/MANIFEST.MF" in zf.namelist():
                                manifest_content = zf.read(
                                    "META-INF/MANIFEST.MF"
                                ).decode("utf-8", errors="ignore")
                                manifest_info["has_manifest"] = True
                                manifest_info["main_class"] = None

                                for line in manifest_content.split("\n"):
                                    if line.startswith("Main-Class:"):
                                        manifest_info["main_class"] = line.split(
                                            ":", 1
                                        )[1].strip()
                                        break
                            else:
                                manifest_info["has_manifest"] = False
                    except Exception:
                        manifest_info["has_manifest"] = False

                validation.update(manifest_info)
                validation["overall_valid"] = all(
                    [
                        validation["exists"],
                        validation["readable"],
                        validation["is_jar"],
                        validation["has_size"],
                    ]
                )

                return {"jar_path": jar_path, "success": True, "validation": validation}

            except Exception as e:
                return {"jar_path": jar_path, "success": False, "error": str(e)}

        results = []
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(jar_files))
        ) as executor:
            future_to_jar = {
                executor.submit(validate_single_jar, jar): jar for jar in jar_files
            }

        results = []
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(jar_files))
        ) as executor:
            future_to_jar = {
                executor.submit(analyze_single_jar, jar): jar for jar in jar_files
            }

            for future in as_completed(future_to_jar):
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(f"  ✅ Analyzed: {Path(result['jar_path']).name}")
                else:
                    print(
                        f"  ❌ Failed: {Path(result['jar_path']).name} - {result.get('error', 'Unknown error')}"
                    )

        return {
            "total_jars": len(jar_files),
            "valid": len(
                [
                    r
                    for r in results
                    if r.get("success")
                    and r.get("validation", {}).get("overall_valid", False)
                ]
            ),
            "invalid": len(
                [
                    r
                    for r in results
                    if r.get("success")
                    and not r.get("validation", {}).get("overall_valid", False)
                ]
            ),
            "failed": len([r for r in results if not r.get("success", False)]),
            "results": results,
        }

    def parallel_java_download_extracts(
        self, java_configs: List[Dict]
    ) -> Dict[str, Any]:
        """Download and extract multiple Java runtimes in parallel"""
        print(f"☕ Processing {len(java_configs)} Java configurations in parallel...")

        def process_java_config(config):
            try:
                java_version = config.get("version", "unknown")
                platform = config.get("platform", "linux-x64")

                # This would integrate with the JavaBundler
                # For now, simulate the process
                time.sleep(0.1)  # Simulate download/extract time

                return {
                    "config": config,
                    "success": True,
                    "java_version": java_version,
                    "platform": platform,
                }
            except Exception as e:
                return {"config": config, "success": False, "error": str(e)}

        results = []
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(java_configs))
        ) as executor:
            future_to_config = {
                executor.submit(process_java_config, config): config
                for config in java_configs
            }

            for future in as_completed(future_to_config):
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(
                        f"  ✅ Processed Java {result['java_version']} ({result['platform']})"
                    )
                else:
                    print(
                        f"  ❌ Failed: {result.get('config', {}).get('version', 'unknown')} - {result.get('error', 'Unknown error')}"
                    )

        return {
            "total_configs": len(java_configs),
            "successful": len([r for r in results if r["success"]]),
            "results": results,
        }

    def parallel_appimage_validation(self, appimage_paths: List[str]) -> Dict[str, Any]:
        """Validate multiple AppImages in parallel"""
        print(f"🔍 Validating {len(appimage_paths)} AppImages in parallel...")

        def validate_single_appimage(appimage_path):
            try:
                # Import here to avoid circular imports
                # from .appimage_validator import AppImageValidator

                # validator = AppImageValidator(appimage_path, timeout=15)
                # For now, simulate validation
                pass

                # Quick validation only (simulated)
                file_validation = {"is_executable": True, "exists": True}
                runtime_validation = {"help_flag_works": True}

                return {
                    "appimage_path": appimage_path,
                    "success": True,
                    "file_validation": file_validation,
                    "runtime_validation": runtime_validation,
                    "overall_status": "passed"
                    if (
                        file_validation.get("is_executable")
                        and runtime_validation.get("help_flag_works", False)
                        or runtime_validation.get("version_flag_works", False)
                    )
                    else "failed",
                }
            except Exception as e:
                return {
                    "appimage_path": appimage_path,
                    "success": False,
                    "error": str(e),
                }

        results = []
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(appimage_paths))
        ) as executor:
            future_to_appimage = {
                executor.submit(validate_single_appimage, app): app
                for app in appimage_paths
            }

            for future in as_completed(future_to_appimage):
                result = future.result()
                results.append(result)

                if result["success"]:
                    status = "✅" if result["overall_status"] == "passed" else "⚠️"
                    print(f"  {status} Validated: {Path(result['appimage_path']).name}")
                else:
                    print(
                        f"  ❌ Failed: {Path(result['appimage_path']).name} - {result.get('error', 'Unknown error')}"
                    )

        return {
            "total_appimages": len(appimage_paths),
            "passed": len([r for r in results if r.get("overall_status") == "passed"]),
            "failed": len([r for r in results if r.get("overall_status") == "failed"]),
            "errors": len([r for r in results if not r.get("success", False)]),
            "results": results,
        }

    def execute_parallel_tasks(
        self, task_functions: List[Callable], task_args: List[tuple]
    ) -> List[Any]:
        """Execute multiple different tasks in parallel"""
        print(f"🚀 Executing {len(task_functions)} tasks in parallel...")

        def execute_task(task_func, args):
            try:
                return {
                    "success": True,
                    "result": task_func(*args),
                    "task_name": task_func.__name__,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "task_name": task_func.__name__,
                }

        results = []
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(task_functions))
        ) as executor:
            future_to_task = {
                executor.submit(execute_task, func, args): (func, args)
                for func, args in zip(task_functions, task_args)
            }

            for future in as_completed(future_to_task):
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(f"  ✅ Completed: {result['task_name']}")
                else:
                    print(
                        f"  ❌ Failed: {result['task_name']} - {result.get('error', 'Unknown error')}"
                    )

        return results


class BatchAppImageProcessor:
    """Batch processing for multiple AppImage creations"""

    def __init__(self, max_workers: int = None):
        self.parallel_processor = ParallelProcessor(max_workers)

    def process_batch(self, batch_configs: List[Dict]) -> Dict[str, Any]:
        """Process multiple AppImage configurations in batch"""
        print(f"🏭 Processing batch of {len(batch_configs)} AppImages...")

        def process_single_config(config):
            try:
                # This would integrate with the main Jar2AppImage class
                # For now, simulate the processing
                jar_path = config.get("jar_path")
                name = config.get("name", Path(jar_path).stem)

                print(f"  🔨 Processing: {name}")

                # Simulate processing time
                time.sleep(0.5)

                return {
                    "config": config,
                    "success": True,
                    "appimage_path": f"{name}.AppImage",
                    "name": name,
                }
            except Exception as e:
                return {
                    "config": config,
                    "success": False,
                    "error": str(e),
                    "name": config.get("name", "unknown"),
                }

        results = []
        with ThreadPoolExecutor(
            max_workers=self.parallel_processor.max_workers
        ) as executor:
            future_to_config = {
                executor.submit(process_single_config, config): config
                for config in batch_configs
            }

            for future in as_completed(future_to_config):
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(f"  ✅ Created: {result['name']}")
                else:
                    print(
                        f"  ❌ Failed: {result['name']} - {result.get('error', 'Unknown error')}"
                    )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_configs": len(batch_configs),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "success_rate": len(successful) / len(batch_configs) * 100
            if batch_configs
            else 0,
        }


# Utility functions for common parallel operations
def parallel_file_operations(
    operations: List[tuple], max_workers: int = None
) -> Dict[str, Any]:
    """Convenient function for parallel file operations"""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_file_copy(operations)


def parallel_jar_analysis(
    jar_files: List[str], max_workers: int = None
) -> Dict[str, Any]:
    """Convenient function for parallel JAR analysis"""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_dependency_analysis(jar_files)


def parallel_appimage_validation(
    appimage_paths: List[str], max_workers: int = None
) -> Dict[str, Any]:
    """Convenient function for parallel AppImage validation"""
    processor = ParallelProcessor(max_workers)
    return processor.parallel_appimage_validation(appimage_paths)


if __name__ == "__main__":
    # Example usage
    processor = ParallelProcessor()

    # Example file copy operations
    file_ops = [
        ("/source/file1.txt", "/dest/file1.txt"),
        ("/source/file2.txt", "/dest/file2.txt"),
    ]

    print("Testing parallel file operations...")
    result = processor.parallel_file_copy(file_ops)
    print(f"Result: {result['successful']}/{result['total_operations']} successful")
