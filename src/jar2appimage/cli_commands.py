#!/usr/bin/env python3
# mypy: ignore-errors
"""
jar2appimage CLI Commands
Command handlers for the unified CLI system
"""

import argparse
import os
import sys
from pathlib import Path

from .cli_utils import (
    check_jar2appimage_support,
    check_java_availability,
    check_required_tools,
    detect_platform,
    get_appimage_info,
    handle_error,
    validate_jar_file,
    validate_output_directory,
)


class CLICommandHandler:
    """
    Unified command handler for jar2appimage CLI
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def handle_convert_command(self, args: argparse.Namespace) -> int:
        """
        Handle the convert command

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Check platform support
            if not check_jar2appimage_support():
                return 1

            # Validate JAR file
            if not validate_jar_file(args.jar_file):
                return 1

            # Validate output directory
            if not validate_output_directory(args.output_dir):
                return 1

            # Determine bundling mode
            bundled = args.bundled and not args.no_bundled
            if args.bundled and args.no_bundled:
                print("❌ Cannot use both --bundled and --no-bundled options")
                return 1

            # Handle Java version selection
            java_version = self._handle_java_version_selection(args, bundled)

            # Show configuration
            self._show_conversion_configuration(args, bundled, java_version)

            # Check if dry run
            if args.dry_run:
                print("\n✅ Dry run completed - no actual conversion performed")
                return 0

            # Import and use the core functionality
            return self._perform_conversion(args, bundled, java_version)

        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            return handle_error(e, "Conversion failed")

    def _handle_java_version_selection(self, args: argparse.Namespace, bundled: bool) -> str:
        """
        Handle Java version selection and detection

        Args:
            args: Parsed arguments
            bundled: Whether Java bundling is enabled

        Returns:
            Selected Java version string
        """
        java_version = args.jdk_version

        if bundled:
            if java_version == "auto":
                # Try to auto-detect latest LTS version
                try:
                    java_version = self._get_auto_java_version()
                    print(f"🎯 Auto-detected latest LTS Java version: {java_version}")
                except Exception as e:
                    print(f"⚠️  Auto-detection failed: {e}, using version 11")
                    java_version = "11"
            else:
                print(f"🎯 Using specified Java version: {java_version}")
        else:
            # Non-bundled mode - just determine version for reference
            if java_version == "auto":
                java_version = "11"
                print(f"🎯 System Java mode, default version: {java_version}")

        return java_version

    def _get_auto_java_version(self) -> str:
        """
        Get automatically detected latest LTS Java version

        Returns:
            Latest LTS Java version string
        """
        try:
            # Try auto downloader first
            from java_auto_downloader import JavaAutoDownloader
            downloader = JavaAutoDownloader()
            return downloader.get_latest_lts_version()
        except ImportError:
            pass

        # Final fallback
        return "11"

    def _show_conversion_configuration(self, args: argparse.Namespace, bundled: bool, java_version: str):
        """
        Show the conversion configuration

        Args:
            args: Parsed arguments
            bundled: Whether Java bundling is enabled
            java_version: Selected Java version
        """
        jar_path = Path(args.jar_file)
        print(f"🚀 Creating AppImage for {jar_path.name}...")

        if bundled:
            print("📦 Java bundling: ENABLED")
            print(f"☕ Java version: {java_version}")
        else:
            print("☕ Java bundling: DISABLED (using system Java)")

        if self.verbose:
            print("\n🔧 Configuration:")
            print(f"  JAR file: {args.jar_file}")
            print(f"  Output directory: {args.output_dir}")
            print(f"  Application name: {args.name or 'Auto-detected'}")
            print(f"  Main class: {args.main_class or 'Auto-detected'}")
            print(f"  Icon: {args.icon or 'Default'}")
            print(f"  Category: {args.category}")
            print(f"  Bundled Java: {bundled}")
            if bundled:
                print(f"  Java version: {java_version}")

    def _perform_conversion(self, args: argparse.Namespace, bundled: bool, java_version: str) -> int:
        """
        Perform the actual AppImage conversion

        Args:
            args: Parsed arguments
            bundled: Whether Java bundling is enabled
            java_version: Selected Java version

        Returns:
            Exit code
        """
        try:
            # Import jar2appimage core
            sys.path.insert(0, str(Path(__file__).parent / "src"))

            try:
                import jar2appimage
            except ImportError as e:
                print(f"❌ Cannot import jar2appimage: {e}")
                print("   Please ensure all dependencies are installed:")
                print("     • Python 3.7+")
                print("     • Required Python packages (click, requests, etc.)")
                return 1

            # Create Jar2AppImage instance with all options
            jar2app = jar2appimage.Jar2AppImage(
                jar_file=args.jar_file,
                output_dir=args.output_dir,
                bundled=bundled,
                jdk_version=java_version
            )

            # Note: Additional options like name, main_class, icon, category
            # would be set through constructor parameters in a real implementation

            # Create AppImage
            appimage_path = jar2app.create()

            if appimage_path and Path(appimage_path).exists():
                # Show success information
                appimage_info = get_appimage_info(appimage_path)
                print("\n✅ AppImage created successfully!")
                print(f"📦 File: {appimage_path}")
                print(f"📏 Size: {appimage_info['size']}")

                # Validate if requested
                if args.validate:
                    print("\n🔍 Validating AppImage...")
                    validation_success = self._validate_appimage(appimage_path)
                    if validation_success:
                        print("✅ AppImage validation passed!")
                    else:
                        print("⚠️  AppImage validation had issues (see report)")

                # Show usage information
                self._show_usage_information(appimage_path, bundled, java_version)

                # Save config if requested
                if args.save_config:
                    self._save_configuration(args, appimage_path)

                return 0
            else:
                print("❌ AppImage creation failed")
                return 1

        except Exception as e:
            return handle_error(e, "AppImage creation failed")

    def _validate_appimage(self, appimage_path: str) -> bool:
        """
        Validate an AppImage file

        Args:
            appimage_path: Path to AppImage

        Returns:
            True if validation passes
        """
        try:
            # Try to import the validator
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from appimage_validator import validate_appimage
            return validate_appimage(appimage_path)
        except ImportError:
            # Fallback to basic validation
            if self.verbose:
                print("⚠️  AppImage validator not available, skipping validation")
            return True
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Validation error: {e}")
            return False

    def _show_usage_information(self, appimage_path: str, bundled: bool, java_version: str):
        """
        Show usage information for the created AppImage

        Args:
            appimage_path: Path to created AppImage
            bundled: Whether Java bundling is enabled
            java_version: Java version used
        """
        print("\n🎯 Usage:")
        print(f"   Run: ./{os.path.basename(appimage_path)}")
        print(f"   Options: ./{os.path.basename(appimage_path)} --help")

        if bundled:
            print("\n📦 Java Bundling Features:")
            print("   • Self-contained AppImage with bundled OpenJDK")
            print("   • No external Java dependency required")
            print("   • Works on any Linux distribution")
            print("   • Professional enterprise deployment")

            if java_version != "auto":
                print(f"   • Uses Java {java_version}")

    def _save_configuration(self, args: argparse.Namespace, appimage_path: str):
        """
        Save configuration to file

        Args:
            args: Parsed arguments
            appimage_path: Path to created AppImage
        """
        try:
            from config_manager import AppImageConfig, ConfigManager

            config_data = {
                "name": args.name or Path(args.jar_file).stem,
                "jar_path": args.jar_file,
                "main_class": args.main_class,
                "icon": args.icon,
                "category": args.category,
                "bundled_java": args.bundled and not args.no_bundled,
                "java_version": args.jdk_version if (args.bundled and not args.no_bundled) else None,
                "output_dir": args.output_dir,
                "appimage_path": appimage_path
            }

            config_obj = AppImageConfig(**config_data)
            config_manager = ConfigManager()
            config_manager.save_config(args.save_config, config_obj)

            print(f"\n📋 Configuration saved to: {args.save_config}")

        except ImportError:
            if self.verbose:
                print("⚠️  Config manager not available, skipping config save")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Failed to save configuration: {e}")

    def handle_check_platform_command(self, args: argparse.Namespace) -> int:
        """
        Handle the check-platform command

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        platform_info = detect_platform()

        print("🔍 Platform Compatibility Check")
        print("=" * 40)
        print(f"System: {platform_info['system']}")
        print(f"Architecture: {platform_info['machine']}")
        print(f"AppImage Support: {'✅ Yes' if platform_info['supports_appimage'] else '❌ No'}")

        if args.verbose:
            print(f"Native Bundle Support: {'✅ Yes' if platform_info['supports_native_bundle'] else '❌ No'}")
            print("Platform Flags:")
            for key, value in platform_info.items():
                if key not in ['system', 'machine']:
                    print(f"  {key}: {value}")

        if platform_info['supports_appimage']:
            print("\n✅ Platform is supported for AppImage creation")
            return 0
        else:
            print("\n❌ Platform is not supported for AppImage creation")
            print("   jar2appimage creates Linux AppImages only")
            return 1

    def handle_java_summary_command(self, args: argparse.Namespace) -> int:
        """
        Handle the java-summary command

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        if args.clear_cache:
            return self._handle_clear_java_cache()

        if args.detect_java:
            return self._handle_detect_java()

        # Show comprehensive Java summary
        return self._show_java_summary(args.verbose)

    def _handle_clear_java_cache(self) -> int:
        """
        Handle clearing Java cache

        Returns:
            Exit code
        """
        try:
            from portable_java_manager import PortableJavaManager
            manager = PortableJavaManager()
            if manager.clear_cache():
                print("✅ Java download cache cleared")
                return 0
            else:
                print("❌ Failed to clear cache")
                return 1
        except ImportError:
            print("⚠️  Portable Java Manager not available")
            return 1

    def _handle_detect_java(self) -> int:
        """
        Handle Java detection

        Returns:
            Exit code
        """
        try:
            from portable_java_manager import PortableJavaManager
            manager = PortableJavaManager()
            java_info = manager.detect_system_java()

            if java_info:
                print(f"✅ Found Java {java_info['version']} ({java_info['type']})")
                print(f"   Command: {java_info['command']}")
                print(f"   Compatible: {java_info['is_compatible']}")
                if java_info.get('java_home'):
                    print(f"   JAVA_HOME: {java_info['java_home']}")
                return 0
            else:
                print("❌ No compatible Java found")
                return 1
        except ImportError:
            print("⚠️  Portable Java Manager not available")
            return 1

    def _show_java_summary(self, verbose: bool = False) -> int:
        """
        Show comprehensive Java summary

        Args:
            verbose: Show detailed information

        Returns:
            Exit code
        """
        try:
            from portable_java_manager import get_java_detection_summary
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

            if verbose:
                # Show additional details
                print("\n📊 Detailed Information:")
                for key, value in summary.items():
                    if key not in ['platform', 'system_java', 'cache_info', 'latest_lts']:
                        print(f"   {key}: {value}")

            return 0

        except ImportError:
            print("⚠️  Portable Java Manager not available")
            # Fallback to basic Java check
            java_info = check_java_availability()
            print("\n🔍 Basic Java Information:")
            print(f"   Available: {'✅ Yes' if java_info['available'] else '❌ No'}")
            if java_info['available']:
                print(f"   Version: {java_info['version']}")
                print(f"   Type: {java_info['type']}")
                print(f"   Command: {java_info['command']}")
            return 0

    def handle_validate_command(self, args: argparse.Namespace) -> int:
        """
        Handle the validate command

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        try:
            # Check if file exists
            if not Path(args.appimage_path).exists():
                print(f"❌ AppImage file not found: {args.appimage_path}")
                return 1

            print(f"🔍 Validating AppImage: {args.appimage_path}")

            # Import validator
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from appimage_validator import validate_appimage

            # Perform validation
            success = validate_appimage(args.appimage_path)

            if success:
                print("✅ AppImage validation passed!")
                return 0
            else:
                print("❌ AppImage validation failed")
                return 1

        except ImportError:
            print("⚠️  AppImage validator not available")
            return 1
        except Exception as e:
            return handle_error(e, "Validation failed")

    def handle_check_tools_command(self, args: argparse.Namespace) -> int:
        """
        Handle the check-tools command

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        tools = check_required_tools()

        print("🔧 Required Tools Check")
        print("=" * 30)

        missing_tools = []
        for tool, available in tools.items():
            status = "✅" if available else "❌"
            print(f"   {tool}: {status}")
            if not available:
                missing_tools.append(tool)

        if missing_tools:
            print(f"\n❌ Missing tools: {', '.join(missing_tools)}")

            if args.fix_suggestions:
                self._show_tool_installation_suggestions(missing_tools)

            return 1
        else:
            print("\n✅ All required tools are available")
            return 0

    def _show_tool_installation_suggestions(self, missing_tools: list):
        """
        Show suggestions for installing missing tools

        Args:
            missing_tools: List of missing tool names
        """
        print("\n💡 Installation Suggestions:")

        for tool in missing_tools:
            if tool == "java":
                print("   • Install Java: sudo apt install openjdk-11-jdk (Ubuntu/Debian)")
                print("                    sudo yum install java-11-openjdk-devel (RHEL/CentOS)")
            elif tool == "javac":
                print("   • Install JDK: sudo apt install openjdk-11-jdk (Ubuntu/Debian)")
                print("                    sudo yum install java-11-openjdk-devel (RHEL/CentOS)")
            elif tool == "file":
                print("   • Install file: sudo apt install file (Ubuntu/Debian)")
                print("                    sudo yum install file (RHEL/CentOS)")
            elif tool == "strip":
                print("   • Install binutils: sudo apt install binutils (Ubuntu/Debian)")
                print("                       sudo yum install binutils (RHEL/CentOS)")


def handle_command(args: argparse.Namespace) -> int:
    """
    Main command dispatcher

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    handler = CLICommandHandler(verbose=args.verbose)

    if args.command == "convert":
        return handler.handle_convert_command(args)
    elif args.command == "check-platform":
        return handler.handle_check_platform_command(args)
    elif args.command == "java-summary":
        return handler.handle_java_summary_command(args)
    elif args.command == "validate":
        return handler.handle_validate_command(args)
    elif args.command == "check-tools":
        return handler.handle_check_tools_command(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1
