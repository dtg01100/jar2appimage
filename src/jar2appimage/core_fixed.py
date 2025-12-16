#!/usr/bin/env python3
# mypy: ignore-errors
"""Simple Java bundler for jar2appimage - Fixed Version"""

import os
import shutil
import subprocess
import tarfile
import tempfile


class JavaBundler:
    """Simple bundler that always bundles Java with applications"""

    def __init__(self, jdk_version: str = "11"):
        self.jdk_version = jdk_version
        self.bundled_jdk_path = None

    def download_opensdk(self, output_dir: str = ".") -> str:
        """Download OpenJDK for Java bundling"""
        jdk_arch = "x64_linux"
        self.jdk_version.replace("+", "_")

        # Common OpenJDK download URLs
        jdk_urls = {
            "11": "https://github.com/adoptium/temurin11-jdk{jdk_version_clean}.tar.gz",
            "17": "https://github.com/adoptium/temurin17-jdk{jdk_version_clean}.tar.gz"
        }

        jdk_url = jdk_urls.get(self.jdk_version, jdk_urls.get("11"))
        if not jdk_url:
            raise ValueError(f"Unsupported OpenJDK version: {self.jdk_version}")

        jdk_filename = f"openjdk-{self.jdk_version}-{jdk_arch}.tar.gz"
        jdk_path = os.path.join(output_dir, jdk_filename)

        print(f"🔍 Downloading OpenJDK {self.jdk_version} ({jdk_arch})...")

        try:
            subprocess.run([
                "curl", "-L", "-f", "-", "-o", jdk_path, jdk_url
            ], check=True, capture_output=True, text=True)

            if os.path.exists(jdk_path):
                file_size = os.path.getsize(jdk_path)
                print(f"✅ OpenJDK {self.jdk_version} downloaded: {jdk_filename} ({file_size // 1024 // 1024} MB)")
                return jdk_path
            else:
                print(f"❌ Download failed: {jdk_filename}")
                return None

        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def extract_opensdk(self, jdk_path: str, extract_to: str = ".") -> str:
        """Extract OpenJDK for bundling"""
        extract_dir = jdk_path.replace(".tar.gz", "")

        print(f"📦 Extracting OpenJDK from {jdk_path}...")

        try:
            with tarfile.open(jdk_path, "r:gz") as tar:
                tar.extractall(path=extract_dir)

            extracted_jdk_path = os.path.join(extract_dir, f"jdk-{self.jdk_version}")
            print(f"✅ OpenJDK extracted to: {extracted_jdk_path}")
            return extracted_jdk_path

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None

    def bundle_application(self, jar_path: str, app_name: str) -> str:
        """Bundle Java application with JDK"""
        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"JAR file not found: {jar_path}")

        if not self.bundled_jdk_path:
            raise RuntimeError("OpenJDK must be downloaded and extracted first")

        app_name_clean = app_name.replace(" ", "-").lower()

        print(f"📦 Bundling {app_name_clean} with bundled JDK {self.jdk_version}...")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = os.path.join(temp_dir, f"{app_name_clean}-bundled")
            os.makedirs(bundle_dir, exist_ok=True)

        # Copy JAR
        dest_jar = os.path.join(bundle_dir, f"{app_name_clean}.jar")
        shutil.copy2(jar_path, dest_jar)

        # Copy JDK if available
        jdk_src = self.bundled_jdk_path if self.bundled_jdk_path else shutil.which("java")

        if jdk_src:
            jdk_dest = os.path.join(bundle_dir, "jdk")
            shutil.copytree(self.bundled_jdk_path, jdk_dest)
            jdk_files = [f"openjdk-{self.jdk_version}"]

            for jdk_file in jdk_files:
                src_jdk = os.path.join(self.bundled_jdk_path, jdk_file)
                dest_jdk = os.path.join(jdk_dest, jdk_file)
                shutil.copy2(src_jdk, dest_jdk)
                print(f"Copied JDK: {jdk_file}")

        # Set up Java bundler if OpenJDK is available
        self.java_bundler = JavaBundler()
        if self.java_bundler:
            print("✅ Java bundler available for self-contained deployment")
        else:
            print("⚠️ Java bundler not available, using basic detection")

        # Create tarball
        bundle_filename = f"{app_name_clean}-bundled.tar.gz"
        bundle_path = os.path.join(self.output_dir, bundle_filename)

        try:
            with tarfile.open(bundle_path, "w:gz") as tar:
                tar.add(bundle_dir, arcname=f"{app_name_clean}-bundled")

            bundle_size = os.path.getsize(bundle_path)
            print(f"✅ Created bundled application: {bundle_filename} ({bundle_size // 1024 // 1024} MB)")

            return bundle_path

        except Exception as e:
            print(f"❌ Bundle creation failed: {e}")
            return None

    def get_jdk_path(self) -> str:
        """Get path to bundled JDK"""
        return self.bundled_jdk_path if self.bundled_jdk_path else None

    def get_appimage_path(self) -> str:
        """Get AppImage path"""
        return self.appimage_path if hasattr(self, '_appimage_path') else os.path.join(self.output_dir, f"{self._app_name}.AppImage")

    def is_bundled(self) -> bool:
        """Check if AppImage uses bundled Java"""
        return self.bundled

    def _detect_main_class(self) -> str:  # noqa: C901
        """Detect main class from JAR or using patterns"""
        # Try to read from manifest first
        try:
            import zipfile
            with zipfile.ZipFile(self.jar_file, 'r') as jar:
                if 'META-INF/MANIFEST.MF' in jar.namelist():
                    manifest_data = jar.read('META-INF/MANIFEST.MF').decode('utf-8')
                    for line in manifest_data.split('\n'):
                        if line.startswith('Main-Class:'):
                            self._main_class = line.split(':', 1)[1].strip()
                            print(f"📋 Found Main-Class in manifest: {self._main_class}")
                            return self._main_class
        except Exception:
            pass

        # Fallback to pattern matching
        if not self._main_class:
            jar_files = subprocess.run(['jar', 'tf', self.jar_file],
                                      capture_output=True, text=True, timeout=10)
            if jar_files.returncode == 0:
                class_list = jar_files.stdout.split('\n')

                # Look for main class candidates
                main_patterns = ["Main", "App", "Application", "Launcher", "executable.Main", "Bootstrap"]

                for pattern in main_patterns:
                    for class_file in class_list:
                        if pattern in class_file:
                            self._main_class = class_file.replace('.class', '').replace('/', '.')
                            print(f"📋 Found main class via pattern: {self._main_class}")
                            return self._main_class

                # Default to jar filename if no class found
                base_name = os.path.basename(self.jar_file).replace('.jar', '')
                for pattern in main_patterns:
                    if base_name.lower() == pattern.lower():
                        self._main_class = base_name
                        break

                # Final fallback
                if not self._main_class:
                    self._main_class = base_name

        return self._main_class

    def _needs_terminal(self) -> bool:
        """Determine if application needs terminal based on main class and name"""
        gui_indicators = ["gui", "swing", "awt", "desktop", "window", "app", "interface", "frame", "panel"]
        cli_indicators = ["cli", "command", "tool", "utility", "batch", "console", "shell"]

        if hasattr(self, '_app_name') and hasattr(self, '_main_class'):
            app_name = getattr(self, '_app_name', '')
            main_class = getattr(self, '_main_class', '')
            main_class_lower = main_class.lower()
            app_name_lower = app_name.lower()

        # GUI applications typically don't need terminal
        for indicator in gui_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return False

        # CLI applications typically need terminal
        for indicator in cli_indicators:
            if indicator in main_class_lower or indicator in app_name_lower:
                return True

        # Default to no terminal for GUI safety
        return False

    def _create_appimage_file(self, appimage_dir: str, app_name: str) -> str:
        """Create final AppImage file"""
        # Create enhanced AppRun script with smart terminal detection
        self._needs_terminal()

        apprun_content = f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
export PATH="${{HERE}}/usr/bin/:${{PATH}}"
export LD_LIBRARY_PATH="${{HERE}}/usr/lib/:${{LD_LIBRARY_PATH}}"

# Enhanced Java dependency checking
JAVA_CMD=""
for candidate in "java" "/usr/bin/java" "/usr/local/bin/java"; do
    if command -v "$candidate" >/dev/null 2>&1; then
        JAVA_CMD="$candidate"
        echo "✅ Found Java: $JAVA_CMD"
        break
    fi
done

if [ -z "$JAVA_CMD" ]; then
    echo "❌ No Java runtime found on system."
    echo "Please install Java 11 or later:"
    echo "  - Ubuntu/Debian: sudo apt install openjdk-11-jre"
    echo "  - RHEL/CentOS: sudo yum install java-11-openjdk"
    echo "  - Arch Linux: sudo pacman -S jdk11-openjdk"
    echo "  - Homebrew: brew install openjdk@11"
    echo "  - Download: https://adoptium.net/"
    exit 1
fi

# Test Java is actually working
if ! "$JAVA_CMD" -version >/dev/null 2>&1; then
    echo "❌ Java found but not working: $JAVA_CMD"
    exit 1
fi

echo "✅ Java runtime validated: $("$JAVA_CMD" -version 2>&1 | head -1)"

# Get JAR file path
JAR_FILE="${{HERE}}/usr/bin/{app_name}.jar"

# Check if JAR exists
if [ ! -f "$JAR_FILE" ]; then
    echo "Error: JAR file not found: $JAR_FILE"
    exit 1
fi

# Build classpath with dependencies
CLASSPATH="$JAR_FILE"
LIB_DIR="${{HERE}}/usr/lib"
if [ -d "$LIB_DIR" ]; then
    for jar in "$LIB_DIR"/*.jar; do
        if [ -f "$jar" ]; then
            CLASSPATH="$CLASSPATH:$jar"
        fi
    done
fi

# Detect if this is a GUI application
GUI_MODE=false
if echo "$MAIN_CLASS" | grep -i "workbench\\|swing\\|java\\|gui\\|app"; then
    GUI_MODE=true
else
    GUI_MODE=false
fi

# Set up Java options for GUI applications
if [ "$GUI_MODE" = "true" ]; then
    # Standard GUI Java options
    JAVA_OPTS="--add-opens java.desktop/com.sun.java.swing.plaf.motif=ALL-UNNAMED"
    JAVA_OPTS="$JAVA_OPTS --add-opens java.desktop/com.sun.java.swing.plaf.gtk=ALL-UNNAMED"

    # Check operating system for specific options
    OS_NAME="$(uname -s)"
    case "$OS_NAME" in
        Darwin)
            JAVA_OPTS="$JAVA_OPTS --add-opens java.desktop/com.apple.laf=ALL-UNNAMED"
            ;;
        Linux)
            JAVA_OPTS="$JAVA_OPTS -Dawt.useSystemAAFontSettings=on"
            ;;
    esac
fi

# Try to run as -jar first (if Main-Class is defined)
if "$JAVA_CMD" -jar "$JAR_FILE" "$@" 2>/dev/null; then
    exit 0
fi

# Fallback to using detected main class if available
if [ -n "$MAIN_CLASS" ]; then
    echo "Using detected main class: $MAIN_CLASS"
    if [ "$GUI_MODE" = "true" ]; then
        exec "$JAVA_CMD" $JAVA_OPTS -cp "$CLASSPATH" "$MAIN_CLASS" "$@"
    else
        exec "$JAVA_CMD" -cp "$CLASSPATH" "$MAIN_CLASS" "$@"
    fi
fi

echo "✅ Java runtime validated: $("$JAVA_CMD" -version 2>&1 | head -1)"
"""
        return apprun_content
