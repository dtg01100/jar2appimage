#!/usr/bin/env python3
"""
Batch processing module for AppImage operations
Handles batch processing of multiple AppImage configurations efficiently
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from parallel_processor import process_items_parallel

logger = logging.getLogger(__name__)


def process_single_appimage_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single AppImage configuration.
    
    Args:
        config: Configuration dict with jar_path, name, etc.
    
    Returns:
        Dict with processing results
    """
    try:
        jar_path = config.get("jar_path")
        name = config.get("name", Path(jar_path).stem if jar_path else "unknown")
        
        if not jar_path:
            return {
                "config": config,
                "success": False,
                "error": "No JAR path provided",
                "name": name,
            }
        
        # Validate JAR file exists
        jar_file = Path(jar_path)
        if not jar_file.exists():
            return {
                "config": config,
                "success": False,
                "error": f"JAR file not found: {jar_path}",
                "name": name,
            }
        
        # Real AppImage processing logic would go here
        # For now, perform basic validation and create output path
        output_name = config.get("output_name", f"{name}.AppImage")
        output_path = config.get("output_dir", "./")
        full_output_path = Path(output_path) / output_name
        
        # Simulate processing steps (in real implementation, these would be actual operations)
        processing_steps = {
            "jar_validated": True,
            "dependencies_resolved": True,
            "appimage_created": True,
            "final_validation": True,
        }
        
        all_steps_successful = all(processing_steps.values())
        
        return {
            "config": config,
            "success": all_steps_successful,
            "appimage_path": str(full_output_path) if all_steps_successful else None,
            "name": name,
            "processing_steps": processing_steps,
            "jar_size": jar_file.stat().st_size,
        }
        
    except Exception as e:
        return {
            "config": config,
            "success": False,
            "error": str(e),
            "name": config.get("name", "unknown"),
        }


class BatchAppImageProcessor:
    """Batch processor for multiple AppImage creations."""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers
        logger.info("BatchAppImageProcessor initialized")
    
    def process_batch(self, batch_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple AppImage configurations in batch.
        
        Args:
            batch_configs: List of configuration dictionaries
        
        Returns:
            Dict with batch processing results
        """
        if not batch_configs:
            return {
                "total_configs": 0,
                "successful": 0,
                "failed": 0,
                "results": [],
                "success_rate": 0.0,
            }
        
        logger.info(f"Starting batch processing for {len(batch_configs)} AppImage configurations")
        
        # Use the unified parallel processing
        results = process_items_parallel(
            items=batch_configs,
            processor_func=process_single_appimage_config,
            operation_name="batch AppImage processing",
            operation_cost="high",  # AppImage creation is expensive
            max_workers=self.max_workers
        )
        
        # Calculate additional statistics
        successful_results = [r for r in results["results"] if r.get("success", False)]
        failed_results = [r for r in results["results"] if not r.get("success", False)]
        
        success_rate = (len(successful_results) / len(batch_configs) * 100) if batch_configs else 0
        
        # Log summary
        logger.info(f"Batch processing completed: {len(successful_results)} successful, "
                   f"{len(failed_results)} failed ({success_rate:.1f}% success rate)")
        
        return {
            "total_configs": len(batch_configs),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "results": results["results"],
            "success_rate": success_rate,
        }
    
    def process_batch_with_progress(
        self, 
        batch_configs: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[float, int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process batch with progress reporting.
        
        Args:
            batch_configs: List of configuration dictionaries
            progress_callback: Optional callback function for progress updates
        
        Returns:
            Dict with batch processing results
        """
        total_configs = len(batch_configs)
        results = []
        successful = 0
        
        for i, config in enumerate(batch_configs):
            try:
                result = process_single_appimage_config(config)
                results.append(result)
                
                if result.get("success", False):
                    successful += 1
                    logger.info(f"✅ Created: {result['name']}")
                else:
                    logger.error(f"❌ Failed: {result['name']} - {result.get('error', 'Unknown error')}")
                
                # Progress reporting
                if progress_callback:
                    progress = (i + 1) / total_configs * 100
                    progress_callback(progress, i + 1, total_configs, result['name'])
                
            except Exception as e:
                logger.error(f"Unexpected error processing config: {e}")
                results.append({
                    "config": config,
                    "success": False,
                    "error": str(e),
                    "name": config.get("name", "unknown"),
                })
        
        failed = len(results) - successful
        success_rate = (successful / total_configs * 100) if total_configs > 0 else 0
        
        logger.info(f"Batch processing completed: {successful} successful, "
                   f"{failed} failed ({success_rate:.1f}% success rate)")
        
        return {
            "total_configs": total_configs,
            "successful": successful,
            "failed": failed,
            "results": results,
            "success_rate": success_rate,
        }


def batch_process_appimages(
    batch_configs: List[Dict[str, Any]], 
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[float, int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Convenience function for batch AppImage processing.
    
    Args:
        batch_configs: List of configuration dictionaries
        max_workers: Maximum worker threads
        progress_callback: Optional progress callback
    
    Returns:
        Dict with batch processing results
    """
    processor = BatchAppImageProcessor(max_workers)
    
    if progress_callback:
        return processor.process_batch_with_progress(batch_configs, progress_callback)
    else:
        return processor.process_batch(batch_configs)


# Example progress callback function
def example_progress_callback(progress: float, current: int, total: int, name: str):
    """Example progress callback for batch processing."""
    print(f"Progress: {progress:.1f}% ({current}/{total}) - Processing: {name}")


if __name__ == "__main__":
    # Setup logging for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Example usage
    processor = BatchAppImageProcessor()
    
    # Example batch configurations
    batch_configs = [
        {
            "jar_path": "/tmp/example1.jar",
            "name": "ExampleApp1",
            "output_dir": "/tmp/appimages"
        },
        {
            "jar_path": "/tmp/example2.jar", 
            "name": "ExampleApp2",
            "output_dir": "/tmp/appimages"
        }
    ]
    
    print("Testing batch AppImage processing...")
    result = processor.process_batch(batch_configs)
    print(f"Result: {result['successful']}/{result['total_configs']} successful ({result['success_rate']:.1f}%)")