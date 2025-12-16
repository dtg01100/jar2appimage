#!/usr/bin/env python3
"""
jar2appimage CLI with automatic Java downloads and bundling support
"""

import argparse
import os
import platform
import sys
from pathlib import Path

# Import automatic Java downloader
try:
    from java_auto_downloader import JavaAutoDownloader
    AUTO_JAVA_AVAILABLE = True
except ImportError:
    AUTO_JAVA_AVAILABLE = False
    print("⚠️  Automatic Java downloader not available")


def detect_platform():
    """Detect current platform and capabilities"""
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


def check_jar2appimage_support():
    """Check if jar2appimage supports current platform"""
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

        return False

    print(f"✅ {platform_info['system']} supports jar2appimage AppImage creation")
    return True


def get_auto_java_version():
    """Get the automatically detected latest LTS Java version"""
    if not AUTO_JAVA_AVAILABLE:
        return "11"  # Fallback to hardcoded version

    try:
        downloader = JavaAutoDownloader()
        return downloader.get_latest_lts_version()
    except Exception as e:
        print(f"⚠️  Auto-detection failed: {e}, using fallback version 11")
        return "11"


def auto_download_java(output_dir: str = ".", java_version: str = None):
    """Automatically download Java if needed"""
    if not AUTO_JAVA_AVAILABLE or not java_version:
        return None

    try:
        downloader = JavaAutoDownloader()
        return downloader.auto_download_java(output_dir, java_version)
    except Exception as e:
        print(f"⚠️  Auto-download failed: {e}")
        return None


def _setup_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Create AppImages from JAR files (Linux only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("jar_file", help="JAR file to convert")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for AppImage (default: current directory)",
    )
    parser.add_argument(
        "--bundled",
        action="store_true",
        help="Create AppImage with bundled OpenJDK for true portability",
    )
    parser.add_argument(
        "--no-bundled",
        action="store_true",
        help="Create AppImage using system Java (default behavior)",
    )
    parser.add_argument(
        "--jdk-version",
        default="auto",
        choices=["8", "11", "17", "21", "auto"],
        help="OpenJDK version for bundling (default: auto - uses latest LTS)",
    )
    parser.add_argument(
        "--check-platform",
        "-p",
        action="store_true",
        help="Check platform compatibility only",
    )
    return parser


def _validate_bundling_options(bundled: bool, no_bundled: bool) -> bool:
    """Validate bundling options."""
    if bundled and no_bundled:
        print("❌ Cannot use both --bundled and --no-bundled options")
        return False
    return True


def _get_java_version(bundled: bool, jdk_version: str) -> str:
    """Determine which Java version to use."""
    if not bundled:
        return jdk_version

    if jdk_version == "auto":
        java_version = get_auto_java_version()
        print(f"🎯 Auto-detected latest LTS Java version: {java_version}")
        return java_version

    print(f"🎯 Using specified Java version: {jdk_version}")
    return jdk_version


def _prepare_bundled_java(bundled: bool, java_version: str, output_dir: str) -> None:
    """Prepare bundled Java if needed."""
    if not bundled:
        print("☕ Java bundling: DISABLED (using system Java)")
        return

    print(f"📦 Java bundling: ENABLED (OpenJDK {java_version})")
    print(f"📥 Checking for Java {java_version} availability...")
    downloaded_java = auto_download_java(output_dir, java_version)
    if downloaded_java:
        print(f"✅ Java {java_version} ready for bundling")
    else:
        print("⚠️  Java download failed, bundling may fail")


def _create_appimage(jar_path: Path, output_dir: str, bundled: bool, java_version: str) -> str:
    """Create the AppImage."""
    sys.path.insert(0, str(Path(__file__).parent / "src"))

    try:
        import jar2appimage
    except ImportError as e:
        print(f"❌ Cannot import jar2appimage: {e}")
        print("   Please ensure all dependencies are installed:")
        print("     • Python 3.7+")
        print("     • Required Python packages (click, requests, etc.)")
        sys.exit(1)

    app = jar2appimage.Jar2AppImage(
        str(jar_path),
        output_dir,
        bundled=bundled,
        jdk_version=java_version
    )
    return app.create()


def _print_success_info(appimage_path: str, bundled: bool, jdk_version: str) -> None:
    """Print success information."""
    print(f"✅ AppImage created successfully: {appimage_path}")
    print(f"   Size: {os.path.getsize(appimage_path) // 1024 // 1024} MB")
    print()
    print("🎯 Usage:")
    print(f"   Run: ./{os.path.basename(appimage_path)}")
    print(f"   Options: ./{os.path.basename(appimage_path)} --help")

    if bundled:
        print()
        print("📦 Java Bundling Features:")
        print("   • Self-contained AppImage with bundled OpenJDK")
        print("   • No external Java dependency required")
        print("   • Works on any Linux distribution")
        print("   • Professional enterprise deployment")
        if jdk_version == "auto":
            print("   • Automatic latest LTS Java version detection")


def main():
    parser = _setup_parser()
    args = parser.parse_args()

    # Check platform support
    if not check_jar2appimage_support():
        sys.exit(1)

    if args.check_platform:
        print("\n🔍 Platform compatibility check complete.")
        print("   jar2appimage is ready for use on this platform.")
        return

    # Check if JAR exists
    jar_path = Path(args.jar_file)
    if not jar_path.exists():
        print(f"❌ JAR file not found: {args.jar_file}")
        sys.exit(1)

    # Determine bundling mode
    bundled = args.bundled and not args.no_bundled
    if not _validate_bundling_options(args.bundled, args.no_bundled):
        sys.exit(1)

    # Get Java version
    java_version = _get_java_version(bundled, args.jdk_version)

    print(f"🚀 Creating AppImage for {jar_path.name}...")
    _prepare_bundled_java(bundled, java_version, args.output_dir)

    try:
        appimage_path = _create_appimage(jar_path, args.output_dir, bundled, java_version)
        _print_success_info(appimage_path, bundled, java_version)
    except Exception as e:
        print(f"❌ Error creating AppImage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
