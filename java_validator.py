#!/usr/bin/env python3
"""
Java Validator Module

This module handles Java version validation and compatibility checking.
Manages system Java detection, version parsing, and JAR requirements analysis.

Key Responsibilities:
- System Java detection and version parsing
- Java compatibility validation
- JAR file requirements analysis
- Platform and architecture validation
"""

import logging
import os
import platform
import re
import subprocess
import zipfile
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class JavaValidationError(Exception):
    """Exception raised when Java validation fails"""
    pass


class JavaCompatibilityError(Exception):
    """Exception raised when Java version is incompatible"""
    pass


class JavaValidator:
    """
    Handles Java validation, detection, and compatibility checking
    """

    # LTS Java versions (as of 2025-12-16)
    LTS_VERSIONS = ["8", "11", "17", "21"]

    # Architecture mapping
    ARCH_MAPPING = {
        "x86_64": "x64",
        "amd64": "x64",
        "aarch64": "aarch64",
        "arm64": "aarch64"
    }

    # Minimum and maximum Java version compatibility
    MIN_JAVA_VERSION = 8
    MAX_JAVA_VERSION = 21

    def __init__(self):
        """Initialize the Java validator"""
        logger.info("Initialized JavaValidator")

    def detect_system_java(self) -> Optional[Dict[str, Union[str, int, bool]]]:
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

            java_info = {
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

    def _check_java_compatibility(self, version_info: Dict) -> bool:
        """
        Check if Java version is compatible with jar2appimage

        Args:
            version_info: Java version information dictionary

        Returns:
            True if compatible, False otherwise
        """
        major_version = version_info["major"]
        return self.MIN_JAVA_VERSION <= major_version <= self.MAX_JAVA_VERSION

    def analyze_jar_requirements(self, jar_path: str) -> Dict[str, Any]:
        """
        Analyze JAR file for Java version requirements

        Args:
            jar_path: Path to JAR file

        Returns:
            Dict with Java requirement information
        """
        logger.info(f"📋 Analyzing JAR requirements: {jar_path}")

        requirements = {
            "min_java_version": None,
            "requires_modules": False,
            "main_class": None,
            "manifest_info": {},
            "class_analysis": {}
        }

        try:
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
        """
        Parse manifest for Java version requirements

        Args:
            manifest_content: Manifest file content

        Returns:
            Dictionary with parsed requirements
        """
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

    def check_java_download_needed(
        self,
        system_java: Optional[Dict],
        jar_requirements: Dict
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

    def detect_platform(self) -> Dict[str, str]:
        """
        Detect current platform and architecture

        Returns:
            Dictionary with platform information
        """
        system = platform.system()
        machine = platform.machine()

        return {
            "system": system,
            "arch": self._map_architecture(machine),
            "machine": machine,
            "is_linux": system == "Linux",
            "is_macos": system == "Darwin",
            "is_windows": system == "Windows",
            "supports_appimage": system == "Linux"
        }

    def _map_architecture(self, machine: str) -> str:
        """
        Map machine architecture to standardized format

        Args:
            machine: Raw machine architecture string

        Returns:
            Mapped architecture string
        """
        return self.ARCH_MAPPING.get(machine, machine)

    def validate_java_installation(self, java_info: Dict[str, Any]) -> bool:
        """
        Validate a Java installation

        Args:
            java_info: Java information dictionary

        Returns:
            True if validation passes
        """
        try:
            # Check if command exists and is executable
            java_cmd = java_info.get("command")
            if not java_cmd or not os.path.exists(java_cmd):
                return False

            # Check if Java version can be retrieved
            result = subprocess.run(
                [java_cmd, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return False

            # Check basic Java functionality
            result = subprocess.run(
                [java_cmd, "-XshowSettings:properties", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Java installation validation failed: {e}")
            return False
