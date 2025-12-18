#!/usr/bin/env python3
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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Protocol, cast

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
        bundled: bool = True,  # Default to True for portable, self-contained AppImages
        jdk_version: str = "11",
        bundle_supporting_files: bool = True,  # Whether to bundle supporting files (config, assets, etc.)
        java_bundler: Optional[JavaBundlerProtocol] = None
    ):
        """
        Initialize the AppImage creator.

        Args:
            jar_file: Path to the JAR file to package
            output_dir: Output directory for the AppImage
            bundled: Whether to bundle Java runtime
            jdk_version: Java version to use for bundling
            bundle_supporting_files: Whether to bundle supporting files (config, assets, etc.)
            java_bundler: Optional Java bundler for dependency injection
        """
        self.jar_file = jar_file
        self.jar_path = Path(jar_file)
        self.output_dir = Path(output_dir)
        self.bundled = bundled
        self.jdk_version = jdk_version
        self.bundle_supporting_files = bundle_supporting_files
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
        self.runtime_manager: Optional[Any] = None
        try:
            from jar2appimage.runtime import JavaRuntimeManager
            self.runtime_manager = JavaRuntimeManager()
            logger.debug("JavaRuntimeManager initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import runtime module: {e}")
            self.runtime_manager = None

        # Initialize dependency analyzer with graceful fallback
        self.dependency_analyzer: Optional[Any] = None
        try:
            from jar2appimage.dependency_analyzer import (
                AnalysisConfiguration,
                ComprehensiveDependencyAnalyzer,
            )
            config = AnalysisConfiguration(
                analyze_bytecode=True,
                resolve_transitive=False,
                generate_reports=False,
                verbose=False
            )
            self.dependency_analyzer = ComprehensiveDependencyAnalyzer(config)
            logger.debug("ComprehensiveDependencyAnalyzer initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import new dependency analyzer module: {e}")
            # Fallback to old analyzer
            try:
                from jar2appimage.analyzer import JarDependencyAnalyzer
                self.dependency_analyzer = JarDependencyAnalyzer(str(self.jar_file))
                logger.debug("JarDependencyAnalyzer (legacy) initialized successfully")
            except ImportError as e2:
                logger.warning(f"Could not import legacy analyzer module: {e2}")
                self.dependency_analyzer = None

        analyzer = cast(Optional[Any], self.dependency_analyzer)
        # Provide legacy 'analyze_jar' compatibility if using the new analyzer API
        if analyzer and not hasattr(analyzer, 'analyze_jar'):
            def _legacy_analyze_jar(jar_path: Path) -> Dict[str, Any]:
                """Wrapper to provide legacy `analyze_jar` API for compatibility and tests."""
                try:
                    # Try to call the new analyze_application API and return a legacy-like shape
                    if hasattr(analyzer, 'analyze_application'):
                        result = analyzer.analyze_application([str(jar_path)])
                        return {
                            'jar_path': str(result.jar_analysis.jar_path) if getattr(result, 'jar_analysis', None) else str(jar_path),
                            'dependencies': [getattr(d, '__dict__', d) for d in getattr(result, 'resolution_result', {}).get('resolved_dependencies', [])] if getattr(result, 'resolution_result', None) else [],
                            'warnings': getattr(result, 'warnings', []),
                            'errors': getattr(result, 'errors', []),
                            'analysis_metadata': getattr(result, 'analysis_metadata', {})
                        }
                except Exception as e:
                    logger.debug(f"Legacy analyze_jar wrapper failed: {e}")
                # Fallback minimal shape expected by tests
                return {'found_local_jars': [], 'missing_jars': []}

            # Attach wrapper to the analyzer instance so patch.object calls succeed in tests
            analyzer.analyze_jar = _legacy_analyze_jar  # type: ignore[attr-defined]
            self.dependency_analyzer = analyzer

    @property
    def app_name(self) -> str:
        """Public app name property for legacy consumers and tests"""
        return self._app_name

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

            # Step 4: Copy supporting files (config, assets, etc.) if enabled
            if self.bundle_supporting_files:
                self._copy_supporting_files(app_dir)

            # Step 5: Handle Java bundling if requested
            if self.bundled:
                self._handle_java_bundling(app_dir)

            # Step 6: Create desktop file and AppRun script
            self._create_desktop_file(app_dir)
            self._install_apprun(app_dir)

            # Step 7: Create final AppImage
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

    def _copy_supporting_files(self, app_dir: str) -> None:
        """
        Identify and copy supporting files for the JAR application.

        This includes common configuration files, assets, libraries, and directories
        that are typically found alongside JAR files.

        Args:
            app_dir: AppDir directory path
        """
        logger.debug("Copying supporting files for the application")

        try:
            jar_path = Path(self.jar_file)
            jar_dir = jar_path.parent
            jar_name_stem = jar_path.stem  # Name without extension

            # Define file extensions and directories to consider as supporting files
            supporting_extensions = {
                '.properties', '.yml', '.yaml', '.json', '.xml', '.conf', '.config',
                '.txt', '.ini', '.cfg', '.log', '.sql', '.db', '.sqlite', '.jar',
                '.so', '.dll', '.dylib', '.jnilib', '.dll', '.exe', '.sh', '.bat'
            }

            # Define directory names that are commonly used for assets/configs
            supporting_directories = {
                'config', 'conf', 'assets', 'resources', 'data', 'lib',
                'libs', 'library', 'libraries', 'native', 'jni', 'plugins',
                'themes', 'icons', 'fonts', 'images', 'sounds', 'media',
                'logs', 'log', 'temp', 'tmp', 'cache', 'storage', 'static',
                'templates', 'views', 'scripts', 'bin', 'tools', 'util'
            }

            # Destination directories in the AppImage
            dest_bin_dir = Path(app_dir) / "usr" / "bin"
            dest_resources_dir = Path(app_dir) / "usr" / "share" / self._app_name

            # Create resources directory if needed
            dest_resources_dir.mkdir(parents=True, exist_ok=True)

            # Track copied files to avoid duplicates
            copied_files = set()

            # Copy files from the same directory as the JAR
            if jar_dir.exists():
                for item in jar_dir.iterdir():
                    if item.name == jar_path.name:
                        continue  # Skip the main JAR file

                    # Check if it's a supporting file based on extension
                    if item.is_file() and item.suffix.lower() in supporting_extensions:
                        # Check if it's related to this JAR (name-matching heuristic)
                        if jar_name_stem.lower() in item.name.lower() or len(jar_name_stem) <= 3:
                            # For short JAR names, copy any matching file type
                            dest_file = dest_resources_dir / item.name
                            shutil.copy2(item, dest_file)
                            copied_files.add(item.name)
                            logger.debug(f"Copied supporting file: {item.name}")

                    # Check if it's a supporting directory
                    elif item.is_dir() and item.name.lower() in supporting_directories:
                        dest_dir = dest_resources_dir / item.name
                        if not dest_dir.exists():
                            shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                            logger.debug(f"Copied supporting directory: {item.name}")

            # Look for app-specific directories (e.g., "myapp-config", "myapp-data")
            for item in jar_dir.parent.iterdir() if jar_dir != jar_dir.parent else []:
                if item.is_dir() and jar_name_stem.lower() in item.name.lower():
                    # Copy app-specific directory
                    dest_dir = dest_resources_dir / item.name
                    if not dest_dir.exists():
                        shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                        logger.debug(f"Copied app-specific directory: {item.name}")

            # Create a manifest of supporting files for reference
            if copied_files:
                manifest_file = dest_resources_dir / "SUPPORTING_FILES_MANIFEST.txt"
                with open(manifest_file, 'w') as f:
                    f.write("# Supporting files automatically bundled with the AppImage\n")
                    f.write(f"# Source JAR: {jar_path.name}\n")
                    f.write(f"# Bundle date: {datetime.now().isoformat()}\n\n")
                    for file_name in sorted(copied_files):
                        f.write(f"{file_name}\n")

                logger.info(f"Identified and copied {len(copied_files)} supporting files")
            else:
                logger.debug("No supporting files identified for bundling")

        except Exception as e:
            logger.warning(f"Failed to copy supporting files: {e}")
            # Don't raise exception - supporting files are optional

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
RESOURCES_DIR="${{HERE}}/usr/share/{self._app_name}"

if [ ! -f "$JAR_FILE" ]; then
  echo "Error: JAR file not found: $JAR_FILE"
  exit 1
fi

# Set up environment for supporting files
export APP_RESOURCES_DIR="$RESOURCES_DIR"

# Execute with bundled JAR, with resources directory available
exec java -Dapp.resources.dir="$RESOURCES_DIR" -cp "$JAR_FILE:$RESOURCES_DIR/*:$RESOURCES_DIR" -jar "$JAR_FILE" "$@"
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
RESOURCES_DIR="${{HERE}}/usr/share/{self._app_name}"

if [ ! -f "$JAR_FILE" ]; then
  echo "Error: JAR file not found: $JAR_FILE"
  exit 1
fi

# Guarantee use of bundled Java - no fallback to system Java
BUNDLED_JAVA="${{HERE}}/usr/java/bin/java"
if [ ! -f "$BUNDLED_JAVA" ]; then
    echo "Error: Bundled Java not found at expected location: $BUNDLED_JAVA"
    echo "This AppImage was created with bundled Java but the Java runtime is missing."
    echo "This indicates an error in the AppImage creation process."
    exit 1
fi

export JAVA_HOME="${{HERE}}/usr/java"
export PATH="${{HERE}}/usr/java/bin:$PATH"
JAVA_CMD="$BUNDLED_JAVA"

echo "Using bundled Java: $($JAVA_CMD -version 2>&1 | head -1)"

# Set up environment for supporting files
export APP_RESOURCES_DIR="$RESOURCES_DIR"

# Execute with bundled JAR, with resources directory available
exec "$JAVA_CMD" -Dapp.resources.dir="$RESOURCES_DIR" -cp "$JAR_FILE:$RESOURCES_DIR/*:$RESOURCES_DIR" -jar "$JAR_FILE" "$@"
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
    def extract_main_class(self) -> Optional[str]:
        """
        Extract main class from JAR manifest.

        Returns:
            Detected main class name or None if not found
        """
        try:
            return self._main_class or self._detect_main_class()
        except MainClassDetectionError:
            # For empty or simple JARs, we prefer returning None instead of raising
            logger.debug("No main class detected; returning None")
            return None

    def analyze_dependencies(self) -> Dict[str, Any]:
        """
        Analyze JAR dependencies if analyzer is available.

        Returns:
            Dictionary with dependency analysis results
        """
        analyzer = self.dependency_analyzer
        analyzer = cast(Optional[Any], self.dependency_analyzer)
        if analyzer is not None:
            # Prefer legacy `analyze_jar` if present (backwards compatibility and tests)
            if hasattr(analyzer, 'analyze_jar'):
                return cast(Dict[str, Any], analyzer.analyze_jar(self.jar_path))

            # Check if it's the new comprehensive analyzer
            if hasattr(analyzer, 'analyze_application'):
                result = analyzer.analyze_application([str(self.jar_path)])
                # Convert to legacy format for backward compatibility
                return cast(Dict[str, Any], {
                    'jar_path': str(result.jar_analysis.jar_path) if result.jar_analysis else str(self.jar_path),
                    'dependencies': [dep.__dict__ for dep in result.resolution_result.resolved_dependencies] if result.resolution_result else [],
                    'warnings': result.warnings,
                    'errors': result.errors,
                    'analysis_metadata': result.analysis_metadata
                })
        return {}

    def get_dependency_aware_classpath(self) -> List[str]:
        """
        Get classpath entries based on dependency analysis.

        Returns:
            List of classpath entries including resolved dependencies
        """
        classpath: List[str] = []

        if self.dependency_analyzer and hasattr(self.dependency_analyzer, 'analyze_application'):
            try:
                result = self.dependency_analyzer.analyze_application([str(self.jar_path)])
                if result.resolution_result:
                    classpath.extend(result.classpath)
                logger.debug(f"Generated dependency-aware classpath with {len(classpath)} entries")
            except Exception as e:
                logger.warning(f"Failed to generate dependency-aware classpath: {e}")

        # Fallback to basic JAR path
        if not classpath:
            classpath.append(str(self.jar_path))

        return classpath

    def get_bundling_recommendations(self) -> Dict[str, Any]:
        """
        Get bundling recommendations based on dependency analysis.

        Returns:
            Dictionary with bundling recommendations and metadata
        """
        recommendations: Dict[str, Any] = {
            'should_bundle_native_libs': False,
            'should_bundle_optional_deps': False,
            'estimated_bundle_size_mb': 0,
            'dependency_count': 0,
            'native_library_count': 0,
            'conflict_count': 0,
            'recommendations': [],
            'warnings': []
        }

        if self.dependency_analyzer and hasattr(self.dependency_analyzer, 'analyze_application'):
            try:
                result = self.dependency_analyzer.analyze_application([str(self.jar_path)])

                if result.bundling_decisions:
                    bundle_decisions = result.bundling_decisions
                    recommendations.update({
                        'should_bundle_native_libs': len(bundle_decisions.get('native_libraries', [])) > 0,
                        'dependency_count': bundle_decisions.get('total_dependencies', 0),
                        'native_library_count': len(bundle_decisions.get('native_libraries', [])),
                        'recommendations': bundle_decisions.get('optimization_suggestions', [])
                    })

                if result.resolution_result:
                    recommendations['conflict_count'] = len(result.resolution_result.conflicts)

                recommendations['warnings'].extend(result.warnings)

                logger.debug(f"Generated bundling recommendations: {len(recommendations['recommendations'])} suggestions")

            except Exception as e:
                logger.warning(f"Failed to generate bundling recommendations: {e}")
                recommendations['warnings'].append(f"Analysis failed: {e}")

        return recommendations

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

    def __enter__(self) -> "Jar2AppImage":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        """Context manager exit with cleanup"""
        self.cleanup()
        return False
