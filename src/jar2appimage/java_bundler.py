"""Java Runtime Manager with Java bundling support"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class JavaBundler:
    """Bundles OpenJDK with Java applications for self-contained AppImages"""

    def __init__(self, jdk_version: str = "11"):
        self.jdk_version = jdk_version
        self.bundled_jdk_path = None

    def download_opensdk(self, output_dir: str = ".") -> str:
        """Download OpenJDK for bundling"""
        jdk_arch = "x64_linux"
        jdk_version_clean = self.jdk_version.replace("+", "_")

        # Common OpenJDK download URLs
        jdk_urls = {
            "11": "https://github.com/adoptium/temurin11-jdk{jdk_version_clean}.tar.gz",
            "17": "https://github.com/adoptium/temurin17-jdk{jdk_version_clean}.tar.gz",
            "21": "https://github.com/adoptium/temurin21-jdk{jdk_version_clean}.tar.gz",
        }

        jdk_url = jdk_urls.get(self.jdk_version, jdk_urls.get("11"))
        if not jdk_url:
            raise ValueError(f"Unsupported OpenJDK version: {self.jdk_version}")

        jdk_filename = f"openjdk-{self.jdk_version}-{jdk_arch}.tar.gz"
        jdk_path = os.path.join(output_dir, jdk_filename)

        print(f"🔍 Downloading OpenJDK {self.jdk_version} ({jdk_arch})...")

        try:
            subprocess.run(
                ["curl", "-L", "-f", "-#", "-o", jdk_path, jdk_url],
                check=True,
                capture_output=True,
                text=True,
            )

            if os.path.exists(jdk_path):
                file_size = os.path.getsize(jdk_path)
                print(
                    f"✅ OpenJDK {self.jdk_version} downloaded: {jdk_filename} ({file_size // 1024 // 1024} MB)"
                )
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
                for root, dirs, files in os.walk(bundle_dir):
                    for file in files:
                        tar.add(file, arcname=os.path.relpath(file, bundle_dir))

            bundle_size = os.path.getsize(bundle_path)
            print(
                f"✅ Bundled application created: {bundle_filename} ({bundle_size // 1024 // 1024} MB)"
            )

            return bundle_path
