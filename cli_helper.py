#!/usr/bin/env python3
"""
Enhanced CLI Help System for jar2appimage
Provides comprehensive help, examples, and best practices
"""

import os
import sys
from pathlib import Path


class CLIHelper:
    """Comprehensive CLI help and documentation system"""

    def __init__(self):
        self.help_data = {
            "basic_usage": {
                "description": "Convert JAR files to AppImage executables",
                "syntax": "jar2appimage <input.jar> [options]",
                "examples": [
                    "jar2appimage MyApp.jar",
                    'jar2appimage MyApp.jar --name "My Application"',
                    "jar2appimage MyApp.jar --icon app.png --bundled",
                    "jar2appimage MyApp.jar --main-class com.example.Main",
                ],
            },
            "options": {
                "input": {
                    "name": "input.jar",
                    "description": "Path to the JAR file to convert",
                    "required": True,
                    "example": "myapp.jar",
                },
                "--name": {
                    "description": "Application name for the AppImage",
                    "default": "Derived from JAR filename",
                    "example": '--name "My Cool App"',
                },
                "--main-class": {
                    "description": "Main class to execute (auto-detected if not specified)",
                    "default": "Auto-detected from JAR",
                    "example": "--main-class com.example.MainClass",
                },
                "--icon": {
                    "description": "Icon file for the application",
                    "formats": ["PNG", "SVG", "ICO"],
                    "example": "--icon myapp.png",
                },
                "--category": {
                    "description": "Desktop application category",
                    "options": [
                        "Development",
                        "Utility",
                        "Office",
                        "Game",
                        "Graphics",
                        "Network",
                    ],
                    "default": "Utility",
                    "example": "--category Development",
                },
                "--bundled": {
                    "description": "Bundle Java runtime inside AppImage",
                    "benefits": [
                        "Self-contained",
                        "No system Java required",
                        "Consistent environment",
                    ],
                    "example": "--bundled",
                },
                "--output": {
                    "description": "Output directory for the AppImage",
                    "default": "Current directory",
                    "example": "--output ./dist/",
                },
                "--validate": {
                    "description": "Validate the created AppImage after creation",
                    "actions": [
                        "File validation",
                        "Runtime testing",
                        "Desktop integration check",
                    ],
                    "example": "--validate",
                },
                "--verbose": {
                    "description": "Show detailed output during conversion",
                    "example": "--verbose",
                },
            },
            "best_practices": {
                "jar_preparation": [
                    "Ensure your JAR has a proper manifest with Main-Class",
                    "Include all dependencies in the JAR (fat JAR) or specify them",
                    "Test your JAR locally before converting to AppImage",
                    "Use appropriate Java version (LTS recommended)",
                ],
                "naming": [
                    "Use descriptive, user-friendly application names",
                    "Avoid version numbers in the name (AppImage handles this)",
                    "Use spaces for display names, underscores for filenames",
                ],
                "icons": [
                    "Use high-quality icons (minimum 64x64 pixels)",
                    "PNG format preferred for best compatibility",
                    "Square icons work best for desktop integration",
                    "Consider multiple sizes if possible",
                ],
                "distribution": [
                    "Test AppImage on multiple Linux distributions",
                    "Validate AppImage before distribution",
                    "Consider both system Java and bundled Java options",
                    "Document any special requirements or limitations",
                ],
            },
            "troubleshooting": {
                "common_issues": {
                    "Main-Class not found": {
                        "symptoms": ["AppImage fails to start", "Java class errors"],
                        "solutions": [
                            "Specify --main-class explicitly",
                            "Check JAR manifest file",
                            "Use --validate to detect issues",
                        ],
                    },
                    "Java not found": {
                        "symptoms": ["Command not found errors", "Java version issues"],
                        "solutions": [
                            "Install Java JDK or JRE",
                            "Use --bundled option for self-contained AppImage",
                            "Check JAVA_HOME environment variable",
                        ],
                    },
                    "Dependencies missing": {
                        "symptoms": ["ClassNotFoundException", "NoClassDefFoundError"],
                        "solutions": [
                            "Create fat JAR with all dependencies",
                            "Specify external JARs separately",
                            "Check classpath configuration",
                        ],
                    },
                    "Permission denied": {
                        "symptoms": ["Cannot execute AppImage"],
                        "solutions": [
                            "Make AppImage executable: chmod +x app.AppImage",
                            "Check filesystem permissions",
                            "Verify AppImage creation completed successfully",
                        ],
                    },
                }
            },
            "examples": {
                "simple": {
                    "title": "Simple CLI Application",
                    "description": "Convert a basic command-line Java application",
                    "code": 'jar2appimage mycli.jar --name "My CLI Tool"',
                },
                "gui_app": {
                    "title": "GUI Application with Icon",
                    "description": "Convert a GUI application with custom icon and proper desktop integration",
                    "code": 'jar2appimage MyApp.jar \\\n  --name "My Cool App" \\\n  --icon app.png \\\n  --category Development',
                },
                "bundled_java": {
                    "title": "Self-contained Application",
                    "description": "Create a completely self-contained AppImage with bundled Java",
                    "code": 'jar2appimage enterprise.jar \\\n  --name "Enterprise App" \\\n  --bundled \\\n  --validate',
                },
                "custom_main": {
                    "title": "Specify Main Class",
                    "description": "When auto-detection fails, specify the main class explicitly",
                    "code": 'jar2appimage app.jar \\\n  --main-class com.example.MyApp \\\n  --name "My Application"',
                },
                "complex": {
                    "title": "Complete Example",
                    "description": "A comprehensive example with all options",
                    "code": 'jar2appimage complex-app.jar \\\n  --name "Complex Enterprise Application" \\\n  --icon ./assets/app-icon.png \\\n  --category Development \\\n  --main-class com.enterprise.ComplexApp \\\n  --output ./dist/ \\\n  --bundled \\\n  --validate \\\n  --verbose',
                },
            },
            "advanced_topics": {
                "java_versions": {
                    "description": "Java version compatibility and considerations",
                    "recommendations": [
                        "Java 8 LTS: Widest compatibility, but older features",
                        "Java 11 LTS: Good balance of features and compatibility",
                        "Java 17 LTS: Latest LTS with modern features",
                        "Java 21+: Cutting edge, but may have compatibility issues",
                    ],
                    "bundling": "Bundled Java uses the system's default Java version for extraction",
                },
                "classpath_handling": {
                    "description": "How jar2appimage handles dependencies and classpath",
                    "strategies": [
                        "Fat JAR: All dependencies in single JAR (recommended)",
                        "External JARs: Separate dependency JARs",
                        "Maven/Gradle: Build tool integration",
                    ],
                },
                "desktop_integration": {
                    "features": [
                        "Automatic desktop file generation",
                        "Smart terminal detection",
                        "Icon integration",
                        "Category classification",
                    ],
                    "standards": "Follows freedesktop.org standards for Linux desktop integration",
                },
            },
        }

    def format_help_text(self, text: str, indent: int = 0) -> str:
        """Format help text with proper indentation"""
        prefix = " " * indent
        lines = text.split("\n")
        formatted_lines = [prefix + line if line.strip() else line for line in lines]
        return "\n".join(formatted_lines)

    def show_basic_help(self):
        """Show basic usage help"""
        print(
            self.format_help_text("""
🎯 jar2appimage - Convert JAR Files to AppImage Executables

USAGE:
    jar2appimage <input.jar> [options]

EXAMPLES:
    jar2appimage MyApp.jar
    jar2appimage MyApp.jar --name "My Application" --bundled
    jar2appimage MyApp.jar --icon app.png --category Development

For detailed help: jar2appimage --help-detailed
For examples: jar2appimage --examples
For troubleshooting: jar2appimage --troubleshooting
""")
        )

    def show_detailed_help(self):
        """Show detailed help with all options"""
        print(
            self.format_help_text(f"""
🎯 jar2appimage - Convert JAR Files to AppImage Executables

USAGE:
    jar2appimage <input.jar> [options]

REQUIRED:
    input.jar               Path to the JAR file to convert

OPTIONS:
""")
        )

        for opt_name, opt_info in self.help_data["options"].items():
            if opt_name == "input":
                continue

            print(f"    {opt_name}")
            print(f"        {opt_info['description']}")

            if "default" in opt_info:
                print(f"        Default: {opt_info['default']}")

            if "formats" in opt_info:
                print(f"        Formats: {', '.join(opt_info['formats'])}")

            if "options" in opt_info:
                print(f"        Options: {', '.join(opt_info['options'])}")

            if "benefits" in opt_info:
                print(f"        Benefits: {', '.join(opt_info['benefits'])}")

            print(f"        Example: {opt_info['example']}")
            print()

    def show_examples(self):
        """Show usage examples"""
        print(
            self.format_help_text("""
📚 USAGE EXAMPLES
""")
        )

        for example_name, example_data in self.help_data["examples"].items():
            print(f"🏷️  {example_data['title']}")
            print(f"   {example_data['description']}")
            print("   Code:")
            print(self.format_help_text(f"   {example_data['code']}", 6))
            print()

    def show_troubleshooting(self):
        """Show troubleshooting guide"""
        print(
            self.format_help_text("""
🔧 TROUBLESHOOTING GUIDE
""")
        )

        for issue_name, issue_info in self.help_data["troubleshooting"][
            "common_issues"
        ].items():
            print(f"❌ {issue_name}")
            print("   Symptoms:")
            for symptom in issue_info["symptoms"]:
                print(f"   • {symptom}")

            print("   Solutions:")
            for solution in issue_info["solutions"]:
                print(f"   • {solution}")
            print()

    def show_best_practices(self):
        """Show best practices guide"""
        print(
            self.format_help_text("""
💡 BEST PRACTICES
""")
        )

        for category, practices in self.help_data["best_practices"].items():
            print(f"📋 {category.replace('_', ' ').title()}")
            for practice in practices:
                print(f"   • {practice}")
            print()

    def show_advanced_topics(self):
        """Show advanced topics and concepts"""
        print(
            self.format_help_text("""
🚀 ADVANCED TOPICS
""")
        )

        for topic_name, topic_info in self.help_data["advanced_topics"].items():
            print(f"📖 {topic_name.replace('_', ' ').title()}")
            print(f"   {topic_info['description']}")

            if "recommendations" in topic_info:
                print("   Recommendations:")
                for rec in topic_info["recommendations"]:
                    print(f"   • {rec}")

            if "strategies" in topic_info:
                print("   Strategies:")
                for strategy in topic_info["strategies"]:
                    print(f"   • {strategy}")

            if "features" in topic_info:
                print("   Features:")
                for feature in topic_info["features"]:
                    print(f"   • {feature}")

            if "standards" in topic_info:
                print(f"   Standards: {topic_info['standards']}")

            print()

    def show_version_info(self):
        """Show version and system information"""
        print(
            self.format_help_text("""
📋 VERSION INFORMATION
""")
        )

        # Try to get version from the package
        try:
            import jar2appimage

            version = getattr(jar2appimage, "__version__", "Unknown")
        except ImportError:
            version = "Unknown"

        print(f"   jar2appimage version: {version}")
        print(f"   Python version: {sys.version}")
        print(f"   Platform: {sys.platform}")

        # Check for required tools
        tools = ["java", "javac", "file", "strip"]
        print("   Tool availability:")
        for tool in tools:
            try:
                result = os.system(f"which {tool} > /dev/null 2>&1")
                available = result == 0
                print(f"   • {tool}: {'✅' if available else '❌'}")
            except:
                print(f"   • {tool}: ❌")


def show_help(help_type: str = "basic"):
    """Show help based on type"""
    helper = CLIHelper()

    help_methods = {
        "basic": helper.show_basic_help,
        "detailed": helper.show_detailed_help,
        "examples": helper.show_examples,
        "troubleshooting": helper.show_troubleshooting,
        "best-practices": helper.show_best_practices,
        "advanced": helper.show_advanced_topics,
        "version": helper.show_version_info,
    }

    if help_type in help_methods:
        help_methods[help_type]()
    else:
        print(f"Unknown help type: {help_type}")
        print(
            "Available help types: basic, detailed, examples, troubleshooting, best-practices, advanced, version"
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_help(sys.argv[1])
    else:
        show_help("basic")
