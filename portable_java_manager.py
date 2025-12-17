#!/usr/bin/env python3
"""
Portable Java Detection and Offering System for jar2appimage

This module provides comprehensive Java detection and management capabilities:
- System Java detection and validation
- Portable Java offering system with user consent
- LTS version management and auto-detection
- Integration with existing bundlers
- Cross-platform support with proper fallbacks
"""

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class JavaDetectionError(Exception):
    """Exception raised when Java detection fails"""
    pass


class JavaCompatibilityError(Exception):
    """Exception raised when Java version is incompatible"""
    pass


class PortableJavaManager:
    """
    Comprehensive portable Java detection and offering system
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

    def __init__(self, interactive_mode: bool = True, cache_dir: Optional[str] = None, non_interactive_answer: bool = True):
        """
        Initialize the portable Java manager

        Args:
            interactive_mode: Whether to use interactive prompts
            cache_dir: Directory for caching downloads
            non_interactive_answer: The answer to return in non-interactive mode (default: True, i.e., 'yes')
        """
        self.interactive_mode = interactive_mode
        self.non_interactive_answer = non_interactive_answer
        self.current_platform = self._detect_platform()

        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".jar2appimage" / "java_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Download cache for Java archives
        self.download_cache = self.cache_dir / "downloads"
        self.download_cache.mkdir(exist_ok=True)

        logger.info(f"Initialized PortableJavaManager for {self.current_platform['system']} {self.current_platform['arch']}")

    def _detect_platform(self) -> Dict[str, Any]:
        """Detect current platform and architecture"""
        system = platform.system()
        machine = platform.machine()

        return {
            "system": system,
            "arch": self.ARCH_MAPPING.get(machine, machine),
            "machine": machine,
            "is_linux": system == "Linux",
            "is_macos": system == "Darwin",
            "is_windows": system == "Windows",
            "supports_appimage": system == "Linux"
        }

    def detect_system_java(self) -> Optional[Dict[str, Any]]:
        """
        Comprehensive system Java detection

        Returns:
            Dict with Java information or None if not found
        """
        logger.info("🔍 Detecting system Java installation...")

        try:
            # Check for java command
            java_cmd = self._find_java_command()
            if not java_cmd:
                logger.warning("No java command found in PATH")
                return None

            # Get Java version information
            version_info = self._get_java_version_info(java_cmd)
            if not version_info:
                logger.warning("Could not get Java version information")
                return None

            # Get Java home if available
            java_home = self._get_java_home(java_cmd)

            # Determine Java type (OpenJDK, Oracle, etc.)
            java_type = self._detect_java_type(java_cmd)

            # Check compatibility
            is_compatible = self._check_java_compatibility(version_info)

            java_info: Dict[str, Any] = {
                "command": java_cmd,
                "version": version_info["version"],
                "major_version": version_info["major"],
                "full_version": version_info["full"],
                "java_home": java_home,
                "type": java_type,
                "is_lts": str(version_info["major"]) in self.LTS_VERSIONS,
                "is_compatible": is_compatible,
                "architecture": version_info.get("architecture", "unknown"),
                "vm_info": version_info.get("vm_info", "")
            }

            logger.info(f"✅ Found Java {version_info['version']} ({java_type})")
            logger.info(f"   Command: {java_cmd}")
            logger.info(f"   Compatible: {is_compatible}")

            return java_info

        except Exception as e:
            logger.error(f"Java detection failed: {e}")
            return None

    def _find_java_command(self) -> Optional[str]:
        """Find java command in PATH"""
        try:
            result = subprocess.run(
                ["which", "java"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                java_path = result.stdout.strip()
                logger.debug(f"Found java at: {java_path}")
                return java_path
        except Exception:
            pass

        # Try common locations
        common_paths = [
            "/usr/bin/java",
            "/usr/local/bin/java",
            "/opt/java/bin/java",
            "/opt/jdk/bin/java",
            "/usr/lib/jvm/default-java/bin/java"
        ]

        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.debug(f"Found java at common path: {path}")
                return path

        return None

    def _get_java_version_info(self, java_cmd: str) -> Optional[Dict[str, Union[str, int]]]:
        """Get detailed Java version information"""
        try:
            # Get version with -version
            result = subprocess.run(
                [java_cmd, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            version_output = result.stderr  # Java writes version info to stderr

            # Parse version information
            version_match = re.search(r'"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:_(\d+))?"', version_output)
            if not version_match:
                return None

            major = int(version_match.group(1))
            minor = int(version_match.group(2)) if version_match.group(2) else 0
            patch = int(version_match.group(3)) if version_match.group(3) else 0

            # Construct version string
            if patch > 0:
                version_str = f"{major}.{minor}.{patch}"
            else:
                version_str = f"{major}.{minor}"

            # Extract VM information
            vm_match = re.search(r'(OpenJDK|Oracle JDK|Amazon Corretto|Eclipse Temurin)', version_output)
            vm_info = vm_match.group(1) if vm_match else "Unknown"

            # Get architecture info
            arch_match = re.search(r'64-Bit Server VM|64-Bit Client VM', version_output)
            architecture = "64-bit" if arch_match else "32-bit"

            return {
                "major": major,
                "minor": minor,
                "patch": patch,
                "version": version_str,
                "full": version_output.strip().split('\n')[0],
                "vm_info": vm_info,
                "architecture": architecture
            }

        except Exception as e:
            logger.error(f"Failed to get Java version info: {e}")
            return None

    def _get_java_home(self, java_cmd: str) -> Optional[str]:
        """Get JAVA_HOME from java command path"""
        try:
            # Resolve symbolic links
            java_path = os.path.realpath(java_cmd)

            # Common JAVA_HOME patterns
            java_home_patterns = [
                java_path.replace("/bin/java", ""),
                java_path.replace("/bin/java", "/.."),
                "/usr/lib/jvm/java",
                "/opt/java",
                "/opt/jdk",
                "/usr/lib/jvm/default-java"
            ]

            for pattern in java_home_patterns:
                java_home = os.path.abspath(pattern)
                if os.path.exists(os.path.join(java_home, "bin", "java")):
                    return java_home

            # Try using readlink and dirname
            java_bin_dir = os.path.dirname(java_path)
            potential_home = os.path.dirname(java_bin_dir)

            if os.path.exists(os.path.join(potential_home, "bin", "java")):
                return potential_home

        except Exception as e:
            logger.debug(f"Could not determine JAVA_HOME: {e}")

        return None

    def _detect_java_type(self, java_cmd: str) -> str:
        """Detect Java distribution type"""
        try:
            result = subprocess.run(
                [java_cmd, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            version_output = result.stderr.lower()

            if "openjdk" in version_output:
                return "OpenJDK"
            elif "oracle" in version_output:
                return "Oracle JDK"
            elif "corretto" in version_output:
                return "Amazon Corretto"
            elif "temurin" in version_output:
                return "Eclipse Temurin"
            elif "liberica" in version_output:
                return "Bellsoft Liberica"
            elif "graalvm" in version_output:
                return "GraalVM"
            else:
                return "Unknown"

        except Exception:
            return "Unknown"

    def _check_java_compatibility(self, version_info: Dict[str, Any]) -> bool:
        """
        Check if Java version is compatible with jar2appimage

        Basic compatibility check - can be enhanced based on specific requirements
        """
        major_version = int(version_info["major"])

        # Minimum Java version for jar2appimage
        min_java_version = 8

        # Maximum tested version (to avoid cutting-edge issues)
        max_java_version = 21

        return min_java_version <= major_version <= max_java_version

    def analyze_jar_requirements(self, jar_path: str) -> Dict[str, Any]:
        """
        Analyze JAR file for Java version requirements

        Args:
            jar_path: Path to JAR file

        Returns:
            Dict with Java requirement information
        """
        logger.info(f"📋 Analyzing JAR requirements: {jar_path}")

        requirements: Dict[str, Any] = {
            "min_java_version": None,
            "requires_modules": False,
            "main_class": None,
            "manifest_info": {},
            "class_analysis": {}
        }

        try:
            import zipfile

            with zipfile.ZipFile(jar_path, 'r') as jar:
                # Check manifest for Java requirements
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_content = jar.read('META-INF/MANIFEST.MF').decode('utf-8', errors='ignore')
                    requirements["manifest_info"] = self._parse_manifest_requirements(manifest_content)

                # Check for module-info.class (Java 9+ modules)
                if any(name.startswith('module-info.class') for name in jar.namelist()):
                    requirements["requires_modules"] = True

                # Extract main class if available
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_content = jar.read('META-INF/MANIFEST.MF').decode('utf-8', errors='ignore')
                    main_class_match = re.search(r'Main-Class:\s*(.+)', manifest_content)
                    if main_class_match:
                        requirements["main_class"] = main_class_match.group(1).strip()

        except Exception as e:
            logger.warning(f"Could not analyze JAR requirements: {e}")

        logger.info(f"✅ JAR analysis complete: {requirements}")
        return requirements

    def _parse_manifest_requirements(self, manifest_content: str) -> Dict[str, str]:
        """Parse manifest for Java version requirements"""
        requirements = {}

        lines = manifest_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Require-Capability:'):
                # Parse Java module requirements
                capability = line.split(':', 1)[1].strip()
                if 'java.version' in capability:
                    version_match = re.search(r'java\.version;version="([0-9.]+)"', capability)
                    if version_match:
                        requirements['min_java_version'] = version_match.group(1)

        return requirements

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
        """Get latest LTS version from Adoptium API"""
        try:
            available_versions = []

            for lts_version in self.LTS_VERSIONS:
                try:
                    api_url = f"https://api.adoptium.net/v3/assets/feature_releases/{lts_version}/ga?architecture=x64&image_type=jdk&os=linux&sort_method=DATE&sort_order=DESC"

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

    def check_java_download_needed(self, system_java: Optional[Dict], jar_requirements: Dict) -> Tuple[bool, str]:
        """
        Determine if Java download is needed

        Returns:
            Tuple of (download_needed, reason)
        """
        if not system_java:
            return True, "No system Java found"

        if not system_java["is_compatible"]:
            return True, f"System Java {system_java['version']} is not compatible"

        # Check if JAR has specific requirements
        min_jar_version = jar_requirements.get("min_java_version")
        if min_jar_version:
            jar_major = int(min_jar_version.split('.')[0])
            system_major = system_java["major_version"]
            if system_major < jar_major:
                return True, f"System Java {system_major} is below JAR requirement {jar_major}"

        # Check if bundled Java is preferred
        if jar_requirements.get("requires_modules"):
            # Modules require Java 9+, prefer bundled for compatibility
            return True, "JAR requires Java modules, bundled Java recommended"

        return False, "System Java is sufficient"

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
        if not download_needed:
            logger.info("✅ System Java is sufficient, no download needed")
            return False

        logger.info(f"📥 Portable Java recommended: {reason}")

        if not self.interactive_mode:
            logger.info(f"🔧 Non-interactive mode: assuming '{'yes' if self.non_interactive_answer else 'no'}'")
            return self.non_interactive_answer

        # Get download information
        download_info = self._get_download_info(java_version)

        print("\n" + "="*60)
        print("🚀 PORTABLE JAVA DETECTION AND DOWNLOAD OFFER")
        print("="*60)
        print("\n📋 Analysis Results:")
        print(f"   • System Java: {'Available' if download_info['has_system_java'] else 'Not found'}")
        print(f"   • Recommendation: Download portable Java {java_version}")
        print(f"   • Reason: {reason}")

        print("\n📦 Download Information:")
        print(f"   • Version: Java {java_version} (LTS)")
        print(f"   • Size: ~{download_info['estimated_size_mb']} MB")
        print("   • Type: JRE (Java Runtime Environment)")
        print(f"   • Architecture: {self.current_platform['arch']}")
        print(f"   • Download time: ~{download_info['estimated_time_minutes']} minutes")

        print("\n💡 Benefits of Portable Java:")
        print("   • Self-contained AppImage (no external dependencies)")
        print("   • Works on any Linux distribution")
        print("   • Latest security updates and features")
        print("   • Consistent Java version across deployments")

        print("\n⚠️  What will be downloaded:")
        print(f"   • Java {java_version} runtime files")
        print(f"   • Stored in: {self.download_cache}")
        print("   • Used for creating portable AppImages")

        # Ask for consent
        while True:
            print(f"\n❓ Do you want to download Java {java_version}?")
            response = input("   [Y]es / [N]o / [I]nfo: ").strip().lower()

            if response in ['y', 'yes']:
                print(f"\n✅ Consent received. Downloading Java {java_version}...")
                return True
            elif response in ['n', 'no']:
                print("\n❌ Download cancelled. Will use system Java if available.")
                return False
            elif response in ['i', 'info']:
                self._show_detailed_download_info(java_version, download_info)
            else:
                print("   Please enter Y, N, or I")

    def _get_download_info(self, java_version: str) -> Dict[str, Any]:
        """Get information about Java download"""
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
            "has_system_java": self.detect_system_java() is not None,
            "package_type": "JRE",
            "architecture": self.current_platform["arch"]
        }

    def _show_detailed_download_info(self, java_version: str, download_info: Dict[str, Any]) -> None:
        """Show detailed download information"""
        print(f"\n📋 Detailed Information for Java {java_version}:")
        print(f"   • Package Type: {download_info['package_type']} (Java Runtime Environment)")
        print(f"   • Architecture: {download_info['architecture']}")
        print(f"   • Estimated Size: {download_info['estimated_size_mb']} MB")
        print(f"   • Download Time: ~{download_info['estimated_time_minutes']} minutes")
        print(f"   • Cache Location: {self.download_cache}")
        print("   • Source: Adoptium (Eclipse Temurin)")

        print("\n🔧 Technical Details:")
        print(f"   • Based on OpenJDK {java_version}")
        print("   • Linux x64 compatible")
        print("   • Includes JavaFX (if applicable)")
        print("   • Security updates included")

        print("\n💾 Storage:")
        print("   • Downloaded files cached locally")
        print("   • Reused for future AppImages")
        print("   • Can be cleared with --clear-cache")

    def _get_dynamic_download_url(self, java_version: str) -> Optional[str]:
        """
        Get dynamic download URL from Adoptium API

        Args:
            java_version: Java version to download

        Returns:
            Download URL or None if not found
        """
        try:
            os_type = self.current_platform["system"].lower()
            arch = self.current_platform["arch"]
            url = (
                f"https://api.adoptium.net/v3/binary/latest/{java_version}/ga/{os_type}/{arch}/jre/hotspot/normal/eclipse"
                f"?project=temurin"
            )
            logger.info(f"Trying to resolve Java download URL: {url}")
            # This request will redirect to the actual download URL
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.url
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f"Java version {java_version} not found on Adoptium API for this platform.")
            else:
                logger.error(f"API request failed for Java {java_version}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get dynamic download URL for Java {java_version}: {e}")
            return None

    # Download thresholds (MB)
    MIN_DOWNLOAD_SIZE_MB = 10

    def _download_from_url(self, download_url: str, java_version: str) -> Optional[str]:
        """Download file from URL and cache it.

        Uses Content-Length header when available to validate size; falls back to
        measuring downloaded size. Small files are removed and considered failures.
        """
        try:
            filename = download_url.split("/")[-1]
            java_path = self.download_cache / filename

            logger.info(f"📥 Downloading from: {download_url}")

            req = urllib.request.Request(download_url, headers={"User-Agent": "jar2appimage/1.0"})
            with urllib.request.urlopen(req) as response:
                # Try to use Content-Length header if present
                content_length = response.getheader('Content-Length') if hasattr(response, 'getheader') else None

                with open(java_path, 'wb') as f:
                    shutil.copyfileobj(response, f)

            # Validate size
            size_bytes = java_path.stat().st_size if java_path.exists() else 0
            min_bytes = self.MIN_DOWNLOAD_SIZE_MB * 1024 * 1024

            if content_length is not None:
                try:
                    content_length_int = int(content_length)
                except Exception:
                    content_length_int = None
            else:
                content_length_int = None

            if content_length_int is not None:
                valid = content_length_int >= min_bytes
            else:
                valid = size_bytes >= min_bytes

            if java_path.exists() and valid:
                size_mb = size_bytes // (1024 * 1024)
                logger.info(f"✅ Downloaded Java {java_version}: {filename} ({size_mb} MB)")
                return str(java_path)
            else:
                logger.error("Download failed or file is too small.")
                if java_path.exists():
                    java_path.unlink() # remove corrupted file
                return None
        except Exception as e:
            logger.error(f"Download from URL failed: {e}")
            return None

    def download_portable_java(self, java_version: str, force: bool = False) -> Optional[str]:
        """
        Download portable Java runtime, using dynamic URLs first.

        Args:
            java_version: Java version to download
            force: Force download even if cached version exists

        Returns:
            Path to downloaded Java archive or None if failed
        """
        logger.info(f"📥 Attempting to download portable Java {java_version}...")

        if not force:
            cached_file = self._get_cached_java(java_version)
            if cached_file:
                logger.info(f"📦 Found cached Java {java_version}: {cached_file}")
                return str(cached_file)

        # Primary method: dynamic URL from API
        download_url = self._get_dynamic_download_url(java_version)
        if download_url:
            downloaded_file = self._download_from_url(download_url, java_version)
            if downloaded_file:
                return downloaded_file

        # Fallback to old bundler logic if dynamic download fails
        logger.warning("Dynamic download failed, trying legacy bundler methods.")
        try:
            from smart_java_bundler import SmartJavaBundler
            bundler = SmartJavaBundler(java_version=java_version, use_jre=True)
            downloaded_file = bundler.download_java(str(self.download_cache))
            if downloaded_file:
                self._cache_download(downloaded_file, java_version)
                return downloaded_file
        except ImportError:
            logger.error("SmartJavaBundler not available, and all download attempts failed.")
        except Exception as e:
            logger.error(f"Legacy bundler download failed: {e}")
        
        logger.error(f"All methods to download Java {java_version} failed.")
        return None

    # Cached thresholds (MB)
    MIN_CACHED_SIZE_MB = 50

    def _get_cached_java(self, java_version: str) -> Optional[Path]:
        """Check for cached Java download"""
        cache_pattern = f"*{java_version}*.tar.gz"
        for cached_file in self.download_cache.glob(cache_pattern):
            if cached_file.exists() and cached_file.stat().st_size > self.MIN_CACHED_SIZE_MB * 1024 * 1024:
                return cached_file
        return None

    def _cache_download(self, downloaded_file: str, java_version: str) -> None:
        """Cache the downloaded file"""
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
            import tarfile

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

    def clear_cache(self) -> bool:
        """
        Clear Java download cache

        Returns:
            True if cache was cleared
        """
        try:
            if self.download_cache.exists():
                shutil.rmtree(self.download_cache)
                self.download_cache.mkdir(parents=True, exist_ok=True)
                logger.info("✅ Java download cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

        return False

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached Java downloads

        Returns:
            Dict with cache information
        """
        cache_info: Dict[str, Any] = {
            "cache_dir": str(self.download_cache),
            "total_files": 0,
            "total_size_mb": 0,
            "java_versions": [],
            "available": self.download_cache.exists()
        }

        if self.download_cache.exists():
            try:
                for file_path in self.download_cache.glob("*.tar.gz"):
                    cache_info["total_files"] += 1
                    cache_info["total_size_mb"] += file_path.stat().st_size // (1024 * 1024)

                    # Extract version from filename
                    filename = file_path.name
                    version_match = re.search(r'jdk?(\d+)', filename)
                    if version_match:
                        version = version_match.group(1)
                        if version not in cache_info["java_versions"]:
                            cache_info["java_versions"].append(version)
            except Exception as e:
                logger.warning(f"Could not read cache info: {e}")

        return cache_info


# Convenience functions for easy integration

def detect_and_manage_java(jar_path: str, interactive: bool = True, non_interactive_answer: bool = True) -> Tuple[Optional[str], bool]:
    """
    Detect system Java and offer portable Java if needed

    Args:
        jar_path: Path to JAR file
        interactive: Whether to use interactive prompts
        non_interactive_answer: The answer to return in non-interactive mode

    Returns:
        Tuple of (java_version_to_use, download_consented)
    """
    manager = PortableJavaManager(interactive_mode=interactive, non_interactive_answer=non_interactive_answer)

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
        consent = manager.offer_portable_java(download_needed, reason, java_version)

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Portable Java Detection and Management for jar2appimage")
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
        if java_info:
            print(f"✅ Found Java {java_info['version']} ({java_info['type']})")
            print(f"   Command: {java_info['command']}")
            print(f"   Compatible: {java_info['is_compatible']}")
            if java_info['java_home']:
                print(f"   JAVA_HOME: {java_info['java_home']}")
        else:
            print("❌ No compatible Java found")

    elif args.jar:
        system_java = manager.detect_system_java()
        jar_requirements = manager.analyze_jar_requirements(args.jar)
        download_needed, reason = manager.check_java_download_needed(system_java, jar_requirements)

        print(f"📋 JAR Analysis for {args.jar}:")
        print(f"   Main Class: {jar_requirements.get('main_class', 'Not specified')}")
        print(f"   Requires Modules: {jar_requirements.get('requires_modules', False)}")
        print(f"   System Java: {'Available' if system_java else 'Not found'}")
        print(f"   Download Needed: {download_needed}")
        if download_needed:
            print(f"   Reason: {reason}")

    elif args.download:
        version = args.version or manager.get_latest_lts_version()
        print(f"📥 Downloading Java {version}...")
        downloaded = manager.download_portable_java(version)
        if downloaded:
            print(f"✅ Downloaded: {downloaded}")
        else:
            print("❌ Download failed")

    elif args.cache_info:
        cache_info = manager.get_cache_info()
        print("📦 Java Download Cache:")
        print(f"   Location: {cache_info['cache_dir']}")
        print(f"   Total Files: {cache_info['total_files']}")
        print(f"   Total Size: {cache_info['total_size_mb']} MB")
        print(f"   Java Versions: {', '.join(cache_info['java_versions'])}")

    elif args.clear_cache:
        if manager.clear_cache():
            print("✅ Cache cleared")
        else:
            print("❌ Failed to clear cache")

    else:
        summary = get_java_detection_summary()
        print("🔍 Java Detection Summary:")
        print(f"   System Java: {'Found' if summary['system_java'] else 'Not found'}")
        print(f"   Latest LTS: {summary['latest_lts']}")
        print(f"   Platform: {summary['platform']['system']} {summary['platform']['arch']}")
        print(f"   Cache: {summary['cache_info']['total_files']} files, {summary['cache_info']['total_size_mb']} MB")
