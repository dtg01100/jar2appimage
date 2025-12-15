#!/usr/bin/env python3
"""jar2appimage: Enhanced Java Application Packaging"""

import os
import sys
import subprocess
import tarfile
from pathlib import Path

class Jar2AppImage:
    """Enhanced AppImage creator with Java dependency management and optional bundling"""
    
    def __init__(self, jar_file: str, output_dir: str = ".", bundled: bool = False):
        self.jar_file = jar_file
        self.output_dir = output_dir
        self.bundled = bundled
        self.java_bundler = None
        
        # Initialize main class storage
        self._app_name = ""
        self._main_class = ""
        
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
        
        # Initialize main class storage
        self._app_name = ""
        self._main_class = ""
    
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
            # Use standard AppImage creation
            appimage_path = self._create_standard_appimage(app_dir, self._app_name)
    
        return appimage_path
    
    def _detect_main_class(self) -> str:
        """Detect main class using multiple strategies"""
        # Try to read from manifest first
        try:
            import zipfile
            with zipfile.ZipFile(self.jar_file, 'r') as jar:
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_data = jar.read('META-INF/MANTIFEST.MF').decode('utf-8')
                    for line in manifest_data.split('\n'):
                        if line.startswith('Main-Class:'):
                            self._main_class = line.split(':', 1)[1].strip()
                            print(f"📋 Detected Main-Class from manifest: {self._main_class}")
                            return self._main_class
        except Exception:
            pass
        
        # Fallback to pattern matching
        if not self._main_class:
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
                            break
        except:
            pass
        
        # Final fallback
        if not self._main_class:
            self._main_class = Path(self.jar_file).stem
            print(f"📋 Using JAR filename as main class: {self._main_class}")
        
        return self._main_class
    
    def _create_standard_appimage(self, appimage_dir: str, app_name: str) -> str:
        """Create standard AppImage without Java bundling"""
        
        # Create AppImage using appimagetool
        appimagetool_path = shutil.which("appimagetool")
        output_path = os.path.join(self.output_dir, f"{app_name}.AppImage")
        
        try:
            subprocess.run([
                appimagetool_path, "--no-appstream", appimage_dir, output_path
            ], check=True, capture_output=True, text=True)
            
            appimage_size = os.path.getsize(output_path)
            print(f"✅ Created standard AppImage: {output_path} ({appimage_size // 1024 // 1024} MB)")
            return output_path
            
        except Exception as e:
            print(f"❌ AppImage creation failed: {e}")
            return None
    
    def _create_bundled_appimage(self, appimage_dir: str, app_name: str) -> str:
        """Create AppImage with bundled Java"""
        
        if not self.bundled_jdk_path:
            raise RuntimeError("Java must be bundled before creating bundling AppImage")
        
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
        
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=Java application packaged as AppImage
Exec=AppRun
Icon={app_name}
Categories=Development;Utility;
        Terminal={"true" if needs_terminal else "false"}
StartupNotify=true
StartupWMClass=java
Keywords=java;jar;{app_name};
"""
        
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        # Also copy to standard location
        desktop_install_dir = os.path.join(appimage_dir, "usr", "share", "applications")
        os.makedirs(desktop_install_dir, exist_ok=True)
        desktop_install_path = os.path.join(desktop_install_dir, f"{app_name}.desktop")
        shutil.copy2(desktop_path, desktop_install_path)
        
        print(f"Created desktop file: {desktop_install_path}")
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
                return True
        
        for indicator in cli_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return True
        
        # Default to no terminal for GUI safety
        return False
    
    def _get_app_name_title(self) -> str:
        """Get title case version of app name"""
        return self._app_name.title() if self._app_name else "Application"
    
    def _get_enhanced_features(self) -> dict:
        """Get enhanced features dictionary"""
        return self._enhanced_features