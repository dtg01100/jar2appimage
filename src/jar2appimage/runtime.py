"""Java runtime management"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class JavaRuntimeManager:
    """Manages Java runtime environments"""

    def __init__(self) -> None:
        import os
        import uuid
        build_root = Path(os.getcwd()) / "jar2appimage_build"
        build_root.mkdir(exist_ok=True)
        self.temp_dir = build_root / f"java_runtime_{uuid.uuid4().hex[:8]}"
        self.temp_dir.mkdir(exist_ok=True)
        print(f"[DEBUG] Created JavaRuntimeManager temp_dir: {self.temp_dir}")

    def cleanup(self) -> None:
        """Clean up temporary directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def get_system_java(self) -> Optional[Path]:
        """Get system Java path if available"""
        java_cmd = shutil.which("java")
        if java_cmd:
            return Path(java_cmd)
        return None

    def get_runtime(self, version: str = "11") -> Optional[str]:
        """Get Java runtime for specified version"""
        # First try to find system Java
        java_cmd = shutil.which("java")
        if java_cmd:
            print(f"✅ Found Java runtime: {java_cmd}")
            return java_cmd

        print("❌ Java runtime not found in PATH")
        return None

    def check_java_availability(self, java_cmd: Optional[str]) -> Tuple[bool, str]:
        """Check if Java is available and working"""
        if not java_cmd:
            java_cmd = shutil.which("java")

        if not java_cmd:
            return (
                False,
                "Java not found. Install Java JRE/JDK (version 11+).",
            )

        try:
            # Test if Java is executable and returns version
            result = subprocess.run(
                [java_cmd, "-version"], capture_output=False, timeout=10
            )
            if result.returncode == 0:
                # Get version info separately to avoid output capture issues
                version_result = subprocess.run(
                    [java_cmd, "-version"],
                    capture_output=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                    timeout=5,
                )
                version_info = (
                    version_result.stdout.strip()
                    if version_result.stdout
                    else "Unknown"
                )
                print(f"✅ Java runtime working: {java_cmd}")
                print(f"   Version: {version_info}")
                return True, f"✅ Java available: {java_cmd} ({version_info})"
            else:
                return False, f"❌ Java found but not working: {java_cmd}"
        except subprocess.TimeoutExpired:
            return False, f"❌ Java command timed out: {java_cmd}"
        except FileNotFoundError:
            return False, f"❌ Java executable not found: {java_cmd}"
        except Exception as e:
            return False, f"❌ Java check failed: {e}"

    def get_runtime_with_fallback(self, version: str = "11") -> Optional[str]:
        """Get Java runtime with comprehensive error handling"""
        java_cmd = self.get_runtime(version)

        if java_cmd is None:
            # Check common installation paths
            common_paths = [
                f"/usr/lib/jvm/java-{version}-openjdk/bin/java",
                f"/usr/lib/jvm/java-{version}/bin/java",
                f"/opt/java-{version}/bin/java",
                "/usr/local/java/bin/java",
                "/usr/local/bin/java",
                "/usr/bin/java",
                "/bin/java",
                "/usr/lib/jvm/default-java/bin/java",
            ]

            for path in common_paths:
                if os.path.exists(path):
                    print(f"✅ Found Java runtime: {path}")
                    return path

            # If still not found, provide installation help
            print("❌ No Java runtime found on system.")
            print("   Please install Java 11 or later:")
            print("   - Ubuntu/Debian: sudo apt install openjdk-11-jre")
            print("   - RHEL/CentOS: sudo yum install java-11-openjdk")
            print("   - Arch: sudo pacman -S jdk11-openjdk")
            print("   - Homebrew: brew install openjdk@11")
            print("   - Download: https://adoptium.net/")
            return None

        # Verify Java is actually working
        is_available, message = self.check_java_availability(java_cmd)
        if not is_available:
            print(f"❌ Java runtime check failed: {message}")
            return None

        return java_cmd

    def get_system_java_version(self) -> str:
        """Get the version of system Java"""
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Java version unknown: {e}"

    def get_java_version(self) -> str:
        """Get the version of system Java"""
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            return result.stdout
        except Exception:
            return "Java version unknown"


# Import os here since it's used in get_runtime
