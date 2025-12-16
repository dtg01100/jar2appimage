#!/usr/bin/env python3
"""
Smart Java bundler for jar2appimage - Automatically discovers and downloads OpenJDK
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional


class SmartJavaBundler:
    """Smart Java bundler that automatically discovers and downloads OpenJDK releases"""

    def __init__(self, java_version: str = "17", use_jre: bool = True):
        self.java_version = java_version
        self.use_jre = use_jre  # Use JRE (smaller) vs JDK (full)
        self.bundled_java_path = None
        self.cache = {}  # Cache for API responses

    def _find_java_download_url(self) -> Optional[str]:
        """Find the correct OpenJDK download URL for the specified version"""

        print(
            f"🔍 Finding Java {self.java_version} {'JRE' if self.use_jre else 'JDK'} download URL..."
        )

        # Try GitHub API first with proper headers
        try:
            repo = f"adoptium/temurin{self.java_version}-binaries"
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"

            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                },
            )

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            # Find the right asset for Linux x64
            package_type = "jre" if self.use_jre else "jdk"
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if (
                    f"{package_type}_x64_linux" in name
                    and name.endswith(".tar.gz")
                    and "hotspot" in name
                ):
                    download_url = asset.get("browser_download_url")
                    print(f"✅ Found {package_type.upper()}: {name}")
                    return download_url

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            json.JSONDecodeError,
        ) as e:
            print(f"⚠️  GitHub API failed: {e}")

        # Fallback to manual URL construction for common versions
        return self._get_fallback_url()

    def _extract_download_url(self, release_info: Dict) -> Optional[str]:
        """Extract the correct download URL from GitHub release info"""
        assets = release_info.get("assets", [])

        # Determine what we're looking for
        package_type = "jre" if self.use_jre else "jdk"
        arch = "x64_linux"
        os_name = "linux"
        archive_type = "tar.gz"

        # Build filename pattern
        filename_patterns = [
            f"OpenJDK{self.java_version}U-{package_type}_{arch}_{os_name}_hotspot_.*\\.{archive_type}",
            f"OpenJDK{self.java_version}U-{package_type}_{arch}_{os_name}_.*\\.{archive_type}",
            f"OpenJDK{self.java_version}U-{package_type}_x64_{os_name}_hotspot_.*\\.{archive_type}",
            f"OpenJDK{self.java_version}U-{package_type}_x64_{os_name}_.*\\.{archive_type}",
        ]

        for asset in assets:
            name = asset.get("name", "")
            download_url = asset.get("browser_download_url", "")

            for pattern in filename_patterns:
                if re.match(pattern, name):
                    print(f"✅ Found matching asset: {name}")
                    return download_url

        return None

    def _get_fallback_url(self) -> Optional[str]:
        """Fallback URLs for common Java versions"""
        fallbacks = {
            "8": {
                "jre": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jre_x64_linux_hotspot_8u412b08.tar.gz",
                "jdk": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u412-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u412b08.tar.gz",
            },
            "11": {
                "jre": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jre_x64_linux_hotspot_11.0.23_9.tar.gz",
                "jdk": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jdk_x64_linux_hotspot_11.0.23_9.tar.gz",
            },
            "17": {
                "jre": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jre_x64_linux_hotspot_17.0.12_7.tar.gz",
                "jdk": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz",
            },
            "21": {
                "jre": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jre_x64_linux_hotspot_21.0.4_7.tar.gz",
                "jdk": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_linux_hotspot_21.0.4_7.tar.gz",
            },
        }

        package_type = "jre" if self.use_jre else "jdk"
        version_fallbacks = fallbacks.get(self.java_version, {})

        if package_type in version_fallbacks:
            url = version_fallbacks[package_type]
            print(
                f"📋 Using fallback URL for Java {self.java_version} {package_type}: {url}"
            )
            return url

        print(f"❌ No download URL found for Java {self.java_version} {package_type}")
        return None

    def download_java(self, output_dir: str = ".") -> Optional[str]:
        """Download the appropriate Java runtime"""

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        print(
            f"🔍 Finding Java {self.java_version} {'JRE' if self.use_jre else 'JDK'} download..."
        )

        download_url = self._find_java_download_url()
        if not download_url:
            print(f"❌ Could not find download URL for Java {self.java_version}")
            return None

        # Extract filename from URL
        filename = download_url.split("/")[-1]
        java_path = output_dir_path / filename

        print(f"📥 Downloading: {filename}")
        print(f"   URL: {download_url}")

        try:
            # Use curl for reliable downloads
            subprocess.run(
                ["curl", "-L", "--progress-bar", "-o", str(java_path), download_url],
                check=True,
                capture_output=True,
                text=True,
            )

            if java_path.exists():
                size_mb = java_path.stat().st_size // (1024 * 1024)
                print(
                    f"✅ Java {self.java_version} downloaded: {filename} ({size_mb} MB)"
                )
                return str(java_path)
            else:
                print("❌ Download completed but file not found")
                return None

        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def extract_java(self, java_archive: str, extract_dir: str) -> Optional[str]:
        """Extract Java archive to directory"""

        extract_dir_path = Path(extract_dir)
        extract_dir_path.mkdir(parents=True, exist_ok=True)

        print("📦 Extracting Java archive...")

        try:
            with tarfile.open(java_archive, "r:gz") as tar:
                # Extract to temp directory first to find the actual JDK/JRE directory
                temp_extract = extract_dir_path / "temp_java"
                temp_extract.mkdir(exist_ok=True)

                tar.extractall(temp_extract)

                # Fix permissions after extraction
                for root, dirs, files in os.walk(temp_extract):
                    os.chmod(root, 0o755)
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)

            # Find the actual Java directory (usually jdk-* or jre-*)
            java_dir = None
            for item in temp_extract.iterdir():
                if item.is_dir() and (
                    item.name.startswith("jdk-") or item.name.startswith("jre-")
                ):
                    java_dir = item
                    break

            if not java_dir:
                print("❌ Could not find Java directory after extraction")
                return None

            # Move to final location
            final_java_dir = extract_dir_path / java_dir.name
            if final_java_dir.exists():
                shutil.rmtree(final_java_dir)

            java_dir.rename(final_java_dir)

            # Clean up temp directory
            shutil.rmtree(temp_extract, ignore_errors=True)

            print(f"✅ Java extracted to: {final_java_dir}")
            return str(final_java_dir)

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None

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


# Utility functions for easy use
def download_java_runtime(
    java_version: str = "17", use_jre: bool = True, output_dir: str = "."
) -> Optional[str]:
    """Convenient function to download Java runtime"""
    bundler = SmartJavaBundler(java_version, use_jre)
    return bundler.download_java(output_dir)


def get_java_download_url(
    java_version: str = "17", use_jre: bool = True
) -> Optional[str]:
    """Get the download URL for a Java version without downloading"""
    bundler = SmartJavaBundler(java_version, use_jre)
    return bundler._find_java_download_url()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smart Java bundler for jar2appimage")
    parser.add_argument(
        "--version", "-v", default="17", help="Java version to download (default: 17)"
    )
    parser.add_argument(
        "--jdk", action="store_true", help="Download JDK instead of JRE"
    )
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument(
        "--url-only", action="store_true", help="Only show download URL, don't download"
    )

    args = parser.parse_args()

    if args.url_only:
        url = get_java_download_url(args.version, not args.jdk)
        if url:
            print(url)
        else:
            print(f"❌ Could not find URL for Java {args.version}", file=sys.stderr)
            sys.exit(1)
    else:
        archive_path = download_java_runtime(args.version, not args.jdk, args.output)
        if archive_path:
            print(f"✅ Downloaded: {archive_path}")
        else:
            print(f"❌ Failed to download Java {args.version}", file=sys.stderr)
            sys.exit(1)
