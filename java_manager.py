#!/usr/bin/env python3
"""
Java Manager Module - Core Orchestration

This module provides the main Java management orchestration, coordinating between
all the specialized modules for a unified interface.

Key Responsibilities:
- Orchestrate between UI, Downloader, Validator, and Cache modules
- Provide unified interface matching original PortableJavaManager API
- Manage dependencies and integration between modules
- Handle backward compatibility and migration
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from java_ui import JavaUserInterface
from java_downloader import JavaDownloader
from java_validator import JavaValidator, JavaValidationError, JavaCompatibilityError
from java_cache import JavaCacheManager

logger = logging.getLogger(__name__)


class PortableJavaManager:
    """
    Refactored portable Java management system using modular architecture
    
    This class provides the same interface as the original PortableJavaManager
    but uses the new modular components internally.
    """

    def __init__(self, interactive_mode: bool = True, cache_dir: Optional[str] = None):
        """
        Initialize the portable Java manager with modular components
        
        Args:
            interactive_mode: Whether to use interactive prompts
            cache_dir: Directory for caching downloads
        """
        self.interactive_mode = interactive_mode
        
        # Initialize modular components
        self.cache_manager = JavaCacheManager(Path(cache_dir) if cache_dir else None)
        self.validator = JavaValidator()
        self.downloader = JavaDownloader(self.cache_manager.download_cache)
        self.ui = JavaUserInterface(interactive_mode)
        
        # Get platform information
        self.current_platform = self.validator.detect_platform()
        
        logger.info(f"Initialized PortableJavaManager for {self.current_platform['system']} {self.current_platform['arch']}")

    def detect_system_java(self) -> Optional[Dict[str, Union[str, int, bool]]]:
        """
        Comprehensive system Java detection
        
        Returns:
            Dict with Java information or None if not found
        """
        return self.validator.detect_system_java()

    def analyze_jar_requirements(self, jar_path: str) -> Dict[str, Any]:
        """
        Analyze JAR file for Java version requirements
        
        Args:
            jar_path: Path to JAR file
            
        Returns:
            Dict with Java requirement information
        """
        return self.validator.analyze_jar_requirements(jar_path)

    def get_latest_lts_version(self, force_update: bool = False) -> str:
        """
        Get the latest LTS Java version
        
        Args:
            force_update: Force API check instead of using cached value
            
        Returns:
            Latest LTS version string
        """
        return self.downloader.get_latest_lts_version(force_update)

    def check_java_download_needed(self, system_java: Optional[Dict], jar_requirements: Dict) -> Tuple[bool, str]:
        """
        Determine if Java download is needed
        
        Args:
            system_java: System Java information or None
            jar_requirements: JAR requirements analysis
            
        Returns:
            Tuple of (download_needed, reason)
        """
        return self.validator.check_java_download_needed(system_java, jar_requirements)

    def offer_portable_java(self, download_needed: bool, reason: str, java_version: str) -> bool:
        """
        Offer to download portable Java with user consent
        
        Args:
            download_needed: Whether download is needed
            reason: Reason for download
            java_version: Java version to download
            
        Returns:
            True if user consents to download
        """
        # Get download information
        system_java = self.detect_system_java()
        download_info = self.downloader.get_download_info(
            java_version, 
            has_system_java=system_java is not None
        )
        
        # Add cache directory to download info
        download_info["cache_dir"] = str(self.cache_manager.cache_dir)
        
        return self.ui.offer_portable_java(
            download_needed, reason, java_version, download_info, self.current_platform
        )

    def download_portable_java(self, java_version: str, force: bool = False) -> Optional[str]:
        """
        Download portable Java runtime
        
        Args:
            java_version: Java version to download
            force: Force download even if cached version exists
            
        Returns:
            Path to downloaded Java archive or None if failed
        """
        return self.downloader.download_portable_java(java_version, force)

    def extract_java_runtime(self, java_archive: str, extract_dir: str) -> Optional[str]:
        """
        Extract Java runtime from archive
        
        Args:
            java_archive: Path to Java archive
            extract_dir: Directory to extract to
            
        Returns:
            Path to extracted Java directory or None if failed
        """
        return self.downloader.extract_java_runtime(java_archive, extract_dir)

    def create_portable_java_integration(self, java_dir: str, appimage_dir: str) -> bool:
        """
        Create portable Java integration for AppImage
        
        Args:
            java_dir: Directory containing extracted Java
            appimage_dir: AppImage directory structure
            
        Returns:
            True if successful
        """
        return self.downloader.create_portable_java_integration(java_dir, appimage_dir)

    def clear_cache(self) -> bool:
        """
        Clear Java download cache
        
        Returns:
            True if cache was cleared
        """
        return self.cache_manager.clear_cache()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached Java downloads
        
        Returns:
            Dict with cache information
        """
        return self.cache_manager.get_cache_info()

    # Additional methods for enhanced functionality
    
    def get_cached_java_file(self, java_version: str) -> Optional[Path]:
        """
        Get cached Java file for specific version
        
        Args:
            java_version: Java version to find
            
        Returns:
            Path to cached file or None if not found
        """
        return self.cache_manager.get_cached_java_file(java_version)
    
    def is_java_version_cached(self, java_version: str) -> bool:
        """
        Check if a specific Java version is cached
        
        Args:
            java_version: Java version to check for
            
        Returns:
            True if Java version is cached
        """
        return self.cache_manager.is_java_version_cached(java_version)
    
    def cleanup_old_cache_files(self, max_age_days: int = 30) -> int:
        """
        Clean up old cache files
        
        Args:
            max_age_days: Maximum age in days for files to keep
            
        Returns:
            Number of files cleaned up
        """
        return self.cache_manager.cleanup_old_cache_files(max_age_days)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics
        
        Returns:
            Dictionary with detailed cache statistics
        """
        return self.cache_manager.get_cache_statistics()
    
    def verify_cache_integrity(self) -> Dict[str, Any]:
        """
        Verify cache file integrity
        
        Returns:
            Dictionary with integrity check results
        """
        return self.cache_manager.verify_cache_integrity()
    
    def validate_java_installation(self, java_info: Dict[str, Any]) -> bool:
        """
        Validate a Java installation
        
        Args:
            java_info: Java information dictionary
            
        Returns:
            True if validation passes
        """
        return self.validator.validate_java_installation(java_info)


# Convenience functions for easy integration (maintaining backward compatibility)

def detect_and_manage_java(jar_path: str, interactive: bool = True) -> Tuple[Optional[str], bool]:
    """
    Detect system Java and offer portable Java if needed
    
    Args:
        jar_path: Path to JAR file
        interactive: Whether to use interactive prompts
        
    Returns:
        Tuple of (java_version_to_use, download_consented)
    """
    manager = PortableJavaManager(interactive_mode=interactive)

    # Detect system Java
    system_java = manager.detect_system_java()

    # Analyze JAR requirements
    jar_requirements = manager.analyze_jar_requirements(jar_path)

    # Determine if download is needed
    download_needed, reason = manager.check_java_download_needed(system_java, jar_requirements)

    if download_needed:
        # Get latest LTS version
        java_version = manager.get_latest_lts_version()

        # Offer portable Java
        if interactive:
            consent = manager.offer_portable_java(download_needed, reason, java_version)
        else:
            consent = True

        if consent:
            return java_version, True

    # Use system Java or fail
    if system_java:
        return f"{system_java['major_version']}", False
    else:
        return None, False


def get_java_detection_summary() -> Dict[str, Any]:
    """
    Get a summary of Java detection results
    
    Returns:
        Dict with detection summary
    """
    manager = PortableJavaManager()

    summary = {
        "system_java": manager.detect_system_java(),
        "cache_info": manager.get_cache_info(),
        "latest_lts": manager.get_latest_lts_version(),
        "platform": manager.current_platform
    }

    return summary


# CLI interface (maintaining backward compatibility)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Portable Java Detection and Management for jar2appimage (Refactored)")
    parser.add_argument("--jar", help="JAR file to analyze")
    parser.add_argument("--detect", action="store_true", help="Detect system Java")
    parser.add_argument("--download", help="Download specific Java version")
    parser.add_argument("--cache-info", action="store_true", help="Show cache information")
    parser.add_argument("--clear-cache", action="store_true", help="Clear download cache")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--version", help="Java version for operations")

    args = parser.parse_args()

    manager = PortableJavaManager(interactive_mode=not args.non_interactive)

    if args.detect:
        java_info = manager.detect_system_java()
        manager.ui.show_java_detection_result(java_info)

    elif args.jar:
        system_java = manager.detect_system_java()
        jar_requirements = manager.analyze_jar_requirements(args.jar)
        download_needed, reason = manager.check_java_download_needed(system_java, jar_requirements)

        manager.ui.show_jar_analysis_results(args.jar, jar_requirements)
        print(f"   System Java: {'Available' if system_java else 'Not found'}")
        print(f"   Download Needed: {download_needed}")
        if download_needed:
            print(f"   Reason: {reason}")

    elif args.download:
        version = args.version or manager.get_latest_lts_version()
        downloaded = manager.download_portable_java(version)
        manager.ui.show_download_progress(version, downloaded or "")

    elif args.cache_info:
        cache_info = manager.get_cache_info()
        manager.ui.show_cache_info(cache_info)

    elif args.clear_cache:
        if manager.clear_cache():
            manager.ui.show_operation_status("Cache cleared", True)
        else:
            manager.ui.show_operation_status("Cache clearing failed", False)

    else:
        summary = get_java_detection_summary()
        manager.ui.show_detection_summary(summary)