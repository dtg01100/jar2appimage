#!/usr/bin/env python3
"""
jar2appimage CLI Argument Parser
Unified argument parsing for the jar2appimage CLI system
"""

import argparse
from pathlib import Path
from typing import List, Optional


class CLIParser:
    """
    Unified CLI argument parser that consolidates features from all existing implementations
    """

    def __init__(self) -> None:
        self.parser: Optional[argparse.ArgumentParser] = None
        self.subparsers: Optional[
            argparse._SubParsersAction[argparse.ArgumentParser]
        ] = None

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create the main argument parser with all available options

        Returns:
            Configured ArgumentParser instance
        """
        # Create main parser
        self.parser = argparse.ArgumentParser(
            description="Create AppImages from JAR files with unified CLI interface",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s app.jar                                    # Basic conversion
  %(prog)s app.jar --bundled --jdk-version 17        # Self-contained AppImage
  %(prog)s app.jar --name "My App" --icon app.png     # With metadata
  %(prog)s --check-platform                           # Platform compatibility check
  %(prog)s --java-summary                             # Java detection summary
  %(prog)s --validate app.AppImage                    # Validate existing AppImage
            """
        )

        # Add global options
        self.parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )

        self.parser.add_argument(
            "--log-file",
            help="Log file path (default: console only)"
        )

        # Create subcommands
        self.subparsers = self.parser.add_subparsers(
            dest="command",
            help="Available commands",
            metavar="COMMAND"
        )

        # Create convert subcommand (main functionality)
        self._create_convert_command()

        # Create utility subcommands
        self._create_utility_commands()

        # Create help subcommands
        self._create_help_commands()

        return self.parser

    def _create_convert_command(self) -> None:
        """Create the main convert command"""
        if self.subparsers is None:
            raise RuntimeError("Subparsers not initialized")
        convert_parser = self.subparsers.add_parser(
            "convert",
            help="Convert JAR file to AppImage",
            description="Convert a JAR file to a portable AppImage executable"
        )

        # Required arguments
        convert_parser.add_argument(
            "jar_file",
            help="JAR file to convert to AppImage"
        )

        # Basic options
        convert_parser.add_argument(
            "--output-dir", "-o",
            default=".",
            help="Output directory for AppImage (default: current directory)"
        )

        convert_parser.add_argument(
            "--name", "-n",
            help="Application name (default: derived from JAR filename)"
        )

        convert_parser.add_argument(
            "--main-class", "-m",
            help="Main class to execute (auto-detected if not specified)"
        )

        convert_parser.add_argument(
            "--icon",
            help="Icon file for the application (PNG, SVG, ICO)"
        )

        convert_parser.add_argument(
            "--category",
            default="Utility",
            choices=[
                "Development", "Utility", "Office", "Game",
                "Graphics", "Network", "AudioVideo", "Education",
                "Science", "System", "Other"
            ],
            help="Desktop application category (default: Utility)"
        )

        # Java bundling options
        java_group = convert_parser.add_argument_group("Java Options")

        java_group.add_argument(
            "--bundled",
            action="store_true",
            help="Create AppImage with bundled Java runtime for true portability"
        )

        java_group.add_argument(
            "--no-bundled",
            action="store_true",
            help="Create AppImage using system Java (default behavior)"
        )

        java_group.add_argument(
            "--jdk-version",
            default="auto",
            choices=["8", "11", "17", "21", "auto"],
            help="Java version for bundling (default: auto - uses latest LTS)"
        )

        java_group.add_argument(
            "--no-portable",
            action="store_true",
            help="Disable portable Java detection and auto-download"
        )

        # Advanced options
        advanced_group = convert_parser.add_argument_group("Advanced Options")

        advanced_group.add_argument(
            "--force-download",
            action="store_true",
            help="Force Java download even if cached version exists"
        )

        advanced_group.add_argument(
            "--validate",
            action="store_true",
            help="Validate the created AppImage"
        )

        advanced_group.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually creating AppImage"
        )

        # Configuration options
        config_group = convert_parser.add_argument_group("Configuration")

        config_group.add_argument(
            "--config", "-c",
            help="Configuration file path"
        )

        config_group.add_argument(
            "--save-config",
            help="Save configuration to file after conversion"
        )

    def _create_utility_commands(self) -> None:
        """Create utility subcommands"""
        if self.subparsers is None:
            raise RuntimeError("Subparsers not initialized")
        # Platform check command
        platform_parser = self.subparsers.add_parser(
            "check-platform",
            help="Check platform compatibility"
        )

        platform_parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show detailed platform information"
        )

        # Java summary command
        java_parser = self.subparsers.add_parser(
            "java-summary",
            help="Show Java detection and management summary"
        )

        java_parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear Java download cache and exit"
        )

        java_parser.add_argument(
            "--detect-java",
            action="store_true",
            help="Detect and analyze system Java installation"
        )

        java_parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show detailed Java information"
        )

        # Validate command
        validate_parser = self.subparsers.add_parser(
            "validate",
            help="Validate an existing AppImage"
        )

        validate_parser.add_argument(
            "appimage_path",
            help="Path to AppImage to validate"
        )

        validate_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed validation report"
        )

        # Tools check command
        tools_parser = self.subparsers.add_parser(
            "check-tools",
            help="Check availability of required tools"
        )

        tools_parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Show only missing tools"
        )

        tools_parser.add_argument(
            "--fix-suggestions",
            action="store_true",
            help="Show suggestions for installing missing tools"
        )

    def _create_help_commands(self) -> None:
        """Create help-related subcommands"""
        if self.subparsers is None:
            raise RuntimeError("Subparsers not initialized")
        # Examples command
        examples_parser = self.subparsers.add_parser(
            "examples",
            help="Show usage examples"
        )

        examples_parser.add_argument(
            "--category",
            choices=["basic", "advanced", "gui", "enterprise"],
            help="Filter examples by category"
        )

        # Troubleshooting command
        troubleshoot_parser = self.subparsers.add_parser(
            "troubleshoot",
            help="Show troubleshooting guide"
        )

        troubleshoot_parser.add_argument(
            "--issue",
            help="Show help for specific issue"
        )

        # Best practices command
        practices_parser = self.subparsers.add_parser(
            "best-practices",
            help="Show best practices guide"
        )

        practices_parser.add_argument(
            "--topic",
            choices=["jar-preparation", "naming", "icons", "distribution"],
            help="Show help for specific topic"
        )

        # Version command
        version_parser = self.subparsers.add_parser(
            "version",
            help="Show version and system information"
        )

        version_parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format"
        )

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command line arguments

        Args:
            args: Command line arguments (default: sys.argv[1:])

        Returns:
            Parsed arguments namespace
        """
        if self.parser is None:
            self.create_parser()

        assert self.parser is not None
        return self.parser.parse_args(args)

    def validate_args(self, args: argparse.Namespace) -> tuple[bool, List[str]]:
        """
        Validate parsed arguments

        Args:
            args: Parsed arguments namespace

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: List[str] = []

        # Validate convert command arguments
        if args.command == "convert":
            errors.extend(self._validate_convert_args(args))

        # Validate validate command arguments
        elif args.command == "validate":
            errors.extend(self._validate_validate_args(args))

        # Validate other commands as needed
        elif args.command == "check-platform":
            errors.extend(self._validate_platform_args(args))

        return len(errors) == 0, errors

    def _validate_convert_args(self, args: argparse.Namespace) -> List[str]:
        """Validate convert command arguments"""
        errors = []

        # Check JAR file exists
        if args.jar_file:
            jar_path = Path(args.jar_file)
            if not jar_path.exists():
                errors.append(f"JAR file not found: {args.jar_file}")
        else:
            errors.append("JAR file is required for convert command")

        # Validate bundling options
        if args.bundled and args.no_bundled:
            errors.append("Cannot use both --bundled and --no-bundled options")

        # Validate Java version
        if args.jdk_version not in ["8", "11", "17", "21", "auto"]:
            errors.append(f"Invalid Java version: {args.jdk_version}")

        # Validate icon file if specified
        if args.icon:
            icon_path = Path(args.icon)
            if not icon_path.exists():
                errors.append(f"Icon file not found: {args.icon}")

        # Validate category
        valid_categories = [
            "Development", "Utility", "Office", "Game",
            "Graphics", "Network", "AudioVideo", "Education",
            "Science", "System", "Other"
        ]
        if args.category not in valid_categories:
            errors.append(f"Invalid category: {args.category}")

        return errors

    def _validate_validate_args(self, args: argparse.Namespace) -> List[str]:
        """Validate validate command arguments"""
        errors = []

        # Check AppImage file exists
        if args.appimage_path:
            appimage_path = Path(args.appimage_path)
            if not appimage_path.exists():
                errors.append(f"AppImage file not found: {args.appimage_path}")
        else:
            errors.append("AppImage path is required for validate command")

        return errors

    def _validate_platform_args(self, args: argparse.Namespace) -> List[str]:
        """Validate platform command arguments"""
        errors: List[str] = []
        # No specific validation needed for platform command currently
        return errors

    def get_command_help(self, command: str) -> str:
        """Get help text for a specific command"""
        if self.parser is None:
            self.create_parser()

        help_map = {
            "convert": "Convert JAR file to AppImage",
            "check-platform": "Check platform compatibility",
            "java-summary": "Show Java detection summary",
            "validate": "Validate existing AppImage",
            "check-tools": "Check required tools availability",
            "examples": "Show usage examples",
            "troubleshoot": "Show troubleshooting guide",
            "best-practices": "Show best practices",
            "version": "Show version information",
        }

        return help_map.get(command, "Unknown command")


def create_unified_parser() -> CLIParser:
    """
    Create and return a unified CLI parser

    Returns:
        Configured CLIParser instance
    """
    parser = CLIParser()
    parser.create_parser()
    return parser


def parse_command_line(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments using unified parser

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = create_unified_parser()
    return parser.parse_args(args)


if __name__ == "__main__":
    # Test the parser
    parser = create_unified_parser()

    # Test different argument combinations
    test_cases = [
        ["app.jar"],
        ["app.jar", "--bundled"],
        ["app.jar", "--name", "My App", "--icon", "app.png"],
        ["--check-platform"],
        ["--java-summary"],
        ["--validate", "app.AppImage"],
        ["--examples"],
        ["--help"]
    ]

    print("Testing CLI Parser:")
    print("=" * 50)

    for test_args in test_cases:
        print(f"\nTesting: {' '.join(test_args)}")
        try:
            args = parser.parse_args(test_args)
            print(f"✓ Parsed successfully: {args}")
        except SystemExit:
            print("✓ Handled (likely help or error)")
        except Exception as e:
            print(f"✗ Error: {e}")
