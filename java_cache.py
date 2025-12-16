#!/usr/bin/env python3
"""
Java Cache Module

This module handles caching and storage management for Java downloads.
Manages cache directories, file operations, and storage cleanup.

Key Responsibilities:
- Download cache management
- File storage and cleanup operations
- Cache information and statistics
- Cache validation and maintenance
"""

import logging
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JavaCacheManager:
    """
    Manages Java download caching and storage operations
    """

    # Minimum file size for valid Java archives (50MB)
    MIN_CACHE_FILE_SIZE = 50 * 1024 * 1024

    # Cache subdirectories
    CACHE_SUBDIRS = ["downloads", "extracted", "temp"]

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the cache manager

        Args:
            cache_dir: Directory for caching Java downloads.
                      If None, uses default ~/.jar2appimage/java_cache
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".jar2appimage" / "java_cache"

        self.download_cache = self.cache_dir / "downloads"
        self.extracted_cache = self.cache_dir / "extracted"
        self.temp_cache = self.cache_dir / "temp"

        # Setup cache directories
        self._setup_cache_directories()

        logger.info(f"Initialized JavaCacheManager at: {self.cache_dir}")

    def _setup_cache_directories(self) -> None:
        """Setup cache directory structure"""
        directories = [self.cache_dir, self.download_cache, self.extracted_cache, self.temp_cache]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Cache directories setup: {list(d.name for d in directories)}")

    def clear_cache(self) -> bool:
        """
        Clear all cached Java downloads

        Returns:
            True if cache was successfully cleared
        """
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self._setup_cache_directories()
                logger.info("✅ Java download cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

        return False

    def clear_download_cache(self) -> bool:
        """
        Clear only the download cache

        Returns:
            True if download cache was cleared
        """
        try:
            if self.download_cache.exists():
                shutil.rmtree(self.download_cache)
                self.download_cache.mkdir(parents=True, exist_ok=True)
                logger.info("✅ Download cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear download cache: {e}")

        return False

    def clear_extracted_cache(self) -> bool:
        """
        Clear only the extracted cache

        Returns:
            True if extracted cache was cleared
        """
        try:
            if self.extracted_cache.exists():
                shutil.rmtree(self.extracted_cache)
                self.extracted_cache.mkdir(parents=True, exist_ok=True)
                logger.info("✅ Extracted cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear extracted cache: {e}")

        return False

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about cached Java downloads

        Returns:
            Dictionary with cache information
        """
        cache_info = {
            "cache_dir": str(self.cache_dir),
            "download_cache_dir": str(self.download_cache),
            "extracted_cache_dir": str(self.extracted_cache),
            "total_files": 0,
            "total_size_mb": 0,
            "java_versions": [],
            "available": self.cache_dir.exists(),
            "download_files": 0,
            "download_size_mb": 0,
            "extracted_files": 0,
            "extracted_size_mb": 0
        }

        if self.cache_dir.exists():
            try:
                # Get download cache info
                download_info = self._get_directory_info(self.download_cache)
                cache_info.update({
                    "download_files": download_info["file_count"],
                    "download_size_mb": download_info["size_mb"],
                    "java_versions": download_info["java_versions"]
                })

                # Get extracted cache info
                extracted_info = self._get_directory_info(self.extracted_cache)
                cache_info.update({
                    "extracted_files": extracted_info["file_count"],
                    "extracted_size_mb": extracted_info["size_mb"]
                })

                # Calculate totals
                cache_info["total_files"] = cache_info["download_files"] + cache_info["extracted_files"]
                cache_info["total_size_mb"] = cache_info["download_size_mb"] + cache_info["extracted_size_mb"]

            except Exception as e:
                logger.warning(f"Could not read cache info: {e}")

        return cache_info

    def _get_directory_info(self, directory: Path) -> Dict[str, Any]:
        """
        Get information about a specific cache directory

        Args:
            directory: Path to cache directory

        Returns:
            Dictionary with directory information
        """
        info = {
            "file_count": 0,
            "size_mb": 0,
            "java_versions": []
        }

        if not directory.exists():
            return info

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    info["file_count"] += 1
                    info["size_mb"] += file_path.stat().st_size // (1024 * 1024)

                    # Extract Java version from filename
                    filename = file_path.name
                    version_match = re.search(r'jdk?(\d+)', filename)
                    if version_match:
                        version = version_match.group(1)
                        if version not in info["java_versions"]:
                            info["java_versions"].append(version)

        except Exception as e:
            logger.warning(f"Could not read directory info for {directory}: {e}")

        return info

    def get_cached_java_versions(self) -> List[str]:
        """
        Get list of cached Java versions

        Returns:
            List of cached Java version strings
        """
        cache_info = self.get_cache_info()
        return cache_info["java_versions"]

    def is_java_version_cached(self, java_version: str) -> bool:
        """
        Check if a specific Java version is cached

        Args:
            java_version: Java version to check for

        Returns:
            True if Java version is cached
        """
        cached_versions = self.get_cached_java_versions()
        return java_version in cached_versions

    def get_cached_java_file(self, java_version: str) -> Optional[Path]:
        """
        Get the cached Java file for a specific version

        Args:
            java_version: Java version to find

        Returns:
            Path to cached file or None if not found
        """
        if not self.download_cache.exists():
            return None

        cache_pattern = f"*{java_version}*.tar.gz"
        for cached_file in self.download_cache.glob(cache_pattern):
            if self._is_valid_cache_file(cached_file):
                return cached_file

        return None

    def _is_valid_cache_file(self, file_path: Path) -> bool:
        """
        Check if a cached file is valid

        Args:
            file_path: Path to cached file

        Returns:
            True if file is valid
        """
        try:
            return (
                file_path.exists() and
                file_path.is_file() and
                file_path.stat().st_size >= self.MIN_CACHE_FILE_SIZE
            )
        except Exception:
            return False

    def cache_file(self, source_path: str, java_version: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        Cache a downloaded file

        Args:
            source_path: Source file path
            java_version: Java version
            filename: Optional custom filename

        Returns:
            Path to cached file or None if caching failed
        """
        try:
            source_file = Path(source_path)
            if not source_file.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return None

            if not self._is_valid_cache_file(source_file):
                logger.warning(f"Source file is not valid for caching: {source_path}")
                return None

            # Generate cache filename
            if filename:
                cache_filename = filename
            else:
                cache_filename = f"java-{java_version}-{source_file.name}"

            cache_path = self.download_cache / cache_filename

            # Copy file to cache
            if not cache_path.exists():
                shutil.copy2(source_file, cache_path)
                logger.info(f"📦 Cached Java {java_version}: {cache_path}")
                return cache_path
            else:
                logger.debug(f"File already cached: {cache_path}")
                return cache_path

        except Exception as e:
            logger.error(f"Failed to cache file {source_path}: {e}")
            return None

    def cleanup_old_cache_files(self, max_age_days: int = 30) -> int:
        """
        Clean up old cache files

        Args:
            max_age_days: Maximum age in days for files to keep

        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        current_time = time.time()

        try:
            for cache_dir in [self.download_cache, self.extracted_cache]:
                if cache_dir.exists():
                    for file_path in cache_dir.rglob("*"):
                        if file_path.is_file():
                            file_age_days = (current_time - file_path.stat().st_mtime) / (24 * 3600)
                            if file_age_days > max_age_days:
                                try:
                                    file_path.unlink()
                                    cleaned_count += 1
                                    logger.debug(f"Removed old cache file: {file_path}")
                                except Exception as e:
                                    logger.warning(f"Could not remove old cache file {file_path}: {e}")

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old cache files")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

        return cleaned_count

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics

        Returns:
            Dictionary with detailed cache statistics
        """
        stats = {
            "total_size_mb": 0,
            "total_files": 0,
            "average_file_size_mb": 0,
            "oldest_file_age_days": None,
            "newest_file_age_days": None,
            "largest_file_size_mb": 0,
            "smallest_file_size_mb": None
        }

        if not self.cache_dir.exists():
            return stats

        try:
            file_ages = []
            file_sizes = []
            current_time = time.time()

            for cache_dir in [self.download_cache, self.extracted_cache]:
                if cache_dir.exists():
                    for file_path in cache_dir.rglob("*"):
                        if file_path.is_file():
                            file_size_mb = file_path.stat().st_size // (1024 * 1024)
                            file_ages.append((current_time - file_path.stat().st_mtime) / (24 * 3600))
                            file_sizes.append(file_size_mb)

            if file_sizes:
                stats["total_size_mb"] = sum(file_sizes)
                stats["total_files"] = len(file_sizes)
                stats["average_file_size_mb"] = stats["total_size_mb"] / stats["total_files"]
                stats["largest_file_size_mb"] = max(file_sizes)
                stats["smallest_file_size_mb"] = min(file_sizes)

                # Calculate file ages (in days from now)
                stats["oldest_file_age_days"] = max(file_ages)
                stats["newest_file_age_days"] = min(file_ages)

        except Exception as e:
            logger.warning(f"Could not generate cache statistics: {e}")

        return stats

    def verify_cache_integrity(self) -> Dict[str, Any]:
        """
        Verify cache file integrity

        Returns:
            Dictionary with integrity check results
        """
        integrity_report = {
            "valid_files": 0,
            "invalid_files": 0,
            "missing_files": 0,
            "corrupted_files": 0,
            "total_size_mb": 0,
            "issues": []
        }

        if not self.cache_dir.exists():
            integrity_report["issues"].append("Cache directory does not exist")
            return integrity_report

        try:
            for cache_dir in [self.download_cache, self.extracted_cache]:
                if cache_dir.exists():
                    for file_path in cache_dir.rglob("*.tar.gz"):
                        if file_path.is_file():
                            integrity_report["total_size_mb"] += file_path.stat().st_size // (1024 * 1024)

                            if not self._is_valid_cache_file(file_path):
                                integrity_report["invalid_files"] += 1
                                integrity_report["issues"].append(f"Invalid file: {file_path}")
                            else:
                                integrity_report["valid_files"] += 1
                        else:
                            integrity_report["missing_files"] += 1
                            integrity_report["issues"].append(f"Missing file: {file_path}")

        except Exception as e:
            integrity_report["issues"].append(f"Integrity check failed: {e}")

        logger.info(f"Cache integrity check: {integrity_report['valid_files']} valid, {integrity_report['invalid_files']} invalid files")
        return integrity_report
