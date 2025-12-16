#!/usr/bin/env python3
"""
Unified Java Bundler for jar2appimage

A consolidated, well-designed Java bundling module that combines the best features
from multiple implementations while maintaining clean architecture and proper
separation of concerns.

Key Features:
- Smart Java detection and download
- Multiple bundling strategies
- Proper error handling and logging
- User interaction support
- Configuration management
- Platform compatibility
- Testing support through dependency injection

Author: jar2appimage Development Team
Version: 1.0.0
"""

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, Tuple, Union, cast

# Configure module-level logger
logger = logging.getLogger(__name__)


class JavaBundlerError(Exception):
    """Base exception for Java bundler operations"""
    pass


class JavaDetectionError(JavaBundlerError):
    """Raised when Java detection fails"""
    pass


class JavaDownloadError(JavaBundlerError):
    """Raised when Java download fails"""
    pass


class JavaExtractionError(JavaBundlerError):
    """Raised when Java extraction fails"""
    pass


class JavaBundlingError(JavaBundlerError):
    """Raised when Java bundling fails"""
    pass


class Configuration:
    """Configuration management for Java bundler operations"""

    def __init__(
        self,
        java_version: str = "17",
        use_jre: bool = True,
        interactive_mode: bool = True,
        cache_dir: Optional[str] = None,
        bundling_strategy: str = "appimage"
    ):
        """
        Initialize configuration

        Args:
            java_version: Java version to use (8, 11, 17, 21)
            use_jre: Use JRE (smaller) vs JDK (full)
            interactive_mode: Enable user interaction prompts
            cache_dir: Directory for caching downloads
            bundling_strategy: Bundling approach ('appimage', 'tarball', 'simple')
        """
        self.java_version = java_version
        self.use_jre = use_jre
        self.interactive_mode = interactive_mode
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jar2appimage" / "java_cache"
        self.bundling_strategy = bundling_strategy

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # LTS versions for automatic selection
        self.lts_versions = ["8", "11", "17", "21"]

        # Architecture mapping
        self.arch_mapping = {
            "x86_64": "x64",
            "amd64": "x64",
            "aarch64": "aarch64",
            "arm64": "aarch64"
        }

        logger.debug(f"Configuration initialized: {self}")

    def __repr__(self) -> str:
        return (f"Configuration(java_version={self.java_version}, use_jre={self.use_jre}, "
                f"interactive_mode={self.interactive_mode}, cache_dir={self.cache_dir}, "
                f"bundling_strategy={self.bundling_strategy})")

    @property
    def package_type(self) -> str:
        """Get package type string"""
        return "jre" if self.use_jre else "jdk"

    @property
    def target_arch(self) -> str:
        """Get target architecture"""
        machine = platform.machine()
        return self.arch_mapping.get(machine, machine)

    @property
    def is_lts_version(self) -> bool:
        """Check if configured version is LTS"""
        return self.java_version in self.lts_versions


class JavaDetector:
    """Java detection and analysis component"""

    def __init__(self, config: Configuration):
        """
        Initialize Java detector

        Args:
            config: Configuration instance
        """
        self.config = config
        self._platform_info = self._detect_platform()

    def _detect_platform(self) -> Dict[str, Union[str, bool]]:
        """Detect current platform and architecture"""
        system = platform.system()
        machine = platform.machine()

        return {
            "system": system,
            "arch": self.config.arch_mapping.get(machine, machine),
            "machine": machine,
            "is_linux": system == "Linux",
            "is_macos": system == "Darwin",
            "is_windows": system == "Windows",
            "supports_appimage": system == "Linux"
        }

    def detect_system_java(self) -> Optional[Dict[str, Union[str, int, bool, None]]]:
        """
        Comprehensive system Java detection

        Returns:
            Dict with Java information or None if not found
        """
        logger.info("Detecting system Java installation...")

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

            # Determine Java type
            java_type = self._detect_java_type(java_cmd)

            # Check compatibility
            is_compatible = self._check_java_compatibility(version_info)

            java_info = {
                "command": java_cmd,
                "version": version_info["version"],
                "major_version": version_info["major"],
                "full_version": version_info["full"],
                "java_home": java_home,
                "type": java_type,
                "is_lts": str(version_info["major"]) in self.config.lts_versions,
                "is_compatible": is_compatible,
                "architecture": version_info.get("architecture", "unknown"),
                "vm_info": version_info.get("vm_info", "")
            }

            logger.info(f"Found Java {version_info['version']} ({java_type})")
            logger.info(f"  Command: {java_cmd}")
            logger.info(f"  Compatible: {is_compatible}")

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

        Args:
            version_info: Java version information dictionary

        Returns:
            True if compatible, False otherwise
        """
        # Ensure we have an integer major version for comparisons
        try:
            major_version = int(version_info.get("major", 0))
        except (TypeError, ValueError):
            major_version = 0

        # Minimum/maximum Java version for jar2appimage
        min_java_version = 8
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
        logger.info(f"Analyzing JAR requirements: {jar_path}")

        requirements: Dict[str, Any] = {
            "min_java_version": None,
            "requires_modules": False,
            "main_class": None,
            "manifest_info": {},
            "class_analysis": {},
            "dependency_analysis": {}
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

            # Use comprehensive dependency analysis if available
            try:
                from jar2appimage.dependency_analyzer import quick_dependency_check
                dep_info = quick_dependency_check(jar_path)
                requirements["dependency_analysis"] = {
                    "dependency_count": dep_info.get("dependency_count", 0),
                    "has_conflicts": dep_info.get("has_conflicts", False),
                    "estimated_size_mb": dep_info.get("estimated_size_mb", 0),
                    "java_version": dep_info.get("java_version", "unknown"),
                    "warnings": dep_info.get("warnings", []),
                    "errors": dep_info.get("errors", [])
                }
                logger.debug(f"Enhanced JAR analysis with dependency info: {requirements['dependency_analysis']}")
            except ImportError:
                logger.debug("Comprehensive dependency analyzer not available, using basic analysis")
            except Exception as e:
                logger.warning(f"Dependency analysis failed: {e}")

        except Exception as e:
            logger.warning(f"Could not analyze JAR requirements: {e}")

        logger.info(f"JAR analysis complete: {requirements}")
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

    def check_java_download_needed(  # noqa: C901
        self,
        system_java: Optional[Dict[str, Any]],
        jar_requirements: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Determine if Java download is needed

        Args:
            system_java: System Java information or None
            jar_requirements: JAR requirements analysis

        Returns:
            Tuple of (download_needed, reason)
        """
        if not system_java:
            return True, "No system Java found"

        if not cast(bool, system_java.get("is_compatible", False)):
            return True, f"System Java {system_java.get('version', 'unknown')} is not compatible"

        # Check if JAR has specific requirements
        min_jar_version = jar_requirements.get("min_java_version")
        if min_jar_version:
            try:
                jar_major = int(str(min_jar_version).split('.')[0])
            except (TypeError, ValueError):
                jar_major = 0

            try:
                system_major = int(system_java.get("major_version", 0))
            except (TypeError, ValueError):
                system_major = 0

            if system_major < jar_major:
                return True, f"System Java {system_major} is below JAR requirement {jar_major}"

        # Check if bundled Java is preferred
        if jar_requirements.get("requires_modules"):
            # Modules require Java 9+, prefer bundled for compatibility
            return True, "JAR requires Java modules, bundled Java recommended"

        # Use enhanced dependency analysis if available
        dep_analysis = jar_requirements.get("dependency_analysis", {})
        if dep_analysis:
            # Check for dependency conflicts - prefer bundled Java for complex apps
            if dep_analysis.get("has_conflicts", False):
                return True, "Dependency conflicts detected, bundled Java recommended for stability"

            # Check for many dependencies - prefer bundled Java for isolation
            dep_count = dep_analysis.get("dependency_count", 0)
            if dep_count > 20:
                return True, f"Complex application ({dep_count} dependencies), bundled Java recommended"

            # Check for native libraries - prefer bundled Java for compatibility
            if dep_analysis.get("warnings"):
                warning_text = " ".join(dep_analysis["warnings"])
                if "native" in warning_text.lower():
                    return True, "Native libraries detected, bundled Java recommended for compatibility"

        return False, "System Java is sufficient"


class JavaDownloader:
    """Java download and API interaction component"""

    def __init__(self, config: Configuration):
        """
        Initialize Java downloader

        Args:
            config: Configuration instance
        """
        self.config = config
        self.download_cache = config.cache_dir / "downloads"
        self.download_cache.mkdir(exist_ok=True)

    def download_java(self, force: bool = False) -> Optional[str]:
        """
        Download the appropriate Java runtime

        Args:
            force: Force download even if cached version exists

        Returns:
            Path to downloaded Java archive or None if failed
        """
        logger.info(f"Downloading Java {self.config.java_version} {self.config.package_type.upper()}...")

        # Check cache first
        if not force:
            cached_file = self._get_cached_java()
            if cached_file:
                logger.info(f"Found cached Java {self.config.java_version}: {cached_file}")
                return str(cached_file)

        try:
            download_url = self._find_java_download_url()
            if not download_url:
                raise JavaDownloadError(f"Could not find download URL for Java {self.config.java_version}")

            # Download Java
            return self._download_from_url(download_url)

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def _find_java_download_url(self) -> Optional[str]:
        """Find the correct Java download URL for the specified version"""
        logger.info(f"Finding Java {self.config.java_version} download URL...")

        # Try GitHub API first
        try:
            return self._get_github_download_url()
        except Exception as e:
            logger.warning(f"GitHub API failed: {e}")

        # Fallback to hardcoded URLs
        return self._get_fallback_url()

    def _get_github_download_url(self) -> Optional[str]:
        """Get download URL from GitHub API"""
        repo = f"adoptium/temurin{self.config.java_version}-binaries"
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"

        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            }
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        # Find the right asset for Linux x64
        assets = data.get("assets", []) if isinstance(data, dict) else []
        for asset in assets:
            if not isinstance(asset, dict):
                continue

            name = asset.get("name", "")
            if (
                isinstance(name, str)
                and f"{self.config.package_type}_x64_linux" in name
                and name.endswith(".tar.gz")
                and "hotspot" in name
            ):
                download_url = asset.get("browser_download_url")
                if isinstance(download_url, str):
                    logger.info(f"Found {self.config.package_type.upper()}: {name}")
                    return download_url

        return None

    def _get_fallback_url(self) -> Optional[str]:
        """Fallback URLs for common Java versions"""
        fallbacks = {
            "8": {
                "jre": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jre_x64_linux_hotspot_8u412b08.tar.gz",
                "jdk": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u412b08.tar.gz",
            },
            "11": {
                "jre": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jre_x64_linux_hotspot_11.0.23_9.tar.gz",
                "jdk": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jdk_x64_linux_hotspot_11.0.23_9.tar.gz",
            },
            "17": {
                "jre": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jre_x64_linux_hotspot_17.0.12_7.tar.gz",
                "jdk": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz",
            },
            "21": {
                "jre": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jre_x64_linux_hotspot_21.0.4_7.tar.gz",
                "jdk": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_linux_hotspot_21.0.4_7.tar.gz",
            },
        }

        version_fallbacks = fallbacks.get(self.config.java_version, {})
        url = version_fallbacks.get(self.config.package_type)

        if url:
            logger.info(f"Using fallback URL for Java {self.config.java_version} {self.config.package_type}")
            return url

        logger.error(f"No download URL found for Java {self.config.java_version} {self.config.package_type}")
        return None

    def _download_from_url(self, download_url: str) -> str:
        """Download Java from URL"""
        # Extract filename from URL
        filename = download_url.split("/")[-1]
        java_path = self.download_cache / filename

        logger.info(f"Downloading: {filename}")
        logger.info(f"  URL: {download_url}")

        # Use curl for reliable downloads
        subprocess.run(
            ["curl", "-L", "--progress-bar", "-o", str(java_path), download_url],
            check=True,
            capture_output=True,
            text=True,
        )

        if java_path.exists():
            size_mb = java_path.stat().st_size // (1024 * 1024)
            logger.info(f"Java {self.config.java_version} downloaded: {filename} ({size_mb} MB)")
            return str(java_path)
        else:
            raise JavaDownloadError("Download completed but file not found")

    def _get_cached_java(self) -> Optional[Path]:
        """Check for cached Java download"""
        cache_pattern = f"*{self.config.java_version}*.tar.gz"
        for cached_file in self.download_cache.glob(cache_pattern):
            if cached_file.exists() and cached_file.stat().st_size > 50 * 1024 * 1024:  # At least 50MB
                return cached_file
        return None

    def clear_cache(self) -> bool:
        """
        Clear Java download cache

        Returns:
            True if cache was cleared
        """
        try:
            if self.download_cache.exists():
                shutil.rmtree(self.download_cache)
                self.download_cache.mkdir(exist_ok=True)
                logger.info("Java download cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

        return False


class JavaExtractor:
    """Java archive extraction component"""

    def __init__(self, config: Configuration):
        """
        Initialize Java extractor

        Args:
            config: Configuration instance
        """
        self.config = config

    def extract_java(self, java_archive: str, extract_dir: str) -> Optional[str]:
        """
        Extract Java archive to directory

        Args:
            java_archive: Path to Java archive
            extract_dir: Directory to extract to

        Returns:
            Path to extracted Java directory or None if failed
        """
        logger.info(f"Extracting Java runtime from {java_archive}")

        try:
            extract_path = Path(extract_dir)
            extract_path.mkdir(parents=True, exist_ok=True)

            with tarfile.open(java_archive, 'r:gz') as tar:
                # Extract to temp directory first
                temp_extract = extract_path / "temp_java"
                temp_extract.mkdir(exist_ok=True)

                tar.extractall(temp_extract)

                # Fix permissions after extraction
                for root, dirs, files in os.walk(temp_extract):
                    os.chmod(root, 0o755)
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)

            # Find the actual Java directory
            java_dir = None
            for item in temp_extract.iterdir():
                if item.is_dir() and (
                    item.name.startswith("jdk-") or item.name.startswith("jre-")
                ):
                    java_dir = item
                    break

            if not java_dir:
                raise JavaExtractionError("Could not find Java directory in archive")

            # Move to final location
            final_java_dir = extract_path / java_dir.name
            if final_java_dir.exists():
                shutil.rmtree(final_java_dir)

            java_dir.rename(final_java_dir)
            shutil.rmtree(temp_extract, ignore_errors=True)

            logger.info(f"Java extracted to: {final_java_dir}")
            return str(final_java_dir)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None


class BundlingStrategy(Protocol):
    """Protocol for different bundling strategies"""

    def bundle(
        self,
        java_dir: str,
        jar_path: str,
        app_name: str,
        output_dir: str
    ) -> str:
        """
        Bundle Java application with Java runtime

        Args:
            java_dir: Directory containing extracted Java
            jar_path: Path to application JAR
            app_name: Application name
            output_dir: Output directory

        Returns:
            Path to bundled application or None if failed
        """
        ...


class AppImageBundlingStrategy:
    """AppImage-specific bundling strategy"""

    def __init__(self, config: Configuration):
        """
        Initialize AppImage bundling strategy

        Args:
            config: Configuration instance
        """
        self.config = config

    def bundle(
        self,
        java_dir: str,
        jar_path: str,
        app_name: str,
        output_dir: str
    ) -> str:
        """
        Bundle Java into AppImage structure

        Args:
            java_dir: Directory containing extracted Java
            jar_path: Path to application JAR
            app_name: Application name
            output_dir: Output directory

        Returns:
            Path to bundled application directory
        """
        java_dir_path = Path(java_dir)
        appimage_java_dir = Path(output_dir) / "usr" / "java"

        appimage_java_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Bundling Java into AppImage structure: {appimage_java_dir}")

        try:
            # Copy Java files
            for item in java_dir_path.iterdir():
                src = java_dir_path / item.name
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
                logger.info(f"Java bundled successfully: {java_binary}")
                return str(appimage_java_dir.parent)
            else:
                raise JavaBundlingError(f"Java binary not found: {java_binary}")

        except Exception as e:
            raise JavaBundlingError(f"Failed to bundle Java for AppImage: {e}") from e


class TarballBundlingStrategy:
    """Tarball bundling strategy"""

    def __init__(self, config: Configuration):
        """
        Initialize tarball bundling strategy

        Args:
            config: Configuration instance
        """
        self.config = config

    def bundle(
        self,
        java_dir: str,
        jar_path: str,
        app_name: str,
        output_dir: str
    ) -> str:
        """
        Create tarball bundle with Java and application

        Args:
            java_dir: Directory containing extracted Java
            jar_path: Path to application JAR
            app_name: Application name
            output_dir: Output directory

        Returns:
            Path to bundled tarball
        """
        app_name_clean = app_name.replace(" ", "-").lower()

        logger.info(f"Creating tarball bundle for {app_name_clean}")

        # Create temporary directory for bundling
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / f"{app_name_clean}-bundled"
            bundle_dir.mkdir(exist_ok=True)

            # Copy JAR
            app_jar = bundle_dir / f"{app_name_clean}.jar"
            shutil.copy2(jar_path, app_jar)

            # Copy Java
            java_dest = bundle_dir / "java"
            shutil.copytree(java_dir, java_dest)

            # Create start script
            start_script = self._create_start_script(app_name_clean, java_dir)
            start_script_path = bundle_dir / "start.sh"
            start_script_path.write_text(start_script)
            start_script_path.chmod(0o755)

            # Create tarball
            bundle_filename = f"{app_name_clean}-bundled.tar.gz"
            bundle_path = Path(output_dir) / bundle_filename

            with tarfile.open(bundle_path, "w:gz") as tar:
                for root, _dirs, files in os.walk(bundle_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(bundle_dir)
                        tar.add(file_path, arcname=arcname)

            bundle_size = bundle_path.stat().st_size
            logger.info(f"Created bundled application: {bundle_filename} ({bundle_size // 1024 // 1024} MB)")

            return str(bundle_path)

    def _create_start_script(self, app_name: str, java_dir: str) -> str:
        """Create startup script for bundled application"""
        return f"""#!/bin/bash
# {app_name} Application with Bundled Java
set -e

echo "Starting {app_name} with bundled Java..."
export JAVA_HOME="{java_dir}"
export PATH="{java_dir}/bin:$PATH"

exec "$JAVA_HOME/bin/java" -jar "$(dirname "$0")/{app_name}.jar" "$@"
"""


class JavaBundler:
    """
    Unified Java Bundler - Main orchestrator class

    This class consolidates all Java bundling functionality into a single,
    well-designed interface that combines the best features from multiple
    implementations while maintaining clean architecture.
    """

    def __init__(self, config: Optional[Configuration] = None):
        """
        Initialize Java bundler

        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or Configuration()

        # Initialize components
        self.detector = JavaDetector(self.config)
        self.downloader = JavaDownloader(self.config)
        self.extractor = JavaExtractor(self.config)

        # Initialize bundling strategies
        self._bundling_strategies: Dict[str, BundlingStrategy] = {
            "appimage": AppImageBundlingStrategy(self.config),
            "tarball": TarballBundlingStrategy(self.config)
        }

        logger.info("JavaBundler initialized")

    def detect_and_prepare_java(
        self,
        jar_path: str,
        force_download: bool = False
    ) -> Tuple[Optional[str], bool]:
        """
        Detect system Java and prepare Java runtime for bundling

        Args:
            jar_path: Path to JAR file for requirements analysis
            force_download: Force download even if system Java is available

        Returns:
            Tuple of (java_dir_path, download_performed)
        """
        logger.info("Starting Java detection and preparation...")

        # Detect system Java
        system_java = self.detector.detect_system_java()

        # Analyze JAR requirements
        jar_requirements = self.detector.analyze_jar_requirements(jar_path)

        # Determine if download is needed
        download_needed, reason = self.detector.check_java_download_needed(
            system_java, jar_requirements
        )

        if download_needed and not force_download:
            if self.config.interactive_mode:
                # In interactive mode, ask user for consent
                if not self._ask_user_consent(download_needed, reason):
                    logger.info("User declined Java download, using system Java if available")
                    java_home_value = system_java["java_home"] if system_java else None
                    java_home = java_home_value if isinstance(java_home_value, str) else None
                    return java_home, False
            else:
                logger.info(f"Java download needed: {reason}")

        if download_needed or force_download:
            # Download Java
            java_archive = self.downloader.download_java(force=force_download)
            if not java_archive:
                raise JavaDownloadError("Failed to download Java")

            # Ensure java_archive is a concrete string for extractor
            java_archive_str: str = java_archive  # type: ignore[assignment]

            # Extract Java
            extract_dir = self.config.cache_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)

            java_dir: Optional[str] = self.extractor.extract_java(java_archive_str, str(extract_dir))
            if not java_dir:
                raise JavaExtractionError("Failed to extract Java")

            result_java_dir: Tuple[Optional[str], bool] = (java_dir, True)
            return result_java_dir

        # Use system Java
        if system_java and system_java.get("java_home"):
            java_home = cast(Optional[str], system_java.get("java_home"))
            result_java_home: Tuple[Optional[str], bool] = (java_home, False)
            return result_java_home

        raise JavaDetectionError("No suitable Java found")

    def bundle_application(
        self,
        jar_path: str,
        app_name: str,
        output_dir: str = ".",
        strategy: Optional[str] = None
    ) -> str:
        """
        Bundle Java application with Java runtime

        Args:
            jar_path: Path to application JAR
            app_name: Application name
            output_dir: Output directory
            strategy: Bundling strategy ('appimage', 'tarball')

        Returns:
            Path to bundled application
        """
        logger.info(f"Bundling {app_name} with Java...")

        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"JAR file not found: {jar_path}")

        # Use specified strategy or default
        bundling_strategy = strategy or self.config.bundling_strategy
        if bundling_strategy not in self._bundling_strategies:
            raise ValueError(f"Unknown bundling strategy: {bundling_strategy}")

        # Prepare Java
        java_dir, _ = self.detect_and_prepare_java(jar_path)
        if not java_dir:
            raise JavaBundlingError("Failed to prepare Java runtime")

        # Perform bundling
        bundler = self._bundling_strategies[bundling_strategy]
        return bundler.bundle(java_dir, jar_path, app_name, output_dir)

    def _ask_user_consent(self, download_needed: bool, reason: str) -> bool:
        """
        Ask user for consent to download Java

        Args:
            download_needed: Whether download is needed
            reason: Reason for download

        Returns:
            True if user consents
        """
        if not download_needed:
            return True

        print("\n" + "="*60)
        print("🚀 JAVA RUNTIME DOWNLOAD OFFER")
        print("="*60)
        print("\n📋 Analysis Results:")
        print(f"   • Recommendation: Download Java {self.config.java_version}")
        print(f"   • Reason: {reason}")

        print("\n📦 Download Information:")
        print(f"   • Version: Java {self.config.java_version} (LTS)")
        print(f"   • Type: {self.config.package_type.upper()}")
        print(f"   • Architecture: {self.config.target_arch}")

        print("\n💡 Benefits:")
        print("   • Self-contained application (no external dependencies)")
        print("   • Works on any Linux distribution")
        print("   • Latest security updates")

        # Ask for consent
        while True:
            print(f"\n❓ Do you want to download Java {self.config.java_version}?")
            response = input("   [Y]es / [N]o: ").strip().lower()

            if response in ['y', 'yes']:
                print(f"\n✅ Downloading Java {self.config.java_version}...")
                return True
            elif response in ['n', 'no']:
                print("\n❌ Download cancelled.")
                return False
            else:
                print("   Please enter Y or N")

    def get_java_info(self) -> Dict[str, Any]:
        """
        Get comprehensive Java information

        Returns:
            Dict with Java detection and system information
        """
        return {
            "system_java": self.detector.detect_system_java(),
            "config": {
                "java_version": self.config.java_version,
                "use_jre": self.config.use_jre,
                "bundling_strategy": self.config.bundling_strategy,
                "target_arch": self.config.target_arch,
                "is_lts": self.config.is_lts_version
            },
            "cache_info": self._get_cache_info(),
            "platform": self.detector._platform_info
        }

    def _get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        cache_info: Dict[str, Any] = {
            "cache_dir": str(self.config.cache_dir),
            "downloads_dir": str(self.downloader.download_cache),
            "total_files": 0,
            "total_size_mb": 0,
            "java_versions": []
        }

        if self.config.cache_dir.exists():
            try:
                for file_path in self.config.cache_dir.rglob("*.tar.gz"):
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

    def clear_cache(self) -> bool:
        """
        Clear Java download and extraction cache

        Returns:
            True if cache was cleared
        """
        return self.downloader.clear_cache()


# Convenience functions for easy integration
def create_java_bundler(
    java_version: str = "17",
    use_jre: bool = True,
    interactive_mode: bool = True,
    bundling_strategy: str = "appimage"
) -> JavaBundler:
    """
    Create a JavaBundler instance with specified configuration

    Args:
        java_version: Java version to use
        use_jre: Use JRE vs JDK
        interactive_mode: Enable user interaction
        bundling_strategy: Bundling approach

    Returns:
        Configured JavaBundler instance
    """
    config = Configuration(
        java_version=java_version,
        use_jre=use_jre,
        interactive_mode=interactive_mode,
        bundling_strategy=bundling_strategy
    )
    return JavaBundler(config)


def quick_bundle(
    jar_path: str,
    app_name: str,
    output_dir: str = ".",
    java_version: str = "17"
) -> str:
    """
    Quick bundling function for common use cases

    Args:
        jar_path: Path to JAR file
        app_name: Application name
        output_dir: Output directory
        java_version: Java version to use

    Returns:
        Path to bundled application
    """
    bundler = create_java_bundler(
        java_version=java_version,
        use_jre=True,
        interactive_mode=False,
        bundling_strategy="tarball"
    )

    return bundler.bundle_application(jar_path, app_name, output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified Java Bundler for jar2appimage")
    parser.add_argument("jar_path", help="JAR file to bundle")
    parser.add_argument("app_name", help="Application name")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--java-version", default="17", help="Java version to use")
    parser.add_argument("--jdk", action="store_true", help="Use JDK instead of JRE")
    parser.add_argument("--strategy", choices=["appimage", "tarball"], default="appimage",
                       help="Bundling strategy")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    parser.add_argument("--info", action="store_true", help="Show Java information")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    if args.info:
        bundler = create_java_bundler(
            java_version=args.java_version,
            use_jre=not args.jdk,
            interactive_mode=not args.non_interactive
        )

        info = bundler.get_java_info()
        print("Java Bundler Information:")
        print(f"  System Java: {'Found' if info['system_java'] else 'Not found'}")
        print(f"  Configured Version: {info['config']['java_version']}")
        print(f"  Package Type: {'JRE' if info['config']['use_jre'] else 'JDK'}")
        print(f"  Target Architecture: {info['config']['target_arch']}")
        print(f"  Cache: {info['cache_info']['total_files']} files, "
              f"{info['cache_info']['total_size_mb']} MB")
    else:
        try:
            bundler = create_java_bundler(
                java_version=args.java_version,
                use_jre=not args.jdk,
                interactive_mode=not args.non_interactive,
                bundling_strategy=args.strategy
            )

            result = bundler.bundle_application(args.jar_path, args.app_name, args.output)
            print(f"✅ Bundling complete: {result}")

        except Exception as e:
            logger.error(f"Bundling failed: {e}")
            exit(1)
