#!/usr/bin/env python3
"""
jar2appimage CLI with platform detection and limitations
"""

import argparse
import os
import platform
import sys
from pathlib import Path


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


def main():

    parser = argparse.ArgumentParser(
        description="Create AppImages from JAR files (Linux only)\n\n"
                    "Examples:\n"
                    "  jar2appimage myapp.jar --output-dir out\n"
                    "  jar2appimage myapp.jar --bundled --jdk-version 17 --output-dir out\n",
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
        help="Bundle a Java runtime (OpenJDK) inside the AppImage (default: use system Java)",
    )
    parser.add_argument(
        "--jdk-version",
        default="11",
        help="OpenJDK version to bundle (default: 11). Only used with --bundled.",
    )
    parser.add_argument(
        "--check-platform",
        "-p",
        action="store_true",
        help="Check platform compatibility only",
    )

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

    print(f"🚀 Creating AppImage for {jar_path.name}...\n   Bundled Java: {'Yes' if args.bundled else 'No'}   JDK Version: {args.jdk_version if args.bundled else 'N/A'}")

    try:
        # Import jar2appimage (with error handling for import issues)
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        try:
            import jar2appimage
        except ImportError as e:
            print(f"❌ Cannot import jar2appimage: {e}")
            print("   Please ensure all dependencies are installed:")
            print("     • Python 3.7+")
            print("     • Required Python packages (click, requests, etc.)")
            sys.exit(1)

        # Create AppImage
        app = jar2appimage.Jar2AppImage(str(jar_path), args.output_dir, bundled=args.bundled, jdk_version=args.jdk_version)
        appimage_path = app.create()

        print(f"✅ AppImage created successfully: {appimage_path}")
        print(f"   Size: {os.path.getsize(appimage_path) // 1024 // 1024} MB")
        print()
        print("🎯 Usage:")
        print(f"   Run: ./{os.path.basename(appimage_path)}")
        print(f"   Options: ./{os.path.basename(appimage_path)} --help")

    except Exception as e:
        print(f"❌ Error creating AppImage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
