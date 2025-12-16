"""Java Runtime Manager with Java bundling support"""

import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path


class JavaBundler:
    """Bundles OpenJDK with Java applications for self-contained AppImages"""

    def __init__(self, jdk_version: str = "11"):
        self.jdk_version = jdk_version
        self.bundled_jdk_path = None

    def download_opensdk(self, output_dir: str = ".") -> str:
        """Download OpenJDK for bundling using Adoptium API"""
        import json
        import urllib.request
        jdk_major = str(self.jdk_version)
        if jdk_major not in ["8", "11", "17", "21"]:
            print(f"❌ Unsupported OpenJDK version: {self.jdk_version}")
            return None

        api_url = f"https://api.adoptium.net/v3/assets/feature_releases/{jdk_major}/ga?architecture=x64&image_type=jdk&os=linux"
        print(f"🔍 Querying Adoptium API for OpenJDK {self.jdk_version}...")
        try:
            with urllib.request.urlopen(api_url) as resp:
                data = json.load(resp)
        except Exception as e:
            print(f"❌ Failed to query Adoptium API: {e}")
            return None

        # Find the latest GA binary
        jdk_url = None
        jdk_filename = None
        for release in data:
            for binary in release.get("binaries", []):
                pkg = binary.get("package", {})
                link = pkg.get("link")
                name = pkg.get("name")
                if link and name and "hotspot" in name and name.endswith(".tar.gz"):
                    jdk_url = link
                    jdk_filename = name
                    break
            if jdk_url:
                break

        if not jdk_url or not jdk_filename:
            print(f"❌ Could not find a suitable OpenJDK binary for version {self.jdk_version}")
            return None

        jdk_path = os.path.join(output_dir, jdk_filename)
        print(f"🔍 Downloading OpenJDK from {jdk_url} ...")
        try:
            subprocess.run(
                ["curl", "-L", "-f", "-#", "-o", jdk_path, jdk_url],
                check=True,
                capture_output=True,
                text=True,
            )
            if os.path.exists(jdk_path):
                file_size = os.path.getsize(jdk_path)
                print(f"✅ OpenJDK downloaded: {jdk_filename} ({file_size // 1024 // 1024} MB)")
                return jdk_path
            else:
                print(f"❌ Download failed for {jdk_filename}")
                return None
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def extract_opensdk(self, jdk_path: str) -> str:
        """Extract OpenJDK for bundling"""
        extract_dir = jdk_path.replace(".tar.gz", "")

        print(f"📦 Extracting OpenJDK from {jdk_path}...")

        try:
            with tarfile.open(jdk_path, "r:gz") as tar:
                tar.extractall(path=extract_dir)

            extracted_jdk_path = os.path.join(
                extract_dir, f"openjdk-{self.jdk_version}"
            )
            print(f"✅ OpenJDK extracted to: {extracted_jdk_path}")
            self.bundled_jdk_path = extracted_jdk_path  # Store the extracted path
            return extracted_jdk_path
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None

    def bundle_application(
        self, jar_path: str, app_name: str, output_dir: str = "."
    ) -> str:
        """Bundle Java application with JDK"""
        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"JAR file not found: {jar_path}")

        if not self.bundled_jdk_path:
            raise RuntimeError("OpenJDK must be downloaded and extracted first")

        app_name_clean = app_name.replace(" ", "-")

        print(f"📦 Bundling {app_name_clean} with OpenJDK {self.jdk_version}...")

        # Create temporary directory for bundling
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = os.path.join(temp_dir, f"{app_name_clean}-bundled")
            os.makedirs(bundle_dir, exist_ok=True)

            # Copy application JAR
            app_jar = os.path.join(bundle_dir, f"{app_name_clean}.jar")
            shutil.copy2(jar_path, app_jar)

            # Copy bundled JDK
            jdk_dest = os.path.join(bundle_dir, "jdk")
            shutil.copytree(self.bundled_jdk_path, jdk_dest)

            # Create custom start script
            start_script = self._create_bundled_start_script(
                app_name_clean, self.bundled_jdk_path
            )
            start_script_path = os.path.join(bundle_dir, "start.sh")
            with open(start_script_path, "w") as f:
                f.write(start_script)
            os.chmod(start_script_path, 0o755)

            # Create tarball
            bundle_filename = f"{app_name_clean}-bundled.tar.gz"
            bundle_path = os.path.join(output_dir, bundle_filename)

            with tarfile.open(bundle_path, "w:gz") as tar:
                # Add all files to tarball
                for _root, _dirs, files in os.walk(bundle_dir):
                    for file in files:
                        tar.add(file, arcname=os.path.relpath(file, bundle_dir))

            bundle_size = os.path.getsize(bundle_path)
            print(
                f"✅ Bundled application created: {bundle_filename} ({bundle_size // 1024 // 1024} MB)"
            )

            return bundle_path

    def _create_bundled_start_script(self, app_name: str, jdk_path: str) -> str:
        """Create startup script for bundled application"""
        app_name_clean = app_name.replace(" ", "-").lower()
        return f"""#!/bin/bash
# {app_name_clean} Application with Bundled OpenJDK {self.jdk_version}
set -e

echo "Starting {app_name_clean} with bundled Java..."
export JAVA_HOME="{jdk_path}"
export PATH="{jdk_path}/bin:$PATH"

exec "$JAVA_HOME/bin/java" -jar "$(dirname "$0")/{app_name_clean}.jar" "$@"
"""

    def get_bundled_jdk_path(self) -> str:
        """Get path to bundled JDK"""
        return self.bundled_jdk_path

    def bundle_java_for_appimage(self, java_dir: str, appimage_dir: str) -> bool:
        """Bundle Java into AppImage structure"""

        java_dir_path = Path(java_dir)
        appimage_java_dir = Path(appimage_dir) / "usr" / "java"

        appimage_java_dir.mkdir(parents=True, exist_ok=True)

        print(f"📋 Bundling Java into AppImage: {appimage_java_dir}")

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
                print(f"✅ Java bundled successfully: {java_binary}")
                return True
            else:
                print(f"❌ Java binary not found: {java_binary}")
                return False

        except Exception as e:
            print(f"❌ Failed to bundle Java: {e}")
            return False
