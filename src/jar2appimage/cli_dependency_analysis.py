#!/usr/bin/env python3
"""
CLI Integration for Dependency Analysis

This module provides CLI commands for the new comprehensive dependency analysis system.
It integrates with the existing CLI infrastructure to provide dependency analysis commands.
"""

import argparse
import json
import sys
from typing import List, Optional

from .dependency_analyzer import (
    AnalysisConfiguration,
    analyze_application_dependencies,
    quick_dependency_check,
)
from .dependency_resolver import ConflictResolutionStrategy, Platform
from .jar_analyzer import analyze_jar_file, generate_jar_report


def create_dependency_parser() -> argparse.ArgumentParser:
    """Create argument parser for dependency analysis commands"""
    parser = argparse.ArgumentParser(
        prog='jar2appimage-deps',
        description='Comprehensive dependency analysis for JAR files',
        add_help=False
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Perform comprehensive dependency analysis',
        parents=[parser]
    )
    analyze_parser.add_argument(
        'jar_files',
        nargs='+',
        help='JAR files to analyze'
    )
    analyze_parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format'
    )
    analyze_parser.add_argument(
        '--config', '-c',
        help='Configuration file path'
    )
    analyze_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    analyze_parser.add_argument(
        '--platform',
        choices=['linux', 'windows', 'macos', 'any'],
        default='any',
        help='Target platform'
    )
    analyze_parser.add_argument(
        '--java-version',
        help='Target Java version'
    )
    analyze_parser.add_argument(
        '--strategy',
        choices=['prefer_latest', 'prefer_compile_scope', 'prefer_non_optional'],
        default='prefer_latest',
        help='Conflict resolution strategy'
    )
    analyze_parser.add_argument(
        '--bundle-native',
        action='store_true',
        help='Bundle native libraries'
    )
    analyze_parser.add_argument(
        '--bundle-optional',
        action='store_true',
        help='Bundle optional dependencies'
    )

    # Quick check command
    quick_parser = subparsers.add_parser(
        'quick',
        help='Quick dependency check',
        parents=[parser]
    )
    quick_parser.add_argument(
        'jar_file',
        help='JAR file to check'
    )
    quick_parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format'
    )

    # JAR info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show JAR file information',
        parents=[parser]
    )
    info_parser.add_argument(
        'jar_file',
        help='JAR file to analyze'
    )
    info_parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format'
    )

    # List dependencies command
    list_parser = subparsers.add_parser(
        'list',
        help='List dependencies',
        parents=[parser]
    )
    list_parser.add_argument(
        'jar_file',
        help='JAR file to analyze'
    )
    list_parser.add_argument(
        '--scope',
        choices=['compile', 'runtime', 'test', 'provided', 'optional'],
        help='Filter by scope'
    )
    list_parser.add_argument(
        '--type',
        choices=['maven', 'jar', 'native', 'resource', 'platform'],
        help='Filter by type'
    )
    list_parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format'
    )

    return parser


def handle_analyze_command(args: argparse.Namespace) -> int:
    """Handle the analyze command"""
    try:
        # Create configuration
        config = AnalysisConfiguration(
            verbose=args.verbose,
            output_format=args.output,
            target_platform=Platform(args.platform),
            java_version=args.java_version,
            conflict_resolution_strategy=ConflictResolutionStrategy(args.strategy),
            bundle_native_libraries=args.bundle_native,
            bundle_optional_deps=args.bundle_optional
        )

        # Load config from file if provided
        if args.config:
            config = load_config_from_file(args.config)

        # Perform analysis
        result = analyze_application_dependencies(args.jar_files, config)

        # Output results
        if args.output == 'json':
            print(json.dumps(result.reports.get('json', '{}'), indent=2))
        else:
            print(result.reports.get('text', 'No report generated'))

        # Show recommendations
        if result.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in result.recommendations:
                print(f"  • {rec}")

        # Show warnings
        if result.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in result.warnings:
                print(f"  • {warning}")

        # Show errors
        if result.errors:
            print("\n❌ ERRORS:")
            for error in result.errors:
                print(f"  • {error}")
            return 1

        return 0

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        return 1


def handle_quick_command(args: argparse.Namespace) -> int:
    """Handle the quick command"""
    try:
        result = quick_dependency_check(args.jar_file)

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"🔍 Quick Dependency Check: {args.jar_file}")
            print(f"  Valid JAR: {'✅' if result['is_valid'] else '❌'}")
            print(f"  Main Class: {result['main_class'] or 'Not found'}")
            print(f"  Dependencies: {result['dependency_count']}")
            print(f"  Conflicts: {'⚠️  Yes' if result['has_conflicts'] else '✅ No'}")
            print(f"  Size: {result['estimated_size_mb']:.1f} MB")
            print(f"  Java Version: {result['java_version']}")

            if result['warnings']:
                print(f"  Warnings: {len(result['warnings'])}")
            if result['errors']:
                print(f"  Errors: {len(result['errors'])}")

        return 0 if not result['errors'] else 1

    except Exception as e:
        print(f"Error during quick check: {e}", file=sys.stderr)
        return 1


def handle_info_command(args: argparse.Namespace) -> int:
    """Handle the info command"""
    try:
        report = generate_jar_report(args.jar_file)

        if args.output == 'json':
            # Convert text report to structured data
            result = analyze_jar_file(args.jar_file)
            data = {
                'jar_path': str(result.jar_path),
                'jar_size': result.jar_size,
                'entry_count': result.entry_count,
                'is_valid': result.is_valid_jar,
                'main_class': result.manifest.main_class if result.manifest else None,
                'class_count': len(result.class_files),
                'resource_count': len(result.resources),
                'native_libraries': result.native_libraries,
                'config_files': result.config_files,
                'estimated_java_version': result.estimated_java_version.value,
                'warnings': result.warnings,
                'errors': result.errors
            }
            print(json.dumps(data, indent=2))
        else:
            print(report)

        return 0 if not analyze_jar_file(args.jar_file).errors else 1

    except Exception as e:
        print(f"Error analyzing JAR: {e}", file=sys.stderr)
        return 1


def handle_list_command(args: argparse.Namespace) -> int:
    """Handle the list command"""
    try:
        result = analyze_jar_file(args.jar_file)

        dependencies = result.dependencies

        # Apply filters
        if args.scope:
            # Note: This would need proper scope filtering logic
            pass

        if args.type:
            # Note: This would need proper type filtering logic
            pass

        if args.output == 'json':
            data = {
                'jar_path': str(result.jar_path),
                'dependencies': [
                    {
                        'group_id': dep.group_id,
                        'artifact_id': dep.artifact_id,
                        'version': dep.version,
                        'scope': dep.scope.value,
                        'type': dep.dependency_type.value,
                        'optional': dep.is_optional
                    }
                    for dep in dependencies
                ]
            }
            print(json.dumps(data, indent=2))
        else:
            print(f"📦 Dependencies in {args.jar_file}:")
            print(f"  Total: {len(dependencies)}")

            for i, dep in enumerate(dependencies, 1):
                version_info = f":{dep.version}" if dep.version else ""
                optional_info = " (optional)" if dep.is_optional else ""
                print(f"  {i:2d}. {dep.group_id}:{dep.artifact_id}{version_info} [{dep.scope.value}]{optional_info}")

        return 0

    except Exception as e:
        print(f"Error listing dependencies: {e}", file=sys.stderr)
        return 1


def load_config_from_file(config_path: str) -> AnalysisConfiguration:
    """Load configuration from file"""
    # This is a placeholder - would implement proper config loading
    # from YAML, JSON, or other formats
    return AnalysisConfiguration()


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point"""
    parser = create_dependency_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    try:
        if parsed_args.command == 'analyze':
            return handle_analyze_command(parsed_args)
        elif parsed_args.command == 'quick':
            return handle_quick_command(parsed_args)
        elif parsed_args.command == 'info':
            return handle_info_command(parsed_args)
        elif parsed_args.command == 'list':
            return handle_list_command(parsed_args)
        else:
            print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
