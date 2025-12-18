#!/usr/bin/env python3
# mypy: ignore-errors
"""
jar2appimage Unified CLI Interface
Main entry point for the jar2appimage command line interface

This module provides a unified CLI that consolidates all existing implementations
and provides backward compatibility with existing usage patterns.
"""

import logging
import sys
from typing import TYPE_CHECKING, Optional

from .cli_commands import handle_command
from .cli_help import show_help
from .cli_parser import create_unified_parser
from .cli_utils import setup_logging

if TYPE_CHECKING:
    from .cli_parser import CLIParser


class UnifiedCLI:
    """
    Unified CLI interface for jar2appimage
    """

    def __init__(self) -> None:
        self.parser: Optional[CLIParser] = None
        self.logger: Optional[logging.Logger] = None

    def setup(self) -> None:
        """Setup the CLI components"""
        # Create parser
        self.parser = create_unified_parser()

        # Setup logging
        # Note: logging will be setup after parsing arguments to know verbosity level

    def parse_arguments(self, args: Optional[list[str]] = None) -> tuple[bool, Optional[object]]:
        """Parse command line arguments"""
        try:
            if self.parser is None:
                self.setup()
            parsed_args = self.parser.parse_args(args)
            return True, parsed_args
        except SystemExit:
            # argparse handles help and error exits
            return False, None
        except Exception as e:
            print(f"❌ Error parsing arguments: {e}")
            return False, None

    def setup_logging_from_args(self, args: object) -> None:
        """Setup logging based on parsed arguments"""
        verbose = getattr(args, 'verbose', False)
        log_file = getattr(args, 'log_file', None)

        setup_logging(verbose, log_file)
        self.logger = logging.getLogger(__name__)

        if verbose:
            self.logger.debug("Verbose logging enabled")
        if log_file:
            self.logger.debug(f"Logging to file: {log_file}")

    def handle_help_commands(self, args: object) -> bool:
        """Handle help-related commands before main processing"""
        # Handle help subcommands
        if hasattr(args, 'command') and args.command in ['examples', 'troubleshoot', 'best-practices', 'version']:
            if args.command == 'examples':
                category = getattr(args, 'category', None)
                show_help('examples', category)
                return True
            elif args.command == 'troubleshoot':
                issue = getattr(args, 'issue', None)
                show_help('troubleshoot', issue)
                return True
            elif args.command == 'best-practices':
                topic = getattr(args, 'topic', None)
                show_help('best-practices', topic)
                return True
            elif args.command == 'version':
                json_output = getattr(args, 'json', False)
                show_help('version', json=json_output)
                return True

        return False

    def run(self, args: Optional[list[str]] = None) -> int:
        """
        Main CLI entry point

        Args:
            args: Command line arguments (default: sys.argv[1:])

        Returns:
            Exit code
        """
        try:
            # Setup CLI components
            self.setup()

            # Parse arguments
            success, parsed_args = self.parse_arguments(args)
            if not success:
                return 1  # Help was shown or parsing failed

            # Setup logging
            self.setup_logging_from_args(parsed_args)

            # Handle help commands
            if self.handle_help_commands(parsed_args):
                return 0

            # Handle the main command
            exit_code = handle_command(parsed_args)  # type: ignore[arg-type]

            return exit_code

        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"❌ Unexpected error: {e}")
            return 1


def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for the CLI

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code
    """
    # Use legacy CLI for backward compatibility - this will convert
    # 'jar2appimage myapp.jar' to 'jar2appimage convert myapp.jar'
    return run_legacy_cli(args)


def _convert_legacy_args(args: Optional[list[str]]) -> tuple[Optional[int], list[str]]:  # noqa: C901
    """Convert legacy CLI arguments into the new unified format.

    This is split into two simpler phases: 1) short-circuit show-help flags,
    2) convert the remaining args in a compact mapping pass.
    Returns (exit_code, converted_args).
    """
    if args is None:
        args = sys.argv[1:]

    # Phase 1: short-circuit help/show flags
    for special in ('--help-detailed', '--examples', '--troubleshooting', '--version'):
        if special in args:
            if special == '--help-detailed':
                show_help('command', 'convert')
            elif special == '--examples':
                show_help('examples')
            elif special == '--troubleshooting':
                show_help('troubleshoot')
            else:
                show_help('version')
            return 0, []

    # Phase 2: mapping pass (delegated)
    def _map_legacy_args(args_list: list[str]) -> list[str]:
        mapping = {
            '--check-platform': ['check-platform'],
            '-p': ['check-platform'],
            '--java-summary': ['java-summary'],
            '--detect-java': ['java-summary', '--detect-java'],
            '--clear-java-cache': ['java-summary', '--clear-cache'],
        }

        mapped = []
        i = 0
        while i < len(args_list):
            arg = args_list[i]
            if arg in mapping:
                mapped.extend(mapping[arg])
            else:
                mapped.append(arg)
                if arg.startswith('--') and not arg.startswith('--no-') and i + 1 < len(args_list):
                    if not args_list[i + 1].startswith('-'):
                        mapped.append(args_list[i + 1])
                        i += 1
            i += 1
        return mapped

    legacy_args = _map_legacy_args(args)

    if legacy_args and not any(cmd in legacy_args for cmd in [
        'convert', 'check-platform', 'java-summary', 'validate',
        'check-tools', 'examples', 'troubleshoot', 'best-practices', 'version'
    ]):
        legacy_args.insert(0, 'convert')

    return None, legacy_args


# Backward compatibility functions
def run_legacy_cli(args: Optional[list[str]] = None) -> int:
    """Run legacy CLI for backward compatibility"""
    exit_code, legacy_args = _convert_legacy_args(args)
    if exit_code is not None:
        return exit_code

    cli = UnifiedCLI()
    return cli.run(legacy_args)


# Compatibility aliases for old CLI files
def run_jar2appimage_cli() -> int:
    """Run as jar2appimage_cli.py"""
    return run_legacy_cli()


def run_enhanced_jar2appimage_cli() -> int:
    """Run as enhanced_jar2appimage_cli.py"""
    return run_legacy_cli()


def run_enhanced_cli() -> int:
    """Run as enhanced_cli.py"""
    return run_legacy_cli()


def run_cli_helper() -> int:
    """Run as cli_helper.py"""
    if len(sys.argv) > 1:
        show_help(sys.argv[1], *sys.argv[2:])
    else:
        show_help('basic')
    return 0




if __name__ == "__main__":
    sys.exit(main())
