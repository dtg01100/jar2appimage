#!/usr/bin/env python3
"""
Java Downloader Module

This module handles Java version detection, downloading, and extraction logic.
Manages network operations, API calls, file downloads, and archive extraction.

Key Responsibilities:
- Java version detection and LTS management
- Network downloads and API calls
- Archive extraction and file system operations
- Integration with existing bundlers
"""

import json
import logging
import shutil
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class JavaDownloader:
    """
    Handles Java downloading, extraction, and integration operations
    """
    
    # LTS Java versions (as of 2025-12-16)
    LTS_VERSIONS = ["8", "11", "17", "21"]
    CURRENT_LTS = "21"  # Latest LTS as of current date
    
    # Architecture mapping
    ARCH_MAPPING = {
        "x86_64": "x64",
        "amd64": "x64", 
        "aarch64": "aarch64",
        "arm64": "aarch64"
    }
    
    # Fallback download URLs for manual downloads
    FALLBACK_URLS = {
        "8": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jre_x64_linux_hotspot_8u412b08.tar.gz",
        "11": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jre_x64_linux_hotspot_11.0.23_9.tar.gz",
        "17": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jre_x64_linux_hotspot_17.0.12_7.tar.gz",
        "21": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jre_x64_linux_hotspot_21.0.4_7.tar.gz",
    }
    
    def __init__(self, download_cache: Path):
        """
        Initialize the Java downloader
        
        Args:
            download_cache: Directory for caching downloads
        """
        self.download_cache = download_cache
        self.download_cache.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized JavaDownloader with cache: {self.download_cache}")
    
    def get_latest_lts_version(self, force_update: bool = False) -> str:
        """
        Get the latest LTS Java version
        
        Args:
            force_update: Force API check instead of using cached value
            
        Returns:
            Latest LTS version string
        """
        if not force_update:
            # Return current known LTS
            return self.CURRENT_LTS

        logger.info("🔍 Checking for latest LTS Java version...")

        try:
            # Try to get from Adoptium API
            latest_version = self._get_latest_lts_from_api()
            if latest_version:
                logger.info(f"✅ Found latest LTS version: {latest_version}")
                return latest_version
        except Exception as e:
            logger.warning(f"API lookup failed: {e}")

        # Fallback to hardcoded current LTS
        logger.info(f"📋 Using fallback LTS version: {self.CURRENT_LTS}")
        return self.CURRENT_LTS
    
    def _get_latest_lts_from_api(self) -> Optional[str]:
        """
        Get latest LTS version from Adoptium API
        
        Returns:
            Latest LTS version string or None if failed
        """
        try:
            available_versions = []

            for lts_version in self.LTS_VERSIONS:
                try:
                    api_url = (
                        f"https://api.adoptium.net/v3/assets/feature_releases/{lts_version}/ga"
                        f"?architecture=x64&image_type=jdk&os=linux"
                        f"&sort_method=DATE&sort_order=DESC"
                    )

                    req = urllib.request.Request(
                        api_url,
                        headers={"User-Agent": "jar2appimage/1.0"}
                    )

                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())

                    if data and len(data) > 0:
                        available_versions.append(int(lts_version))

                except Exception:
                    continue

            if available_versions:
                return str(max(available_versions))

        except Exception:
            pass

        return None
    
    def download_portable_java(self, java_version: str, force: bool = False) -> Optional[str]:
        """
        Download portable Java runtime
        
        Args:
            java_version: Java version to download
            force: Force download even if cached version exists
            
        Returns:
            Path to downloaded Java archive or None if failed
        """
        logger.info(f"📥 Downloading portable Java {java_version}...")

        # Check cache first
        if not force:
            cached_file = self._get_cached_java(java_version)
            if cached_file:
                logger.info(f"📦 Found cached Java {java_version}: {cached_file}")
                return str(cached_file)

        try:
            # Try using existing SmartJavaBundler
            try:
                from smart_java_bundler import SmartJavaBundler
                bundler = SmartJavaBundler(java_version=java_version, use_jre=True)
                downloaded_file = bundler.download_java(str(self.download_cache))
                if downloaded_file:
                    self._cache_download(downloaded_file, java_version)
                    return downloaded_file
            except ImportError:
                logger.warning("SmartJavaBundler not available, using fallback")

            # Fallback to manual download
            return self._fallback_download(java_version)

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def _get_cached_java(self, java_version: str) -> Optional[Path]:
        """
        Check for cached Java download
        
        Args:
            java_version: Java version to check for
            
        Returns:
            Path to cached file or None if not found
        """
        cache_pattern = f"*{java_version}*.tar.gz"
        for cached_file in self.download_cache.glob(cache_pattern):
            if cached_file.exists() and cached_file.stat().st_size > 50 * 1024 * 1024:  # At least 50MB
                return cached_file
        return None
    
    def _cache_download(self, downloaded_file: str, java_version: str) -> None:
        """
        Cache the downloaded file
        
        Args:
            downloaded_file: Path to downloaded file
            java_version: Java version
        """
        try:
            source_path = Path(downloaded_file)
            if source_path.exists():
                cache_filename = f"java-{java_version}-{source_path.name}"
                cache_path = self.download_cache / cache_filename

                if not cache_path.exists():
                    shutil.copy2(source_path, cache_path)
                    logger.info(f"📦 Cached Java {java_version}: {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache download: {e}")
    
    def _fallback_download(self, java_version: str) -> Optional[str]:
        """
        Fallback download method using hardcoded URLs
        
        Args:
            java_version: Java version to download
            
        Returns:
            Path to downloaded file or None if failed
        """
        download_url = self.FALLBACK_URLS.get(java_version)
        if not download_url:
            logger.error(f"No fallback URL for Java {java_version}")
            return None

        try:
            filename = download_url.split("/")[-1]
            java_path = self.download_cache / filename

            logger.info("📥 Downloading from fallback URL...")
            logger.info(f"   URL: {download_url}")

            req = urllib.request.Request(download_url, headers={"User-Agent": "jar2appimage/1.0"})
            with urllib.request.urlopen(req) as response:
                with open(java_path, 'wb') as f:
                    shutil.copyfileobj(response, f)

            if java_path.exists():
                size_mb = java_path.stat().st_size // (1024 * 1024)
                logger.info(f"✅ Downloaded Java {java_version}: {filename} ({size_mb} MB)")
                return str(java_path)

        except Exception as e:
            logger.error(f"Fallback download failed: {e}")

        return None
    
    def extract_java_runtime(self, java_archive: str, extract_dir: str) -> Optional[str]:
        """
        Extract Java runtime from archive
        
        Args:
            java_archive: Path to Java archive
            extract_dir: Directory to extract to
            
        Returns:
            Path to extracted Java directory or None if failed
        """
        logger.info(f"📦 Extracting Java runtime from {java_archive}")

        try:
            extract_path = Path(extract_dir)
            extract_path.mkdir(parents=True, exist_ok=True)

            with tarfile.open(java_archive, 'r:gz') as tar:
                # Extract to temp directory
                temp_extract = extract_path / "temp_java"
                temp_extract.mkdir(exist_ok=True)

                tar.extractall(temp_extract)

                # Find Java directory
                java_dir = None
                for item in temp_extract.iterdir():
                    if item.is_dir() and (item.name.startswith("jdk-") or item.name.startswith("jre-")):
                        java_dir = item
                        break

                if not java_dir:
                    logger.error("Could not find Java directory in archive")
                    return None

                # Move to final location
                final_java_dir = extract_path / java_dir.name
                if final_java_dir.exists():
                    shutil.rmtree(final_java_dir)

                java_dir.rename(final_java_dir)
                shutil.rmtree(temp_extract, ignore_errors=True)

                logger.info(f"✅ Java extracted to: {final_java_dir}")
                return str(final_java_dir)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None
    
    def create_portable_java_integration(self, java_dir: str, appimage_dir: str) -> bool:
        """
        Create portable Java integration for AppImage
        
        Args:
            java_dir: Directory containing extracted Java
            appimage_dir: AppImage directory structure
            
        Returns:
            True if successful
        """
        logger.info("🔧 Integrating portable Java into AppImage structure")

        try:
            from smart_java_bundler import SmartJavaBundler

            bundler = SmartJavaBundler()
            return bundler.bundle_java_for_appimage(java_dir, appimage_dir)

        except ImportError:
            # Manual integration if SmartJavaBundler not available
            return self._manual_integration(java_dir, appimage_dir)
    
    def _manual_integration(self, java_dir: str, appimage_dir: str) -> bool:
        """
        Manual Java integration for AppImage
        
        Args:
            java_dir: Directory containing extracted Java
            appimage_dir: AppImage directory structure
            
        Returns:
            True if successful
        """
        java_path = Path(java_dir)
        appimage_java_dir = Path(appimage_dir) / "usr" / "java"
        appimage_java_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Copy Java files
            for item in java_path.iterdir():
                src = java_path / item.name
                dst = appimage_java_dir / item.name

                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # Verify Java binary exists
            java_binary = appimage_java_dir / "bin" / "java"
            if java_binary.exists():
                logger.info("✅ Portable Java integrated successfully")
                return True
            else:
                logger.error("Java binary not found after integration")
                return False

        except Exception as e:
            logger.error(f"Manual integration failed: {e}")
            return False
    
    def get_download_info(self, java_version: str, has_system_java: bool = False) -> Dict[str, Any]:
        """
        Get information about Java download
        
        Args:
            java_version: Java version
            has_system_java: Whether system Java is available
            
        Returns:
            Dictionary with download information
        """
        # Estimated sizes for different Java versions (JRE)
        size_estimates = {
            "8": 45,   # MB
            "11": 35,  # MB
            "17": 30,  # MB
            "21": 32   # MB
        }

        estimated_size_mb = size_estimates.get(java_version, 35)

        # Estimate download time (assuming 5 MB/s)
        estimated_time_minutes = max(1, estimated_size_mb // 5)

        return {
            "version": java_version,
            "estimated_size_mb": estimated_size_mb,
            "estimated_time_minutes": estimated_time_minutes,
            "has_system_java": has_system_java,
            "package_type": "JRE",
            "architecture": "x64",  # Default for Linux
            "cache_dir": str(self.download_cache)
        }