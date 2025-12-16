#!/usr/bin/env python3
# mypy: ignore-errors
"""
jar2appimage: Enhanced Java Application Packaging - Refactored Core Module

This module provides a clean, maintainable implementation of the core AppImage creation
functionality with proper separation of concerns, comprehensive error handling, and
logging integration.

Key improvements:
- Single Responsibility Principle compliance
- Comprehensive error handling with custom exceptions
- Professional logging instead of print statements
- Dependency injection support for testing
- Clean separation of concerns
- Type hints and documentation

Author: jar2appimage Development Team
Version: 2.0.0
"""

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

# Configure module-level logger
logger = logging.getLogger(__name__)


# Custom Exception Classes
class Jar2AppImageError(Exception):
    """Base exception for jar2appimage operations"""
    pass


class ValidationError(Jar2AppImageError):
    """Raised when input validation fails"""
    pass


class MainClassDetectionError(Jar2AppImageError):
    """Raised when main class detection fails"""
    pass


class DirectoryCreationError(Jar2AppImageError):
    """Raised when directory structure creation fails"""
    pass


class JavaBundlingError(Jar2AppImageError):
    """Raised when Java bundling fails"""
    pass


class AppImageCreationError(Jar2AppImageError):
    """Raised when AppImage creation fails"""
    pass


class DesktopFileCreationError(Jar2AppImageError):
    """Raised when desktop file creation fails"""
    pass


class AppRunInstallationError(Jar2AppImageError):
    """Raised when AppRun installation fails"""
    pass


# Protocol for dependency injection
class JavaBundlerProtocol(Protocol):
    """Protocol for Java bundler dependency injection"""

    def bundle_application(
        self,
        jar_path: str,
        app_name: str,
        output_dir: str,
        strategy: Optional[str] = None
    ) -> str:
        """Bundle Java application with Java runtime"""
        ...


class Jar2AppImage:
    """
    Enhanced AppImage creator with Java dependency management and optional bundling.

    This class provides a clean, maintainable interface for creating AppImages from
    JAR files with optional Java bundling. The implementation follows the Single
    Responsibility Principle with proper separation of concerns.

    Attributes:
        jar_file: Path to the JAR file to package
        jar_path: Path object for the JAR file
        output_dir: Output directory for the AppImage
        bundled: Whether to bundle Java runtime
        jdk_version: Java version to use for bundling
        java_bundler: Configurable Java bundler for dependency injection
    """

    def __init__(
        self,
        jar_file: str,
        output_dir: str = ".",
        bundled: bool = False,
        jdk_version: str = "11",
        java_bundler: Optional[JavaBundlerProtocol] = None
    ):
        """
        Initialize the AppImage creator.

        Args:
            jar_file: Path to the JAR file to package
            output_dir: Output directory for the AppImage
            bundled: Whether to bundle Java runtime
            jdk_version: Java version to use for bundling
            java_bundler: Optional Java bundler for dependency injection
        """
        self.jar_file = jar_file
        self.jar_path = Path(jar_file)
        self.output_dir = Path(output_dir)
        self.bundled = bundled
        self.jdk_version = jdk_version
        self.java_bundler = java_bundler

        # Initialize application metadata
        self._app_name = self.jar_path.stem
        self._main_class = ""

        # Create temporary directory in build folder
        build_root = Path(os.getcwd()) / "jar2appimage_build"
        build_root.mkdir(exist_ok=True)
        self.temp_dir = build_root / f"{self._app_name}-{uuid.uuid4().hex[:8]}"
        self.temp_dir.mkdir(exist_ok=True)

        logger.info(f"Initialized Jar2AppImage for: {self._app_name}")
        logger.debug(f"Temporary directory: {self.temp_dir}")

        # Initialize enhanced capabilities tracking
        self._enhanced_features = {
            'java_bundler': False,
            'smart_gui_detection': True,
            'platform_specific_opts': True,
            'professional_desktop_integration': True,
            'comprehensive_error_handling': True,
            'java_dependency_management': True,
            'appimage_creation': True
        }

        # Initialize runtime manager with graceful fallback
        try:
            from jar2appimage.runtime import JavaRuntimeManager
            self.runtime_manager = JavaRuntimeManager()
            logger.debug("JavaRuntimeManager initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import runtime module: {e}")
            self.runtime_manager = None

        # Initialize dependency analyzer with graceful fallback
        try:
            from jar2appimage.analyzer import JarDependencyAnalyzer
            self.dependency_analyzer = JarDependencyAnalyzer(str(self.jar_file))
            logger.debug("JarDependencyAnalyzer initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import analyzer module: {e}")
            self.dependency_analyzer = None

    def create(self) -> str:
        """
        Create enhanced AppImage with optional Java bundling.

        This method orchestrates the entire AppImage creation process by delegating
        to focused sub-methods, each handling a specific responsibility. This approach
        significantly reduces complexity while maintaining all functionality.

        Returns:
            Path to the created AppImage file

        Raises:
            ValidationError: If input validation fails
            MainClassDetectionError: If main class cannot be detected
            DirectoryCreationError: If directory structure creation fails
            JavaBundlingError: If Java bundling fails
            AppImageCreationError: If AppImage creation fails
        """
        logger.info(f"Starting AppImage creation for {self._app_name}")

        try:
            # Step 1: Validate input and extract application metadata
            self._validate_input()
            self._detect_main_class()

            # Step 2: Create directory structure
            app_dir = self._create_directory_structure()

            # Step 3: Copy JAR file and store main class
            self._copy_jar_and_main_class(app_dir)

            # Step 4: Handle Java bundling if requested
            if self.bundled:
                self._handle_java_bundling(app_dir)

            # Step 5: Create desktop file and AppRun script
            self._create_desktop_file(app_dir)
            self._install_apprun(app_dir)

            # Step 6: Create final AppImage
            appimage_path = self._create_appimage(app_dir)

            logger.info(f"AppImage creation completed successfully: {appimage_path}")
            return appimage_path

        except Exception as e:
            logger.error(f"AppImage creation failed: {e}")
            raise

    def _validate_input(self) -> None:
        """
        Validate input parameters and JAR file existence.

        Raises:
            ValidationError: If input validation fails
        """
        logger.debug("Validating input parameters")

        # Validate JAR file existence
        if not os.path.exists(self.jar_file):
            raise ValidationError(f"JAR file not found: {self.jar_file}")

        # Validate JAR file is readable
        if not os.access(self.jar_file, os.R_OK):
            raise ValidationError(f"JAR file is not readable: {self.jar_file}")

        # Validate output directory is accessible
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            if not os.access(self.output_dir, os.W_OK):
                raise ValidationError(f"Output directory is not writable: {self.output_dir}")
        except Exception as e:
            raise ValidationError(f"Cannot access output directory: {e}") from e

        logger.debug("Input validation completed successfully")

    def _detect_main_class(self) -> str:
        """
        Detect main class from JAR manifest and fallback strategies.

        Returns:
            Detected main class name

        Raises:
            MainClassDetectionError: If main class cannot be detected
        """
        logger.debug("Detecting main class from JAR")

        main_class = self._detect_main_class_from_manifest()

        if not main_class:
            main_class = self._detect_main_class_from_patterns()

        if not main_class:
            raise MainClassDetectionError("Could not detect main class from JAR manifest or patterns")

        self._main_class = main_class
        logger.info(f"Detected main class: {main_class}")
        return main_class

    def _detect_main_class_from_manifest(self) -> Optional[str]:
        """
        Extract main class from JAR manifest file.

        Returns:
            Main class name from manifest or None if not found
        """
        try:
            import zipfile
            with zipfile.ZipFile(self.jar_file, 'r') as jar:
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_data = jar.read('META-INF/MANIFEST.MF').decode('utf-8')
                    for line in manifest_data.split('\n'):
                        if line.startswith('Main-Class:'):
                            main_class = line.split(':', 1)[1].strip()
                            logger.debug(f"Found main class in manifest: {main_class}")
                            return main_class
        except Exception as e:
            logger.debug(f"Manifest parsing failed: {e}")

        return None

    def _detect_main_class_from_patterns(self) -> Optional[str]:
        """
        Fallback main class detection using pattern matching.

        Returns:
            Main class name from patterns or None if not found
        """
        try:
            result = subprocess.run(
                ['jar', 'tf', self.jar_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                classes = result.stdout.split('\n')
                common_main_classes = ['Main', 'App', 'Application', 'Launcher']

                for class_line in classes:
                    class_line = class_line.strip()
                    if class_line.endswith('.class'):
                        class_name = class_line.replace('.class', '').replace('/', '.')
                        if class_name in common_main_classes:
                            logger.debug(f"Found main class from pattern: {class_name}")
                            return class_name
        except Exception as e:
            logger.debug(f"Pattern matching failed: {e}")

        return None

    def _create_directory_structure(self) -> str:
        """
        Create AppImage directory structure.

        Returns:
            Path to the created AppDir directory

        Raises:
            DirectoryCreationError: If directory creation fails
        """
        logger.debug("Creating AppImage directory structure")

        try:
            # Create main build directory
            appimage_dir = self.temp_dir / f"{self._app_name}_appimage"
            appimage_dir.mkdir(exist_ok=True)

            # Create AppDir structure
            app_dir = appimage_dir / f"{self._app_name}.AppDir"

            # Create standard AppImage directory structure
            dirs_to_create = [
                app_dir / "usr" / "bin",
                app_dir / "usr" / "lib",
                app_dir / "usr" / "share" / "applications"
            ]

            for dir_path in dirs_to_create:
                dir_path.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Created directory structure: {app_dir}")
            return str(app_dir)

        except Exception as e:
            raise DirectoryCreationError(f"Failed to create directory structure: {e}") from e

    def _copy_jar_and_main_class(self, app_dir: str) -> None:
        """
        Copy JAR file and store main class information.

        Args:
            app_dir: AppDir directory path

        Raises:
            ValidationError: If file operations fail
        """
        logger.debug("Copying JAR file and storing main class")

        try:
            # Copy JAR file
            dest_jar = os.path.join(app_dir, "usr", "bin", f"{self._app_name}.jar")
            shutil.copy2(self.jar_file, dest_jar)
            logger.debug(f"Copied JAR file to: {dest_jar}")

            # Store main class for AppRun script
            main_class_file = os.path.join(app_dir, ".main_class")
            with open(main_class_file, 'w') as f:
                f.write(self._main_class)
            logger.debug(f"Stored main class: {self._main_class}")

        except Exception as e:
            raise ValidationError(f"Failed to copy JAR file or store main class: {e}") from e

    def _handle_java_bundling(self, app_dir: str) -> None:
        """
        Handle Java bundling process using dependency injection.

        Args:
            app_dir: AppDir directory path

        Raises:
            JavaBundlingError: If Java bundling fails
        """
        logger.info("Starting Java bundling process")

        try:
            # Use injected bundler or create default one
            if self.java_bundler:
                bundler = self.java_bundler
                logger.debug("Using injected Java bundler")
            else:
                from jar2appimage.java_bundler_unified import create_java_bundler
                bundler = create_java_bundler(
                    java_version=self.jdk_version,
                    use_jre=True,
                    interactive_mode=False,
                    bundling_strategy="appimage"
                )
                logger.debug("Created default Java bundler")

            # Bundle Java into AppImage structure
            java_output_dir = os.path.join(app_dir, "usr")
            result_path = bundler.bundle_application(
                jar_path=self.jar_file,
                app_name=self._app_name,
                output_dir=java_output_dir,
                strategy="appimage"
            )

            if not result_path:
                raise JavaBundlingError("Java bundling returned empty result")

            # Update enhanced features
            self._enhanced_features['java_bundler'] = True

            logger.info("Java bundling completed successfully")

        except Exception as e:
            logger.warning(f"Java bundling failed, falling back to system Java: {e}")
            # Don't raise exception - allow fallback to system Java

    def _create_desktop_file(self, app_dir: str) -> None:
        """
        Create desktop entry file for the application.

        Args:
            app_dir: AppDir directory path

        Raises:
            DesktopFileCreationError: If desktop file creation fails
        """
        logger.debug("Creating desktop file")

        try:
            # Determine if application needs terminal
            needs_terminal = self._needs_terminal()

            # Create desktop file content
            import textwrap
            desktop_content = textwrap.dedent(f"""\
                [Desktop Entry]
                Type=Application
                Name={self._app_name}
                Comment=Java application packaged as AppImage
                Exec=AppRun
                Icon={self._app_name}
                Categories=Development;Utility
                Terminal={"true" if needs_terminal else "false"}
                StartupNotify=true
                StartupWMClass=java
                Keywords=java;jar;{self._app_name}
            """)

            # Write desktop file to root of AppDir
            desktop_path = os.path.join(app_dir, f"{self._app_name}.desktop")
            with open(desktop_path, 'w') as f:
                f.write(desktop_content)

            # Copy to standard applications directory
            desktop_install_dir = os.path.join(app_dir, "usr", "share", "applications")
            desktop_install_path = os.path.join(desktop_install_dir, f"{self._app_name}.desktop")
            shutil.copy2(desktop_path, desktop_install_path)

            # Create placeholder icon if needed
            self._create_placeholder_icon(app_dir)

            logger.debug(f"Created desktop file: {desktop_install_path}")

        except Exception as e:
            raise DesktopFileCreationError(f"Failed to create desktop file: {e}") from e

    def _install_apprun(self, app_dir: str) -> None:
        """
        Install AppRun script for the application.

        Args:
            app_dir: AppDir directory path

        Raises:
            AppRunInstallationError: If AppRun installation fails
        """
        logger.debug("Installing AppRun script")

        try:
            apprun_path = os.path.join(app_dir, "AppRun")

            # Choose AppRun content based on bundling status
            if self.bundled and self._enhanced_features.get('java_bundler'):
                apprun_content = self._create_bundled_apprun_content()
            else:
                apprun_content = self._create_standard_apprun_content()

            # Write AppRun script
            with open(apprun_path, 'w') as f:
                f.write(apprun_content)

            # Make executable
            os.chmod(apprun_path, 0o755)

            logger.debug(f"Installed AppRun script: {apprun_path}")

        except Exception as e:
            raise AppRunInstallationError(f"Failed to install AppRun script: {e}") from e

    def _create_standard_apprun_content(self) -> str:
        """
        Create standard AppRun content for non-bundled Java.

        Returns:
            AppRun script content
        """
        return f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
JAR_FILE="${{HERE}}/usr/bin/{self._app_name}.jar"
if [ ! -f "$JAR_FILE" ]; then
  echo "Error: JAR file not found: $JAR_FILE"
  exit 1
fi
exec java -jar "$JAR_FILE" "$@"
"""

    def _create_bundled_apprun_content(self) -> str:
        """
        Create bundled AppRun content that uses bundled Java.

        Returns:
            AppRun script content with bundled Java support
        """
        return f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
JAR_FILE="${{HERE}}/usr/bin/{self._app_name}.jar"

if [ ! -f "$JAR_FILE" ]; then
  echo "Error: JAR file not found: $JAR_FILE"
  exit 1
fi

# Priority 1: Try bundled Java (if available)
BUNDLED_JAVA="${{HERE}}/usr/java/bin/java"
if [ -f "$BUNDLED_JAVA" ]; then
    export JAVA_HOME="${{HERE}}/usr/java"
    export PATH="${{HERE}}/usr/java/bin:$PATH"
    JAVA_CMD="$BUNDLED_JAVA"
    echo "Using bundled Java: $($JAVA_CMD -version 2>&1 | head -1)"
else
    # Priority 2: Fall back to system Java
    JAVA_CMD="java"
    if command -v "$JAVA_CMD" >/dev/null 2>&1; then
        echo "Using system Java: $($JAVA_CMD -version 2>&1 | head -1)"
    else
        echo "Error: No Java runtime found - neither bundled nor system Java available"
        exit 1
    fi
fi

# Execute with bundled JAR
exec "$JAVA_CMD" -jar "$JAR_FILE" "$@"
"""

    def _create_appimage(self, app_dir: str) -> str:
        """
        Create final AppImage from AppDir.

        Args:
            app_dir: AppDir directory path

        Returns:
            Path to created AppImage file

        Raises:
            AppImageCreationError: If AppImage creation fails
        """
        logger.info("Creating AppImage from AppDir")

        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)

            # Get appimagetool
            from jar2appimage.tools import ToolManager
            tool_manager = ToolManager()
            appimagetool_path = tool_manager.get_appimagetool()

            # Set up output path
            output_path = os.path.join(self.output_dir, f"{self._app_name}.AppImage")

            # Set up environment for appimagetool
            import platform as _platform
            arch_map = {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64"}
            arch = arch_map.get(_platform.machine(), _platform.machine())
            env = os.environ.copy()
            env["ARCH"] = arch

            # Run appimagetool
            cmd = [appimagetool_path, "--no-appstream", app_dir, output_path]
            logger.debug(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise AppImageCreationError(
                    f"appimagetool failed with exit code {result.returncode}. "
                    f"stderr: {result.stderr}"
                )

            if not os.path.exists(output_path):
                raise AppImageCreationError(f"AppImage was not created: {output_path}")

            # Log success
            appimage_size = os.path.getsize(output_path)
            logger.info(f"Created AppImage: {output_path} ({appimage_size // 1024 // 1024} MB)")

            return output_path

        except Exception as e:
            if isinstance(e, AppImageCreationError):
                raise
            raise AppImageCreationError(f"AppImage creation failed: {e}") from e

    def _needs_terminal(self) -> bool:
        """
        Determine if application needs terminal based on main class and name.

        Returns:
            True if application needs terminal, False otherwise
        """
        gui_indicators = [
            "gui", "swing", "awt", "desktop", "window", "app",
            "interface", "frame", "panel", "fx", "javafx"
        ]
        cli_indicators = [
            "cli", "command", "tool", "utility", "batch",
            "console", "shell", "main"
        ]

        main_class_lower = self._main_class.lower()
        app_name_lower = self._app_name.lower()

        # Check for GUI indicators (prefer GUI for these)
        for indicator in gui_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return False

        # Check for CLI indicators (prefer terminal for these)
        for indicator in cli_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return True

        # Default to GUI (no terminal)
        return False

    def _create_placeholder_icon(self, app_dir: str) -> None:
        """
        Create a placeholder icon if no icon exists.

        Args:
            app_dir: AppDir directory path
        """
        icon_path = os.path.join(app_dir, f"{self._app_name}.png")

        if not os.path.exists(icon_path):
            try:
                # Minimal transparent 1x1 PNG (base64)
                png_data = (
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
                    b"\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
                )
                with open(icon_path, 'wb') as f:
                    f.write(png_data)
                logger.debug(f"Created placeholder icon: {icon_path}")
            except Exception as e:
                logger.warning(f"Could not create placeholder icon: {e}")

    # Public API Methods
    def extract_main_class(self) -> str:
        """
        Extract main class from JAR manifest.

        Returns:
            Detected main class name
        """
        return self._main_class or self._detect_main_class()

    def analyze_dependencies(self) -> Dict[str, Any]:
        """
        Analyze JAR dependencies if analyzer is available.

        Returns:
            Dictionary with dependency analysis results
        """
        if self.dependency_analyzer:
            return self.dependency_analyzer.analyze_jar(self.jar_path)
        return {}

    def _get_app_name_title(self) -> str:
        """
        Get title case version of app name.

        Returns:
            Title case application name
        """
        return self._app_name.title() if self._app_name else "Application"

    def _get_enhanced_features(self) -> Dict[str, bool]:
        """
        Get enhanced features dictionary.

        Returns:
            Dictionary of enabled features
        """
        return self._enhanced_features.copy()

    def get_java_info(self) -> Dict[str, Any]:
        """
        Get comprehensive Java information for the application.

        Returns:
            Dictionary with Java-related information
        """
        return {
            "bundled": self.bundled,
            "jdk_version": self.jdk_version,
            "main_class": self._main_class,
            "enhanced_features": self._enhanced_features,
            "java_bundler_available": self.java_bundler is not None
        }

    def cleanup(self) -> None:
        """
        Clean up temporary files and directories.

        This method should be called when the AppImage creation process is complete
        to clean up temporary build artifacts.
        """
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()
        return False
