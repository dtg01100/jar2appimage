#!/usr/bin/env python3
# mypy: ignore-errors
"""
jar2appimage CLI Help System
Unified help system for the jar2appimage CLI
"""

import os
import sys
from typing import Any, Dict, Optional


class CLIHelpSystem:
    """
    Comprehensive CLI help and documentation system
    """

    def __init__(self) -> None:
        self.help_data = self._initialize_help_data()

    def _initialize_help_data(self) -> Dict[str, Any]:
        """Initialize comprehensive help data"""
        return {
            "basic_usage": {
                "description": "Convert JAR files to AppImage executables",
                "syntax": "jar2appimage <command> [options]",
                "examples": [
                    "jar2appimage convert app.jar",
                    "jar2appimage convert app.jar --bundled --jdk-version 17",
                    "jar2appimage check-platform",
                    "jar2appimage java-summary",
                    "jar2appimage validate app.AppImage",
                ],
            },
            "commands": {
                "convert": {
                    "description": "Convert JAR file to AppImage",
                    "usage": "jar2appimage convert <jar_file> [options]",
                    "options": {
                        "--output-dir, -o": "Output directory for AppImage",
                        "--name, -n": "Application name",
                        "--main-class, -m": "Main class to execute",
                        "--icon": "Icon file for the application",
                        "--category": "Desktop application category",
                        "--bundled": "Create AppImage with bundled Java",
                        "--no-bundled": "Use system Java (default)",
                        "--jdk-version": "Java version for bundling (8, 11, 17, 21, auto)",
                        "--no-portable": "Disable portable Java detection",
                        "--validate": "Validate the created AppImage",
                        "--dry-run": "Show what would be done without creating",
                        "--config, -c": "Configuration file path",
                        "--save-config": "Save configuration to file",
                    }
                },
                "check-platform": {
                    "description": "Check platform compatibility",
                    "usage": "jar2appimage check-platform [options]",
                    "options": {
                        "--verbose, -v": "Show detailed platform information"
                    }
                },
                "java-summary": {
                    "description": "Show Java detection and management summary",
                    "usage": "jar2appimage java-summary [options]",
                    "options": {
                        "--clear-cache": "Clear Java download cache",
                        "--detect-java": "Detect and analyze system Java",
                        "--verbose, -v": "Show detailed Java information"
                    }
                },
                "validate": {
                    "description": "Validate an existing AppImage",
                    "usage": "jar2appimage validate <appimage_path>",
                    "options": {
                        "--detailed": "Show detailed validation report"
                    }
                },
                "check-tools": {
                    "description": "Check availability of required tools",
                    "usage": "jar2appimage check-tools [options]",
                    "options": {
                        "--missing-only": "Show only missing tools",
                        "--fix-suggestions": "Show installation suggestions"
                    }
                },
                "examples": {
                    "description": "Show usage examples",
                    "usage": "jar2appimage examples [options]",
                    "options": {
                        "--category": "Filter by category (basic, advanced, gui, enterprise)"
                    }
                },
                "troubleshoot": {
                    "description": "Show troubleshooting guide",
                    "usage": "jar2appimage troubleshoot [options]",
                    "options": {
                        "--issue": "Show help for specific issue"
                    }
                },
                "best-practices": {
                    "description": "Show best practices guide",
                    "usage": "jar2appimage best-practices [options]",
                    "options": {
                        "--topic": "Show help for specific topic"
                    }
                },
                "version": {
                    "description": "Show version and system information",
                    "usage": "jar2appimage version [options]",
                    "options": {
                        "--json": "Output in JSON format"
                    }
                }
            },
            "examples": {
                "basic": {
                    "title": "Basic Conversion",
                    "description": "Simple JAR to AppImage conversion",
                    "code": "jar2appimage convert app.jar"
                },
                "bundled_java": {
                    "title": "Self-contained AppImage",
                    "description": "Create AppImage with bundled Java",
                    "code": "jar2appimage convert app.jar --bundled --jdk-version 17"
                },
                "with_metadata": {
                    "title": "With Application Metadata",
                    "description": "Include custom name, icon, and category",
                    "code": 'jar2appimage convert app.jar \\\n  --name "My Cool App" \\\n  --icon app.png \\\n  --category Development'
                },
                "advanced": {
                    "title": "Advanced Configuration",
                    "description": "Complete example with all options",
                    "code": 'jar2appimage convert app.jar \\\n  --name "Enterprise App" \\\n  --icon ./assets/app-icon.png \\\n  --category Development \\\n  --main-class com.example.Main \\\n  --output ./dist/ \\\n  --bundled \\\n  --jdk-version 17 \\\n  --validate \\\n  --verbose'
                },
                "validation": {
                    "title": "Validate Existing AppImage",
                    "description": "Check an already created AppImage",
                    "code": "jar2appimage validate app.AppImage --detailed"
                },
                "platform_check": {
                    "title": "Platform Compatibility",
                    "description": "Check if current platform supports AppImage creation",
                    "code": "jar2appimage check-platform --verbose"
                }
            },
            "troubleshooting": {
                "common_issues": {
                    "Main-Class not found": {
                        "symptoms": ["AppImage fails to start", "Java class errors"],
                        "solutions": [
                            "Specify --main-class explicitly",
                            "Check JAR manifest file",
                            "Use --validate to detect issues"
                        ]
                    },
                    "Java not found": {
                        "symptoms": ["Command not found errors", "Java version issues"],
                        "solutions": [
                            "Install Java JDK or JRE",
                            "Use --bundled option for self-contained AppImage",
                            "Check JAVA_HOME environment variable"
                        ]
                    },
                    "Dependencies missing": {
                        "symptoms": ["ClassNotFoundException", "NoClassDefFoundError"],
                        "solutions": [
                            "Create fat JAR with all dependencies",
                            "Specify external JARs separately",
                            "Check classpath configuration"
                        ]
                    },
                    "Permission denied": {
                        "symptoms": ["Cannot execute AppImage"],
                        "solutions": [
                            "Make AppImage executable: chmod +x app.AppImage",
                            "Check filesystem permissions",
                            "Verify AppImage creation completed successfully"
                        ]
                    }
                }
            },
            "best_practices": {
                "jar_preparation": [
                    "Ensure your JAR has a proper manifest with Main-Class",
                    "Include all dependencies in the JAR (fat JAR) or specify them",
                    "Test your JAR locally before converting to AppImage",
                    "Use appropriate Java version (LTS recommended)"
                ],
                "naming": [
                    "Use descriptive, user-friendly application names",
                    "Avoid version numbers in the name (AppImage handles this)",
                    "Use spaces for display names, underscores for filenames"
                ],
                "icons": [
                    "Use high-quality icons (minimum 64x64 pixels)",
                    "PNG format preferred for best compatibility",
                    "Square icons work best for desktop integration",
                    "Consider multiple sizes if possible"
                ],
                "distribution": [
                    "Test AppImage on multiple Linux distributions",
                    "Validate AppImage before distribution",
                    "Consider both system Java and bundled Java options",
                    "Document any special requirements or limitations"
                ]
            },
            "advanced_topics": {
                "java_versions": {
                    "description": "Java version compatibility and considerations",
                    "recommendations": [
                        "Java 8 LTS: Widest compatibility, but older features",
                        "Java 11 LTS: Good balance of features and compatibility",
                        "Java 17 LTS: Latest LTS with modern features",
                        "Java 21+: Cutting edge, but may have compatibility issues"
                    ],
                    "bundling": "Bundled Java uses the system's default Java version for extraction"
                },
                "classpath_handling": {
                    "description": "How jar2appimage handles dependencies and classpath",
                    "strategies": [
                        "Fat JAR: All dependencies in single JAR (recommended)",
                        "External JARs: Separate dependency JARs",
                        "Maven/Gradle: Build tool integration"
                    ]
                },
                "desktop_integration": {
                    "features": [
                        "Automatic desktop file generation",
                        "Smart terminal detection",
                        "Icon integration",
                        "Category classification"
                    ],
                    "standards": "Follows freedesktop.org standards for Linux desktop integration"
                }
            }
        }

    def show_basic_help(self) -> None:
        """Show basic usage help"""
        self._print_formatted_text("""
🎯 jar2appimage - Convert JAR Files to AppImage Executables

USAGE:
    jar2appimage <command> [options]

COMMANDS:
    convert              Convert JAR file to AppImage
    check-platform       Check platform compatibility
    java-summary         Show Java detection summary
    validate             Validate existing AppImage
    check-tools          Check required tools
    examples             Show usage examples
    troubleshoot         Show troubleshooting guide
    best-practices       Show best practices
    version              Show version information

EXAMPLES:
    jar2appimage convert app.jar
    jar2appimage convert app.jar --bundled --jdk-version 17
    jar2appimage check-platform
    jar2appimage java-summary
    jar2appimage validate app.AppImage

For detailed help: jar2appimage <command> --help
        """)

    def show_command_help(self, command: str) -> None:
        """Show help for a specific command"""
        if command not in self.help_data["commands"]:
            print(f"❌ Unknown command: {command}")
            print("Available commands:")
            for cmd in self.help_data["commands"].keys():
                print(f"  • {cmd}")
            return

        cmd_data = self.help_data["commands"][command]
        self._print_formatted_text(f"""
🏷️  {command.upper()} COMMAND

{cmd_data['description']}

USAGE:
    {cmd_data['usage']}

OPTIONS:""")

        for option, description in cmd_data["options"].items():
            self._print_formatted_text(f"    {option:<20} {description}")

    def show_examples(self, category: Optional[str] = None) -> None:
        """Show usage examples"""
        self._print_formatted_text("""
📚 USAGE EXAMPLES
        """)

        examples = self.help_data["examples"]
        if category:
            # Filter examples by category
            filtered_examples = {k: v for k, v in examples.items()
                               if category.lower() in k.lower()}
            if filtered_examples:
                examples = filtered_examples
            else:
                print(f"No examples found for category: {category}")
                return

        for _example_name, example_data in examples.items():
            self._print_formatted_text(f"""
🏷️  {example_data['title']}
   {example_data['description']}
   Code:""")
            self._print_formatted_text(f"   {example_data['code']}", indent=6)

    def show_troubleshooting(self, issue: Optional[str] = None) -> None:
        """Show troubleshooting guide"""
        self._print_formatted_text("""
🔧 TROUBLESHOOTING GUIDE
        """)

        if issue:
            # Show help for specific issue
            issues = self.help_data["troubleshooting"]["common_issues"]
            for issue_name, issue_info in issues.items():
                if issue.lower() in issue_name.lower():
                    self._print_formatted_text(f"""
❌ {issue_name}
   Symptoms:""")
                    for symptom in issue_info["symptoms"]:
                        self._print_formatted_text(f"   • {symptom}", indent=4)

                    self._print_formatted_text("   Solutions:")
                    for solution in issue_info["solutions"]:
                        self._print_formatted_text(f"   • {solution}", indent=4)
                    return

            print(f"No troubleshooting help found for: {issue}")
            return

        # Show all issues
        issues = self.help_data["troubleshooting"]["common_issues"]
        for issue_name, issue_info in issues.items():
            self._print_formatted_text(f"""
❌ {issue_name}
   Symptoms:""")
            for symptom in issue_info["symptoms"]:
                self._print_formatted_text(f"   • {symptom}", indent=4)

            self._print_formatted_text("   Solutions:")
            for solution in issue_info["solutions"]:
                self._print_formatted_text(f"   • {solution}", indent=4)

    def show_best_practices(self, topic: Optional[str] = None) -> None:
        """Show best practices guide"""
        self._print_formatted_text("""
💡 BEST PRACTICES
        """)

        if topic:
            # Show help for specific topic
            practices = self.help_data["best_practices"]
            for topic_name, topic_practices in practices.items():
                if topic.lower() in topic_name.lower():
                    self._print_formatted_text(f"""
📋 {topic_name.replace('_', ' ').title()}""")
                    for practice in topic_practices:
                        self._print_formatted_text(f"   • {practice}", indent=4)
                    return

            print(f"No best practices found for topic: {topic}")
            return

        # Show all topics
        practices = self.help_data["best_practices"]
        for topic_name, topic_practices in practices.items():
            self._print_formatted_text(f"""
📋 {topic_name.replace('_', ' ').title()}""")
            for practice in topic_practices:
                self._print_formatted_text(f"   • {practice}", indent=4)

    def show_advanced_topics(self) -> None:
        """Show advanced topics and concepts"""
        self._print_formatted_text("""
🚀 ADVANCED TOPICS
        """)

        topics = self.help_data["advanced_topics"]
        for topic_name, topic_info in topics.items():
            self._print_formatted_text(f"""
📖 {topic_name.replace('_', ' ').title()}
   {topic_info['description']}""")

            if "recommendations" in topic_info:
                self._print_formatted_text("   Recommendations:")
                for rec in topic_info["recommendations"]:
                    self._print_formatted_text(f"   • {rec}", indent=6)

            if "strategies" in topic_info:
                self._print_formatted_text("   Strategies:")
                for strategy in topic_info["strategies"]:
                    self._print_formatted_text(f"   • {strategy}", indent=6)

            if "features" in topic_info:
                self._print_formatted_text("   Features:")
                for feature in topic_info["features"]:
                    self._print_formatted_text(f"   • {feature}", indent=6)

            if "standards" in topic_info:
                self._print_formatted_text(f"   Standards: {topic_info['standards']}")

    def show_version_info(self, json_output: bool = False) -> None:
        """Show version and system information"""
        if json_output:
            import json
            version_info = self._get_version_info()
            print(json.dumps(version_info, indent=2))
        else:
            self._print_formatted_text("""
📋 VERSION INFORMATION
            """)

            version_info = self._get_version_info()
            for key, value in version_info.items():
                self._print_formatted_text(f"   {key}: {value}")

    def _get_version_info(self) -> Dict[str, Any]:
        """Get comprehensive version information"""
        info: Dict[str, Any] = {}

        # Try to get version from the package
        try:
            import jar2appimage
            info["jar2appimage version"] = getattr(jar2appimage, "__version__", "Unknown")
        except ImportError:
            info["jar2appimage version"] = "Unknown"

        info["Python version"] = sys.version.split()[0]
        info["Platform"] = sys.platform

        # Check for required tools
        tools = ["java", "javac", "file", "strip"]
        info["Required tools"]: Dict[str, str] = {}
        for tool in tools:
            try:
                result = os.system(f"which {tool} > /dev/null 2>&1")
                available = result == 0
                info["Required tools"][tool] = "✅" if available else "❌"
            except Exception:
                info["Required tools"][tool] = "❌"

        return info

    def _print_formatted_text(self, text: str, indent: int = 0) -> None:
        """Format help text with proper indentation"""
        prefix = " " * indent
        lines = text.split("\n")
        formatted_lines = [prefix + line if line.strip() else line for line in lines]
        print("\n".join(formatted_lines))


def show_help(help_type: str = "basic", *args: Any, **kwargs: Any) -> None:
    """
    Show help based on type

    Args:
        help_type: Type of help to show
        *args: Additional arguments for specific help types
        **kwargs: Additional keyword arguments
    """
    help_system = CLIHelpSystem()

    def show_examples_wrapper(category: Optional[str] = None):
        help_system.show_examples(category)

    def show_troubleshoot_wrapper(issue: Optional[str] = None):
        help_system.show_troubleshooting(issue)

    def show_best_practices_wrapper(topic: Optional[str] = None):
        help_system.show_best_practices(topic)

    help_methods = {
        "basic": help_system.show_basic_help,
        "command": lambda cmd: help_system.show_command_help(cmd),
        "examples": show_examples_wrapper,
        "troubleshoot": show_troubleshoot_wrapper,
        "best-practices": show_best_practices_wrapper,
        "advanced": help_system.show_advanced_topics,
        "version": lambda json=False: help_system.show_version_info(json),
    }

    if help_type in help_methods:
        if help_type == "command" and args:
            help_methods[help_type](args[0])
        elif help_type in ["examples", "troubleshoot", "best-practices"] and args:
            help_methods[help_type](args[0] if args[0] is not None else None)
        elif help_type == "version" and kwargs.get("json"):
            help_methods[help_type](True)
        else:
            help_methods[help_type]()
    else:
        print(f"Unknown help type: {help_type}")
        print("Available help types: basic, command, examples, troubleshoot, best-practices, advanced, version")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_help(sys.argv[1], *sys.argv[2:])
    else:
        show_help("basic")
