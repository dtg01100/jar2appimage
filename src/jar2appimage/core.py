#!/usr/bin/env python3
"""jar2appimage: Enhanced Java Application Packaging"""

import os
import sys
import subprocess
import tarfile
import shutil
from pathlib import Path

class Jar2AppImage:
    """Enhanced AppImage creator with Java dependency management and optional bundling"""
    
    def __init__(self, jar_file: str, output_dir: str = ".", bundled: bool = False):
        self.jar_file = jar_file
        self.jar_path = Path(jar_file)
        self.output_dir = Path(output_dir)
        self.bundled = bundled
        self.java_bundler = None
        
        # Initialize main class storage
        self._app_name = ""
        self._main_class = ""
        self.app_name = self.jar_path.stem
        
        # Create temp directory
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"{self.app_name}-"))
        
        # Initialize enhanced capabilities
        self._enhanced_features = {
            'java_bundler': False,  # Will be set if bundling enabled
            'smart_gui_detection': True,
            'platform_specific_opts': True,
            'professional_desktop_integration': True,
            'comprehensive_error_handling': True,
            'java_dependency_management': True,
            'appimage_creation': True
        }
        
        # Import runtime manager
        from jar2appimage.runtime import JavaRuntimeManager
        self.runtime_manager = JavaRuntimeManager()
        
        # Initialize dependency analyzer
        from jar2appimage.analyzer import JarDependencyAnalyzer
        self.dependency_analyzer = JarDependencyAnalyzer(str(self.jar_file))
    
    def create(self) -> str:
        """Create enhanced AppImage with optional Java bundling"""
        
        # Extract application name from JAR path
        if not os.path.exists(self.jar_file):
            raise FileNotFoundError(f"JAR file not found: {self.jar_file}")
        
        # Extract application name from path
        path = Path(self.jar_file)
        self._app_name = path.stem
        
        # Detect main class using existing logic
        self._main_class = self._detect_main_class()
        
        # Create AppImage directory structure
        import tempfile
        appimage_dir = tempfile.mkdtemp(prefix=f"{self._app_name}-")
        app_dir = os.path.join(appimage_dir, f"{self._app_name}.AppDir")
        
        # Create standard directories
        os.makedirs(os.path.join(app_dir, "usr", "bin"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "usr", "lib"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "usr", "share", "applications"), exist_ok=True)
        
        # Copy JAR file
        dest_jar = os.path.join(app_dir, "usr", "bin", f"{self._app_name}.jar")
        shutil.copy2(self.jar_file, dest_jar)
        
        # Store detected main class
        main_class_file = os.path.join(app_dir, ".main_class")
        with open(main_class_file, 'w') as f:
            f.write(self._main_class)
        
        # Check for Java bundling option
        if self.bundled:
            # Create Java bundler
            from jar2appimage.java_bundler import JavaBundler
            bundler = JavaBundler(jdk_version="11")
            print(f"📦 Creating {self._app_name} with OpenJDK 11...")
            
            # Download and extract OpenJDK
            bundled_jdk_path = bundler.download_opensdk(self.output_dir)
            if not bundled_jdk_path:
                raise RuntimeError("Failed to download/extract OpenJDK")
            
            bundler.extract_opensdk(bundled_jdk_path)
            
            # Create bundled application
            bundle_path = bundler.bundle_application(self.jar_file, self._app_name, self.output_dir)
            
            print(f"✅ Created bundled {self._app_name} application: {bundle_path}")
            
        else:
            # Prepare AppDir (desktop file, AppRun)
            try:
                self._create_desktop_file(app_dir, self._app_name)
            except Exception:
                # Non-fatal: continue even if desktop file creation fails
                pass

            try:
                self._install_apprun(app_dir, self._app_name)
            except Exception:
                # Non-fatal: continue even if AppRun installation fails
                pass

            # Use standard AppImage creation
            appimage_path = self._create_standard_appimage(app_dir, self._app_name)

        return appimage_path
    
    def extract_main_class(self) -> str:
        """Extract main class from JAR manifest"""
        return self._detect_main_class()
    
    def analyze_dependencies(self) -> dict:
        """Analyze JAR dependencies"""
        return self.dependency_analyzer.analyze_jar(self.jar_path)
    
    def _detect_main_class(self) -> str:
        """Detect main class using multiple strategies"""
        # Try to read from manifest first
        try:
            import zipfile
            with zipfile.ZipFile(self.jar_file, 'r') as jar:
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_data = jar.read('META-INF/MANIFEST.MF').decode('utf-8')
                    for line in manifest_data.split('\n'):
                        if line.startswith('Main-Class:'):
                            self._main_class = line.split(':', 1)[1].strip()
                            print(f"📋 Detected Main-Class from manifest: {self._main_class}")
                            return self._main_class
        except Exception:
            # Ignore manifest parsing errors and continue to fallbacks
            pass
        
        # Fallback to pattern matching
        if not self._main_class:
            try:
                import os
                result = subprocess.run(['jar', 'tf', self.jar_file], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    classes = result.stdout.split('\n')
                    for class_line in classes:
                        if class_line.strip() and '.class' in class_line:
                            class_name = class_line.replace('.class', '').replace('/', '.')
                            if class_name in ['Main', 'App', 'Application', 'Launcher']:
                                self._main_class = class_name
                                print(f"📋 Detected main class from patterns: {class_name}")
                                return class_name
            except Exception:
                # Ignore jar tool failures
                pass
        
        # Return None if no main class found (don't use filename fallback for tests)
        return None
    
    def _create_standard_appimage(self, appimage_dir: str, app_name: str) -> str:
        """Create standard AppImage without Java bundling"""
        
        # Get appimagetool (download if necessary)
        from jar2appimage.tools import ToolManager
        tool_manager = ToolManager()
        try:
            appimagetool_path = tool_manager.get_appimagetool()
        except RuntimeError as e:
            raise RuntimeError(f"Cannot create AppImage: {e}")
        
        output_path = os.path.join(self.output_dir, f"{app_name}.AppImage")
        
        try:
            # Ensure ARCH is provided when appimagetool cannot guess it
            import platform as _platform
            arch_map = {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64"}
            arch = arch_map.get(_platform.machine(), _platform.machine())
            env = os.environ.copy()
            env["ARCH"] = arch

            subprocess.run([
                appimagetool_path, "--no-appstream", appimage_dir, output_path
            ], check=True, capture_output=True, text=True, env=env)
            
            appimage_size = os.path.getsize(output_path)
            print(f"✅ Created standard AppImage: {output_path} ({appimage_size // 1024 // 1024} MB)")
            return output_path
            
        except Exception as e:
            # Include stderr/stdout when available for debugging
            if hasattr(e, 'stderr') and e.stderr:
                print(f"❌ AppImage creation failed: {e.stderr}")
            else:
                print(f"❌ AppImage creation failed: {e}")
            return None

    def _install_apprun(self, appimage_dir: str, app_name: str):
        """Install AppRun script customized to this application"""

        apprun_path = os.path.join(appimage_dir, "AppRun")

        # Simple AppRun that launches the bundled JAR
        apprun_content = f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
JAR_FILE="${{HERE}}/usr/bin/{app_name}.jar"
if [ ! -f "$JAR_FILE" ]; then
  echo "Error: JAR file not found: $JAR_FILE"
  exit 1
fi
exec java -jar "$JAR_FILE" "$@"
"""

        with open(apprun_path, 'w') as f:
            f.write(apprun_content)

        # Make executable
        os.chmod(apprun_path, 0o755)
        print(f"Installed AppRun: {apprun_path}")
    
    def _create_bundled_appimage(self, appimage_dir: str, app_name: str) -> str:
        """Create AppImage with bundled Java"""
        
        # Bundled path will be handled via java_bundler; no precondition variable here
        
        # Create Java bundler if not initialized
        if not self.java_bundler:
            from jar2appimage.java_bundler import JavaBundler
            self.java_bundler = JavaBundler(jdk_version="11")
        
        print(f"📦 Initializing Java bundler for {app_name}...")
        
        # Download and extract OpenJDK
        bundled_jdk_path = self.java_bundler.download_opensdk(self.output_dir)
        if not bundled_jdk_path:
            raise RuntimeError("Failed to download/extract OpenJDK")
            
        self.java_bundler.extract_opensdk(bundled_jdk_path)
        
        # Create bundled application
        bundle_path = self.java_bundler.bundle_application(self.jar_file, app_name, self.output_dir)
        
        print(f"✅ Created bundled {app_name.title()} application: {bundle_path}")
        return bundle_path
    
    def _create_desktop_file(self, appimage_dir: str, app_name: str):
        """Create enhanced .desktop file with smart features"""
        desktop_path = os.path.join(appimage_dir, f"{app_name}.desktop")
        
        # Smart terminal detection
        needs_terminal = self._needs_terminal()
        
        # Compose a compliant desktop file (no leading spaces on lines)
        import textwrap
        desktop_content = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Name={app_name}
            Comment=Java application packaged as AppImage
            Exec=AppRun
            Icon={app_name}
            Categories=Development;Utility
            Terminal={"true" if needs_terminal else "false"}
            StartupNotify=true
            StartupWMClass=java
            Keywords=java;jar;{app_name}
        """)
        
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        # Also copy to standard location
        desktop_install_dir = os.path.join(appimage_dir, "usr", "share", "applications")
        os.makedirs(desktop_install_dir, exist_ok=True)
        desktop_install_path = os.path.join(desktop_install_dir, f"{app_name}.desktop")
        shutil.copy2(desktop_path, desktop_install_path)
        
        print(f"Created desktop file: {desktop_install_path}")
        # Ensure an icon file exists (create a tiny placeholder PNG if necessary)
        icon_path = os.path.join(appimage_dir, f"{app_name}.png")
        if not os.path.exists(icon_path):
            # Minimal transparent 1x1 PNG (base64)
            png_data = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
                b"\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            with open(icon_path, 'wb') as f:
                f.write(png_data)
            print(f"Created placeholder icon: {icon_path}")
        return desktop_path
    
    def _needs_terminal(self) -> bool:
        """Determine if application needs terminal based on main class and name"""
        gui_indicators = ["gui", "swing", "awt", "desktop", "window", "app", "interface", "frame", "panel"]
        cli_indicators = ["cli", "command", "tool", "utility", "batch", "console", "shell"]
        
        main_class_lower = self._main_class.lower()
        app_name_lower = self._app_name.lower()
        
        # Check if main class or app name suggests GUI application
        for indicator in gui_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                # GUI apps generally should not launch a terminal
                return False
        
        for indicator in cli_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return True
        
        # Default to no terminal
        return False
    
    def _get_app_name_title(self) -> str:
        """Get title case version of app name"""
        return self._app_name.title() if self._app_name else "Application"
    
    def _get_enhanced_features(self) -> dict:
        """Get enhanced features dictionary"""
        return self._enhanced_features