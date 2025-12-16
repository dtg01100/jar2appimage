#!/usr/bin/env python3
"""
jar2appimage CLI Utilities
Common utilities and helpers for the unified CLI system
"""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


def detect_platform() -> Dict[str, Any]:
    """
    Detect current platform and capabilities

    Returns:
        Dictionary with platform information and capabilities
    """
    system = platform.system()
    machine = platform.machine()

    return {
        "system": system,
        "machine": machine,
        "is_linux": system == "Linux",
        "is_macos": system == "Darwin",
        "is_windows": system == "Windows",
        "supports_appimage": system == "Linux",
        "supports_native_bundle": system in ["Darwin", "Windows"],
    }


def check_jar2appimage_support() -> bool:
    """
    Check if jar2appimage supports current platform

    Returns:
        True if platform is supported, False otherwise
    """
    platform_info = detect_platform()

    if not platform_info["supports_appimage"]:
        print(f"❌ {platform_info['system']} is not supported by jar2appimage")
        print(f"   Platform: {platform_info['system']} {platform_info['machine']}")
        print()
        print("⚠️  jar2appimage creates Linux AppImages only")
        print()
        print(f"   For {platform_info['system']}, use: java -jar your-application.jar")
        print()
        print("   Alternative: Use platform-specific packaging:")
        print()

        if platform_info["is_macos"]:
            print("     • macOS: Create .app bundles")
            print("     • macOS: Use Homebrew cask or native installers")
        elif platform_info["is_windows"]:
            print("     • Windows: Use .exe installers or batch scripts")
            print("     • Windows: Use MSI packages for enterprise deployment")

        logger.warning(f"Platform {platform_info['system']} not supported for AppImage creation")
        return False

    print(f"✅ {platform_info['system']} supports jar2appimage AppImage creation")
    logger.info(f"Platform {platform_info['system']} supports AppImage creation")
    return True


def validate_jar_file(jar_path: str) -> bool:
    """
    Validate that the JAR file exists and is readable

    Args:
        jar_path: Path to the JAR file

    Returns:
        True if valid, False otherwise
    """
    if not jar_path:
        print("❌ JAR file path is required")
        return False

    path = Path(jar_path)
    if not path.exists():
        print(f"❌ JAR file not found: {jar_path}")
        return False

    if not path.is_file():
        print(f"❌ Path is not a file: {jar_path}")
        return False

    if not path.suffix.lower() == '.jar':
        print(f"⚠️  File does not have .jar extension: {jar_path}")
        logger.warning(f"JAR file does not have .jar extension: {jar_path}")

    logger.info(f"JAR file validated: {jar_path}")
    return True


def validate_output_directory(output_dir: str) -> bool:
    """
    Validate and create output directory if needed

    Args:
        output_dir: Output directory path

    Returns:
        True if valid, False otherwise
    """
    if not output_dir:
        output_dir = "."

    try:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory validated: {output_dir}")
        return True
    except Exception as e:
        print(f"❌ Cannot create output directory: {output_dir}")
        print(f"   Error: {e}")
        logger.error(f"Cannot create output directory {output_dir}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def check_java_availability() -> Dict[str, Any]:
    """
    Check Java availability and version

    Returns:
        Dictionary with Java information
    """
    java_info: Dict[str, Any] = {
        "available": False,
        "version": None,
        "command": None,
        "java_home": None,
        "type": None
    }

    try:
        # Try to get Java version
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            java_info["available"] = True
            java_info["command"] = "java"

            # Parse version from stderr
            version_output = result.stderr
            if "version" in version_output:
                # Extract version string
                import re
                version_match = re.search(r'"([^"]+)"', version_output)
                if version_match:
                    java_info["version"] = version_match.group(1)

            # Check JAVA_HOME
            java_home = os.environ.get("JAVA_HOME")
            if java_home:
                java_info["java_home"] = java_home
                if Path(java_home).exists():
                    java_info["type"] = "JDK"
                else:
                    java_info["type"] = "JRE"
            else:
                java_info["type"] = "System"

            logger.info(f"Java available: {java_info['version']} ({java_info['type']})")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"Java availability check failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error checking Java availability: {e}")

    return java_info


def get_appimage_info(appimage_path: str) -> Dict[str, Any]:
    """
    Get information about a created AppImage

    Args:
        appimage_path: Path to the AppImage

    Returns:
        Dictionary with AppImage information
    """
    if not Path(appimage_path).exists():
        return {}

    try:
        stat = Path(appimage_path).stat()
        size = format_file_size(stat.st_size)

        return {
            "path": appimage_path,
            "size": size,
            "size_bytes": stat.st_size,
            "executable": os.access(appimage_path, os.X_OK),
            "exists": True
        }
    except Exception as e:
        logger.error(f"Error getting AppImage info: {e}")
        return {"path": appimage_path, "exists": False, "error": str(e)}


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration

    Args:
        verbose: Enable verbose logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.warning(f"Cannot setup log file {log_file}: {e}")


def check_required_tools() -> Dict[str, bool]:
    """
    Check availability of required tools

    Returns:
        Dictionary mapping tool names to availability
    """
    tools = {
        "java": False,
        "javac": False,
        "file": False,
        "strip": False
    }

    for tool in tools:
        try:
            result = subprocess.run(
                ["which", tool],
                capture_output=True,
                timeout=5
            )
            tools[tool] = result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            tools[tool] = False

    logger.info(f"Required tools check: {tools}")
    return tools


def handle_error(error: Exception, context: str = "") -> int:
    """
    Handle errors consistently

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred

    Returns:
        Exit code (1 for error)
    """
    error_msg = str(error)
    if context:
        error_msg = f"{context}: {error_msg}"

    print(f"❌ {error_msg}")
    logger.error(error_msg, exc_info=True)

    return 1
