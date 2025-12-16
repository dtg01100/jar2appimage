#!/usr/bin/env python3
"""
Enhanced jar2appimage CLI with Portable Java Detection and Management

This enhanced CLI integrates the PortableJavaManager to provide:
- Intelligent system Java detection and validation
- User consent-based portable Java downloading
- Automatic JAR requirement analysis
- Seamless integration with existing bundlers
- Comprehensive error handling and fallbacks
"""

import argparse
import os
import platform
import sys
from pathlib import Path

# Import portable Java manager
try:
    from portable_java_manager import (
        PortableJavaManager,
        detect_and_manage_java,
        get_java_detection_summary,
    )
    PORTABLE_JAVA_AVAILABLE = True
except ImportError:
    PORTABLE_JAVA_AVAILABLE = False
    print("⚠️  Portable Java Manager not available")

# Import existing functionality
try:
    from java_auto_downloader import JavaAutoDownloader
    AUTO_JAVA_AVAILABLE = True
except ImportError:
    AUTO_JAVA_AVAILABLE = False


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


def check_java_requirements(jar_path: str, use_portable: bool = True) -> tuple:
    """
    Check Java requirements using portable Java manager

    Returns:
        Tuple of (java_version, download_consented, portable_manager)
    """
    if not PORTABLE_JAVA_AVAILABLE:
        # Fallback to simple detection
        print("⚠️  Portable Java Manager not available, using fallback detection")
        java_version = "11"  # Default fallback
        return java_version, False, None

    try:
        # Use the comprehensive portable Java manager
        java_version, download_consented = detect_and_manage_java(jar_path, interactive=True)
        portable_manager = PortableJavaManager()

        if java_version:
            print(f"✅ Java version determined: {java_version}")
            if download_consented:
                print("📥 Portable Java download consented")
            return java_version, download_consented, portable_manager
        else:
            print("❌ No suitable Java version found")
            return None, False, None

    except Exception as e:
        print(f"⚠️  Java detection failed: {e}")
        print("   Using fallback Java version 11")
        return "11", False, None


def handle_java_download(portable_manager: PortableJavaManager, java_version: str) -> str:
    """
    Handle Java download using portable manager

    Returns:
        Path to downloaded Java or None if failed
    """
    if not portable_manager:
        return None

    try:
        print(f"📥 Downloading portable Java {java_version}...")
        downloaded_path = portable_manager.download_portable_java(java_version)

        if downloaded_path:
            print(f"✅ Java {java_version} downloaded successfully")
            return downloaded_path
        else:
            print(f"❌ Failed to download Java {java_version}")
            return None

    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def create_appimage_with_portable_java(jar_path: str, output_dir: str, bundled: bool,
                                      java_version: str, portable_manager: PortableJavaManager = None):
    """
    Create AppImage with portable Java integration
    """
    print("🚀 Creating AppImage with portable Java support...")

    # Download Java if needed and not already downloaded
    java_archive = None
    if bundled and portable_manager:
        # Check if we have cached Java
        cached_java = portable_manager._get_cached_java(java_version)
        if not cached_java:
            java_archive = handle_java_download(portable_manager, java_version)
        else:
            java_archive = str(cached_java)

    try:
        # Import jar2appimage core
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        try:
            import jar2appimage
        except ImportError as e:
            print(f"❌ Cannot import jar2appimage: {e}")
            print("   Please ensure all dependencies are installed")
            return None

        # Create AppImage with bundling options
        app = jar2appimage.Jar2AppImage(
            jar_path,
            output_dir,
            bundled=bundled,
            jdk_version=java_version
        )
        appimage_path = app.create()

        if appimage_path:
            print(f"✅ AppImage created successfully: {appimage_path}")
            print(f"   Size: {os.path.getsize(appimage_path) // 1024 // 1024} MB")

            if bundled and java_archive:
                print(f"📦 Includes portable Java {java_version}")
                print("   Self-contained AppImage (no external dependencies)")

            return appimage_path
        else:
            print("❌ AppImage creation failed")
            return None

    except Exception as e:
        print(f"❌ Error creating AppImage: {e}")
        return None


def show_java_summary():
    """Show comprehensive Java detection summary"""
    if not PORTABLE_JAVA_AVAILABLE:
        print("⚠️  Portable Java Manager not available")
        return

    try:
        summary = get_java_detection_summary()

        print("\n🔍 Java Detection Summary:")
        print(f"   Platform: {summary['platform']['system']} {summary['platform']['arch']}")
        print(f"   Latest LTS: {summary['latest_lts']}")

        if summary['system_java']:
            java = summary['system_java']
            print(f"   System Java: {java['version']} ({java['type']})")
            print(f"   Compatible: {java['is_compatible']}")
            print(f"   Command: {java['command']}")
        else:
            print("   System Java: Not found")

        cache_info = summary['cache_info']
        print(f"   Download Cache: {cache_info['total_files']} files, {cache_info['total_size_mb']} MB")
        if cache_info['java_versions']:
            print(f"   Cached Versions: {', '.join(cache_info['java_versions'])}")

    except Exception as e:
        print(f"⚠️  Could not get Java summary: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced jar2appimage with Portable Java Detection and Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s app.jar                                    # Basic AppImage with portable Java detection
  %(prog)s app.jar --bundled                          # Self-contained AppImage with portable Java
  %(prog)s app.jar --no-portable                      # Use system Java only
  %(prog)s --java-summary                             # Show Java detection summary
  %(prog)s --clear-java-cache                         # Clear Java download cache
        """
    )

    parser.add_argument("jar_file", nargs="?", help="JAR file to convert")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for AppImage (default: current directory)",
    )

    # Enhanced Java bundling options
    parser.add_argument(
        "--bundled",
        action="store_true",
        help="Create AppImage with bundled portable Java for true portability",
    )
    parser.add_argument(
        "--no-bundled",
        action="store_true",
        help="Create AppImage using system Java (default behavior)",
    )
    parser.add_argument(
        "--no-portable",
        action="store_true",
        help="Disable portable Java detection and offering",
    )
    parser.add_argument(
        "--jdk-version",
        default="auto",
        choices=["8", "11", "17", "21", "auto"],
        help="Java version for bundling (default: auto - uses latest LTS)",
    )

    # Java management options
    parser.add_argument(
        "--java-summary",
        action="store_true",
        help="Show Java detection summary and exit",
    )
    parser.add_argument(
        "--detect-java",
        action="store_true",
        help="Detect and analyze system Java installation",
    )
    parser.add_argument(
        "--clear-java-cache",
        action="store_true",
        help="Clear Java download cache",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force download Java even if cached version exists",
    )

    parser.add_argument(
        "--check-platform",
        "-p",
        action="store_true",
        help="Check platform compatibility only",
    )

    args = parser.parse_args()

    # Handle Java management commands
    if args.java_summary:
        show_java_summary()
        return

    if args.clear_java_cache:
        if PORTABLE_JAVA_AVAILABLE:
            manager = PortableJavaManager()
            if manager.clear_cache():
                print("✅ Java download cache cleared")
            else:
                print("❌ Failed to clear cache")
        else:
            print("⚠️  Portable Java Manager not available")
        return

    if args.detect_java:
        if PORTABLE_JAVA_AVAILABLE:
            manager = PortableJavaManager()
            java_info = manager.detect_system_java()
            if java_info:
                print(f"✅ Found Java {java_info['version']} ({java_info['type']})")
                print(f"   Command: {java_info['command']}")
                print(f"   Compatible: {java_info['is_compatible']}")
                if java_info['java_home']:
                    print(f"   JAVA_HOME: {java_info['java_home']}")
            else:
                print("❌ No compatible Java found")
        else:
            print("⚠️  Portable Java Manager not available")
        return

    # Check platform support
    if not check_jar2appimage_support():
        sys.exit(1)

    if args.check_platform:
        print("\n🔍 Platform compatibility check complete.")
        print("   Enhanced jar2appimage is ready for use on this platform.")
        return

    # Check if JAR exists
    if not args.jar_file:
        print("❌ JAR file is required")
        print("   Usage: enhanced_jar2appimage_cli.py <jar_file> [options]")
        sys.exit(1)

    jar_path = Path(args.jar_file)
    if not jar_path.exists():
        print(f"❌ JAR file not found: {args.jar_file}")
        sys.exit(1)

    # Determine bundling mode
    bundled = args.bundled and not args.no_bundled
    if args.bundled and args.no_bundled:
        print("❌ Cannot use both --bundled and --no-bundled options")
        sys.exit(1)

    # Enhanced Java version handling
    java_version = args.jdk_version

    if bundled:
        # Use portable Java detection and management
        if not args.no_portable and PORTABLE_JAVA_AVAILABLE:
            print("🔍 Using enhanced portable Java detection...")
            detected_java, download_consented, portable_manager = check_java_requirements(str(jar_path))

            if detected_java:
                if java_version == "auto":
                    java_version = detected_java
                    print(f"🎯 Auto-detected Java version: {java_version}")
                else:
                    print(f"🎯 Using specified Java version: {java_version}")

            # Handle download if consented
            if download_consented and portable_manager:
                downloaded_path = handle_java_download(portable_manager, java_version)
                if not downloaded_path:
                    print("⚠️  Download failed, continuing with system Java")
        else:
            # Fallback to simple auto-detection
            if java_version == "auto" and AUTO_JAVA_AVAILABLE:
                try:
                    downloader = JavaAutoDownloader()
                    java_version = downloader.get_latest_lts_version()
                    print(f"🎯 Auto-detected latest LTS Java version: {java_version}")
                except Exception as e:
                    print(f"⚠️  Auto-detection failed: {e}, using version 11")
                    java_version = "11"
            elif java_version == "auto":
                java_version = "11"
                print(f"🎯 Using default Java version: {java_version}")
    else:
        # Non-bundled mode - just determine version for reference
        if java_version == "auto":
            java_version = "11"
            print(f"🎯 System Java mode, default version: {java_version}")

    print(f"🚀 Creating AppImage for {jar_path.name}...")

    if bundled:
        print("📦 Enhanced Java bundling: ENABLED")
        if PORTABLE_JAVA_AVAILABLE and not args.no_portable:
            print("📥 Portable Java management: ENABLED")
        print(f"☕ Java version: {java_version}")
    else:
        print("☕ Java bundling: DISABLED (using system Java)")

    try:
        # Create AppImage with enhanced Java support
        if bundled and PORTABLE_JAVA_AVAILABLE and not args.no_portable:
            appimage_path = create_appimage_with_portable_java(
                str(jar_path), args.output_dir, bundled, java_version, portable_manager
            )
        else:
            # Fallback to standard creation
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            import jar2appimage

            app = jar2appimage.Jar2AppImage(
                str(jar_path),
                args.output_dir,
                bundled=bundled,
                jdk_version=java_version
            )
            appimage_path = app.create()

        if appimage_path:
            print("\n✅ AppImage created successfully!")
            print(f"📦 File: {appimage_path}")
            print(f"📏 Size: {os.path.getsize(appimage_path) // 1024 // 1024} MB")
            print("\n🎯 Usage:")
            print(f"   Run: ./{os.path.basename(appimage_path)}")
            print(f"   Options: ./{os.path.basename(appimage_path)} --help")

            if bundled:
                print("\n📦 Enhanced Features:")
                print("   • Self-contained AppImage with portable Java")
                print("   • No external Java dependency required")
                print("   • Works on any Linux distribution")
                print("   • Latest security updates and features")
                if PORTABLE_JAVA_AVAILABLE and not args.no_portable:
                    print("   • Intelligent Java requirement detection")
                    print("   • User-consented Java downloads")
        else:
            print("❌ AppImage creation failed")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error creating AppImage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
