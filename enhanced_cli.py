#!/usr/bin/env python3
"""
Enhanced jar2appimage CLI with all advanced features
"""

import os
import sys
import argparse
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from jar2appimage.core import Jar2AppImage
    from jar2appimage.java_bundler import JavaBundler
    from config_manager import ConfigManager, auto_discover_config
    from appimage_validator import validate_appimage
    from cli_helper import show_help
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert JAR files to AppImage executables with advanced features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument("jar_file", help="JAR file to convert")

    # Basic options
    parser.add_argument("--name", "-n", help="Application name")
    parser.add_argument(
        "--output-dir", "-o", default=".", help="Output directory (default: current)"
    )
    parser.add_argument(
        "--main-class", "-m", help="Main class (auto-detected if not specified)"
    )
    parser.add_argument("--icon", help="Icon file for the application")
    parser.add_argument(
        "--category", default="Utility", help="Desktop category (default: Utility)"
    )

    # Advanced options
    parser.add_argument(
        "--bundled", action="store_true", help="Bundle Java runtime inside AppImage"
    )
    parser.add_argument(
        "--java-version", default="11", help="Java version for bundling (default: 11)"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate the created AppImage"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    # Configuration
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--save-config", help="Save configuration to file")

    # Help and utilities
    parser.add_argument(
        "--help-detailed", action="store_true", help="Show detailed help"
    )
    parser.add_argument("--examples", action="store_true", help="Show usage examples")
    parser.add_argument(
        "--troubleshooting", action="store_true", help="Show troubleshooting guide"
    )

    args = parser.parse_args()

    # Handle help requests
    if args.help_detailed:
        show_help("detailed")
        return 0
    elif args.examples:
        show_help("examples")
        return 0
    elif args.troubleshooting:
        show_help("troubleshooting")
        return 0

    # Check JAR file exists
    if not os.path.exists(args.jar_file):
        print(f"❌ JAR file not found: {args.jar_file}")
        return 1

    try:
        # Load configuration
        config_manager = ConfigManager()

        # Try to auto-discover config if none specified
        if not args.config:
            auto_config = auto_discover_config()
            if auto_config:
                print(f"📋 Using auto-discovered configuration")
        elif args.config:
            try:
                config = config_manager.load_config(args.config)
                print(f"📋 Loaded configuration from: {args.config}")
            except Exception as e:
                print(f"⚠️  Failed to load config: {e}")

        # Create Jar2AppImage instance
        print(f"🚀 Creating AppImage for: {args.jar_file}")

        jar2app = Jar2AppImage(
            jar_file=args.jar_file, output_dir=args.output_dir, bundled=args.bundled
        )

        # Set options
        if args.name:
            jar2app.set_app_name(args.name)
        if args.main_class:
            jar2app.set_main_class(args.main_class)
        if args.icon:
            jar2app.set_icon(args.icon)
        if args.category:
            jar2app.set_category(args.category)

        # Create AppImage
        if args.verbose:
            print("🔧 Configuration:")
            print(f"  Application: {jar2app._app_name}")
            print(f"  Main Class: {jar2app._main_class}")
            print(f"  Output Dir: {args.output_dir}")
            print(f"  Bundled Java: {args.bundled}")
            if args.bundled:
                print(f"  Java Version: {args.java_version}")

        appimage_path = jar2app.create()

        if appimage_path and os.path.exists(appimage_path):
            print(f"✅ AppImage created successfully: {appimage_path}")

            # Validate if requested
            if args.validate:
                print(f"🔍 Validating AppImage...")
                validation_success = validate_appimage(appimage_path)
                if validation_success:
                    print(f"✅ AppImage validation passed!")
                else:
                    print(f"⚠️  AppImage validation had issues (see report)")

            # Save config if requested
            if args.save_config:
                config_data = {
                    "name": jar2app._app_name,
                    "jar_path": args.jar_file,
                    "main_class": jar2app._main_class,
                    "icon": args.icon,
                    "category": args.category,
                    "bundled_java": args.bundled,
                    "java_version": args.java_version if args.bundled else None,
                    "output_dir": args.output_dir,
                }

                # Create a config object
                from config_manager import AppImageConfig

                config_obj = AppImageConfig(**config_data)
                config_manager.save_config(args.save_config, config_obj)

            return 0
        else:
            print("❌ Failed to create AppImage")
            return 1

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
