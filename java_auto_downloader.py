#!/usr/bin/env python3
"""
Automatic Java Downloader for jar2appimage
Automatically downloads the latest LTS Java version when no specific version is provided
"""

import json
import logging
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


class JavaAutoDownloader:
    """Automatically discovers and downloads the latest LTS Java version"""

    # LTS Java versions (as of 2025)
    LTS_VERSIONS = ["8", "11", "17", "21"]

    def __init__(self) -> None:
        self.cache: Dict[str, Any] = {}  # Cache for API responses
        self.download_cache_dir: Path = Path.home() / ".jar2appimage" / "java_downloads"
        self.download_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_latest_lts_version(self) -> str:
        """
        Get the latest LTS Java version
        Returns the most recent LTS version number
        """
        print("🔍 Checking for latest LTS Java version...")
        logger.info("Checking for latest LTS Java version")

        # Try to get the latest LTS from Adoptium API
        try:
            latest_version = self._get_latest_lts_from_api()
            if latest_version:
                print(f"✅ Found latest LTS version: {latest_version}")
                logger.info(f"Found latest LTS version: {latest_version}")
                return latest_version
        except Exception as e:
            print(f"⚠️  API lookup failed: {e}")
            logger.warning(f"API lookup failed: {e}")

        # Fallback to hardcoded latest LTS (21 as of 2025-12-16)
        fallback_version = "21"
        print(f"📋 Using fallback LTS version: {fallback_version}")
        logger.info(f"Using fallback LTS version: {fallback_version}")
        return fallback_version

    def _get_latest_lts_from_api(self) -> Optional[str]:
        """Get latest LTS version from Adoptium API by checking all LTS versions"""
        try:
            available_versions = []

            # Check each LTS version to find all available ones
            for lts_version in self.LTS_VERSIONS:
                try:
                    # Query for the latest release of this specific LTS version
                    api_url = f"https://api.adoptium.net/v3/assets/feature_releases/{lts_version}/ga?architecture=x64&image_type=jdk&os=linux&sort_method=DATE&sort_order=DESC"

                    req = urllib.request.Request(
                        api_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                        },
                    )

                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())

                    # Check if we got valid data for this version
                    if data and len(data) > 0:
                        available_versions.append(int(lts_version))

                except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception):
                    # Continue to next version if this one fails
                    continue

            # Return the highest available LTS version
            if available_versions:
                return str(max(available_versions))

            return None

        except Exception as e:
            logger.debug(f"Failed to get latest LTS from API: {e}")
            pass

        return None

    def auto_download_java(self, output_dir: str = ".", java_version: Optional[str] = None) -> Optional[str]:
        """
        Automatically download Java - uses latest LTS if no version specified

        Args:
            output_dir: Directory to download Java to
            java_version: Specific Java version, or None for auto-detection

        Returns:
            Path to downloaded Java archive, or None if failed
        """
        # Auto-detect version if not specified
        if java_version is None:
            java_version = self.get_latest_lts_version()
            print(f"🎯 Auto-detected Java version: {java_version}")
        else:
            print(f"🎯 Using specified Java version: {java_version}")

        # Check cache first
        cached_file = self._get_cached_download(java_version)
        if cached_file and cached_file.exists():
            print(f"📦 Found cached Java {java_version}: {cached_file}")
            logger.info(f"Found cached Java {java_version}: {cached_file}")
            return str(cached_file)

        # Download using existing smart bundler
        try:
            from smart_java_bundler import SmartJavaBundler
            bundler = SmartJavaBundler(java_version=java_version, use_jre=True)

            downloaded_file = bundler.download_java(output_dir)
            if downloaded_file:
                # Cache the download
                self._cache_download(downloaded_file, java_version)
                return downloaded_file

        except ImportError:
            print("⚠️  SmartJavaBundler not available, using fallback method")
            logger.warning("SmartJavaBundler not available, using fallback method")
            return self._fallback_download(java_version, output_dir)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            logger.error(f"Download failed: {e}")
            return self._fallback_download(java_version, output_dir)

        return None

    def _fallback_download(self, java_version: str, output_dir: str) -> Optional[str]:
        """Fallback download method using hardcoded URLs"""
        fallbacks = {
            "8": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u412b08.tar.gz",
            "11": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jdk_x64_linux_hotspot_11.0.23_9.tar.gz",
            "17": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz",
            "21": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_linux_hotspot_21.0.4_7.tar.gz",
        }

        download_url = fallbacks.get(java_version)
        if not download_url:
            print(f"❌ No fallback URL available for Java {java_version}")
            logger.error(f"No fallback URL available for Java {java_version}")
            return None

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        filename = download_url.split("/")[-1]
        java_path = output_dir_path / filename

        print(f"📥 Downloading Java {java_version} from fallback URL...")
        print(f"   URL: {download_url}")
        logger.info(f"Downloading Java {java_version} from fallback URL: {download_url}")

        try:
            subprocess.run(
                ["curl", "-L", "--progress-bar", "-o", str(java_path), download_url],
                check=True,
                capture_output=True,
                text=True,
            )

            if java_path.exists():
                size_mb = java_path.stat().st_size // (1024 * 1024)
                print(f"✅ Java {java_version} downloaded: {filename} ({size_mb} MB)")
                logger.info(f"Java {java_version} downloaded successfully: {filename} ({size_mb} MB)")
                return str(java_path)
            else:
                print("❌ Download completed but file not found")
                logger.error("Download completed but file not found")
                return None

        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e}")
            logger.error(f"Download failed: {e}")
            return None

    def _get_cached_download(self, java_version: str) -> Optional[Path]:
        """Check if we have a cached download for this version"""
        cache_pattern = f"*{java_version}*.tar.gz"
        for cached_file in self.download_cache_dir.glob(cache_pattern):
            if cached_file.exists() and cached_file.stat().st_size > 100 * 1024 * 1024:  # At least 100MB
                logger.debug(f"Found cached download for Java {java_version}: {cached_file}")
                return cached_file
        return None

    def _cache_download(self, downloaded_file: str, java_version: str) -> None:
        """Cache the downloaded file"""
        try:
            source_path = Path(downloaded_file)
            if source_path.exists():
                # Create a standardized cache filename
                cache_filename = f"java-{java_version}-{source_path.name}"
                cache_path = self.download_cache_dir / cache_filename

                # Copy to cache (only if not already cached)
                if not cache_path.exists():
                    shutil.copy2(source_path, cache_path)
                    print(f"📦 Cached Java {java_version}: {cache_path}")
                    logger.info(f"Cached Java {java_version}: {cache_path}")
        except Exception as e:
            print(f"⚠️  Failed to cache download: {e}")
            logger.warning(f"Failed to cache download: {e}")

    def get_java_info(self, java_version: Optional[str] = None) -> Dict:
        """Get information about a Java version"""
        if java_version is None:
            java_version = self.get_latest_lts_version()

        return {
            "version": java_version,
            "is_lts": java_version in self.LTS_VERSIONS,
            "type": "LTS" if java_version in self.LTS_VERSIONS else "Non-LTS",
            "download_ready": self._get_cached_download(java_version) is not None,
        }


def auto_download_latest_lts(output_dir: str = ".") -> Optional[str]:
    """
    Convenient function to automatically download the latest LTS Java version

    Args:
        output_dir: Directory to download Java to

    Returns:
        Path to downloaded Java archive, or None if failed
    """
    downloader = JavaAutoDownloader()
    return downloader.auto_download_java(output_dir)


def get_auto_java_version() -> str:
    """
    Get the automatically detected latest LTS Java version

    Returns:
        Version string (e.g., "21")
    """
    downloader = JavaAutoDownloader()
    return downloader.get_latest_lts_version()


if __name__ == "__main__":
    import argparse

    # Setup logging for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(description="Automatic Java Downloader for jar2appimage")
    parser.add_argument(
        "--output", "-o", default=".", help="Output directory for downloads"
    )
    parser.add_argument(
        "--version", "-v", help="Specific Java version (auto-detects LTS if not specified)"
    )
    parser.add_argument(
        "--info", action="store_true", help="Show Java version information"
    )
    parser.add_argument(
        "--cache-dir", action="store_true", help="Show cache directory location"
    )

    args = parser.parse_args()

    downloader = JavaAutoDownloader()

    if args.cache_dir:
        print(f"📦 Java download cache: {downloader.download_cache_dir}")
    elif args.info:
        java_version = args.version if args.version else downloader.get_latest_lts_version()
        info = downloader.get_java_info(java_version)
        print("Java Version Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        downloaded_file = downloader.auto_download_java(args.output, args.version)
        if downloaded_file:
            print(f"✅ Downloaded: {downloaded_file}")
        else:
            print("❌ Failed to download Java", file=sys.stderr)
            sys.exit(1)
