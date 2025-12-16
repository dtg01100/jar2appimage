# jar2appimage CLI Unified Migration Guide

## Overview

This guide helps users migrate from the multiple legacy CLI implementations to the new unified CLI system. The unified CLI consolidates all existing functionality into a single, consistent interface while maintaining backward compatibility.

## What Changed

### Before (Multiple CLIs)
- `jar2appimage_cli.py` - Original 223-line implementation
- `enhanced_jar2appimage_cli.py` - Enhanced 457-line implementation with complex nesting
- `enhanced_cli.py` - Another 187-line enhanced version
- `cli_helper.py` - Help system with 414 lines, mixed with CLI logic

### After (Unified CLI)
- **`src/jar2appimage/cli.py`** - Main unified CLI interface
- **`src/jar2appimage/cli_parser.py`** - Argument parsing and validation
- **`src/jar2appimage/cli_commands.py`** - Command handlers
- **`src/jar2appimage/cli_help.py`** - Unified help system
- **`src/jar2appimage/cli_utils.py`** - Common utilities and platform detection

## Key Benefits

### ✅ Eliminated Duplication
- **Platform detection logic**: Consolidated from 4 implementations to 1
- **Argument parsing**: Unified approach across all commands
- **Error handling**: Consistent error messages and exit codes
- **Help system**: Single source of truth for documentation

### ✅ Improved Architecture
- **Clean separation**: CLI parsing vs business logic
- **Modular design**: Each component has a single responsibility
- **Testability**: Clean interfaces allow for comprehensive testing
- **Maintainability**: Single codebase to maintain

### ✅ Enhanced User Experience
- **Consistent interface**: Same options and behaviors across commands
- **Comprehensive help**: Complete documentation and examples
- **Better error messages**: User-friendly suggestions
- **Command organization**: Logical grouping of functionality

## Migration Paths

### For End Users

#### New Recommended Usage

```bash
# Basic conversion
jar2appimage convert app.jar

# With Java bundling
jar2appimage convert app.jar --bundled --jdk-version 17

# Platform check
jar2appimage check-platform

# Java management
jar2appimage java-summary

# Validate existing AppImage
jar2appimage validate app.AppImage
```

#### Legacy Usage (Still Supported)

```bash
# These still work for backward compatibility
python jar2appimage_cli.py app.jar
python enhanced_jar2appimage_cli.py app.jar --bundled
python enhanced_cli.py app.jar --name "My App"
python cli_helper.py --examples
```

### For Developers

#### New Unified API

```python
from jar2appimage.cli import UnifiedCLI

# Create and run CLI
cli = UnifiedCLI()
exit_code = cli.run(['convert', 'app.jar', '--bundled'])

# Or use individual components
from jar2appimage.cli_parser import create_unified_parser
from jar2appimage.cli_commands import handle_command

parser = create_unified_parser()
args = parser.parse_args(['convert', 'app.jar'])
exit_code = handle_command(args)
```

#### Legacy API (Deprecated)

```python
# Old way - still works but not recommended
import jar2appimage_cli
jar2appimage_cli.main()

import enhanced_jar2appimage_cli
enhanced_jar2appimage_cli.main()
```

## Command Mapping

### New Commands vs Old Options

| Old CLI | Old Usage | New Usage | Description |
|---------|-----------|-----------|-------------|
| jar2appimage_cli.py | `app.jar` | `jar2appimage convert app.jar` | Basic conversion |
| jar2appimage_cli.py | `app.jar --bundled` | `jar2appimage convert app.jar --bundled` | Java bundling |
| enhanced_jar2appimage_cli.py | `app.jar --check-platform` | `jar2appimage check-platform` | Platform check |
| enhanced_jar2appimage_cli.py | `--java-summary` | `jar2appimage java-summary` | Java info |
| enhanced_cli.py | `app.jar --validate` | `jar2appimage convert app.jar --validate` | With validation |
| cli_helper.py | `--examples` | `jar2appimage examples` | Usage examples |
| cli_helper.py | `--help-detailed` | `jar2appimage convert --help` | Detailed help |

### New Commands

| Command | Description | Options |
|---------|-------------|---------|
| `convert` | Convert JAR to AppImage | `--bundled`, `--jdk-version`, `--name`, `--icon`, etc. |
| `check-platform` | Check platform compatibility | `--verbose` |
| `java-summary` | Java detection and management | `--clear-cache`, `--detect-java` |
| `validate` | Validate existing AppImage | `--detailed` |
| `check-tools` | Check required tools | `--missing-only`, `--fix-suggestions` |
| `examples` | Show usage examples | `--category` |
| `troubleshoot` | Troubleshooting guide | `--issue` |
| `best-practices` | Best practices guide | `--topic` |
| `version` | Version information | `--json` |

## Configuration Migration

### Old Configuration Files
Old CLIs used various configuration approaches:
- Manual command-line options
- Some support for config files via `enhanced_cli.py`

### New Unified Configuration

The unified CLI supports:
```yaml
# config.yaml
name: "My Application"
jar_path: "app.jar"
main_class: "com.example.Main"
icon: "app.png"
category: "Development"
bundled_java: true
java_version: "17"
output_dir: "./dist"
```

Usage:
```bash
jar2appimage convert app.jar --config config.yaml
jar2appimage convert app.jar --save-config new-config.yaml
```

## Troubleshooting Migration

### Common Issues and Solutions

#### 1. Command Not Found
**Old:**
```bash
python jar2appimage_cli.py --help
```

**New:**
```bash
jar2appimage --help
# or
python -m jar2appimage.cli --help
```

#### 2. Platform Detection
**Old:**
```bash
python enhanced_jar2appimage_cli.py --check-platform
```

**New:**
```bash
jar2appimage check-platform
```

#### 3. Java Management
**Old:**
```bash
python enhanced_jar2appimage_cli.py --java-summary
```

**New:**
```bash
jar2appimage java-summary
```

#### 4. Help System
**Old:**
```bash
python cli_helper.py --examples
python enhanced_cli.py --help-detailed
```

**New:**
```bash
jar2appimage examples
jar2appimage convert --help
jar2appimage troubleshoot
jar2appimage best-practices
```

## Testing Your Migration

### Step 1: Test Basic Functionality
```bash
# Test help system
jar2appimage --help
jar2appimage examples

# Test platform check
jar2appimage check-platform

# Test Java summary
jar2appimage java-summary
```

### Step 2: Test Conversion
```bash
# Test with a simple JAR file
jar2appimage convert your-app.jar

# Test with bundling
jar2appimage convert your-app.jar --bundled --jdk-version 17

# Test validation
jar2appimage validate your-app.AppImage
```

### Step 3: Test Advanced Features
```bash
# Test verbose output
jar2appimage convert your-app.jar --verbose

# Test configuration
jar2appimage convert your-app.jar --save-config my-config.yaml
jar2appimage convert your-app.jar --config my-config.yaml
```

## Backward Compatibility

### Guaranteed Support
All legacy CLI invocations continue to work:
- Direct execution of old CLI files
- Existing scripts and automation
- Command-line argument patterns
- Exit codes and error messages

### Migration Timeline
- **Phase 1** (Current): Dual support - both old and new CLIs work
- **Phase 2** (Future): Deprecation warnings for old CLIs
- **Phase 3** (Future): Old CLIs removed (major version bump)

### Updating Scripts

#### Bash Scripts
```bash
# Old script
python jar2appimage_cli.py "$1" --bundled

# Updated script
jar2appimage convert "$1" --bundled

# Or use the unified CLI directly
python -m jar2appimage.cli convert "$1" --bundled
```

#### Python Scripts
```python
# Old way
import subprocess
subprocess.run(['python', 'jar2appimage_cli.py', 'app.jar', '--bundled'])

# New way
import subprocess
subprocess.run(['jar2appimage', 'convert', 'app.jar', '--bundled'])

# Or use the API directly
from jar2appimage.cli import main
main(['convert', 'app.jar', '--bundled'])
```

## Performance Improvements

### Faster Startup
- **Before**: Multiple 200-400 line files to parse
- **After**: Modular loading, only load needed components

### Better Memory Usage
- **Before**: All functionality loaded in each CLI
- **After**: Lazy loading of components

### Improved Error Handling
- **Before**: Inconsistent error messages
- **After**: Standardized error handling with helpful suggestions

## Advanced Features

### Logging
```bash
# Enable verbose logging
jar2appimage convert app.jar --verbose

# Log to file
jar2appimage convert app.jar --log-file conversion.log

# Both
jar2appimage convert app.jar --verbose --log-file conversion.log
```

### Dry Run
```bash
# See what would be done without actually creating AppImage
jar2appimage convert app.jar --dry-run --verbose
```

### Tool Validation
```bash
# Check all required tools
jar2appimage check-tools

# Get installation suggestions
jar2appimage check-tools --fix-suggestions

# Show only missing tools
jar2appimage check-tools --missing-only
```

## Getting Help

### Built-in Help
```bash
# General help
jar2appimage --help

# Command-specific help
jar2appimage convert --help
jar2appimage check-platform --help

# Examples
jar2appimage examples

# Troubleshooting
jar2appimage troubleshoot

# Best practices
jar2appimage best-practices
```

### Online Resources
- **Migration Guide**: This document
- **API Documentation**: Available in source code
- **Examples**: Run `jar2appimage examples`

## Summary

The unified CLI provides:
- ✅ **Single interface** for all functionality
- ✅ **Backward compatibility** with existing usage
- ✅ **Improved performance** and memory usage
- ✅ **Better error handling** and user experience
- ✅ **Clean architecture** for future development
- ✅ **Comprehensive testing** and validation

Migrating to the unified CLI is straightforward - most existing usage patterns continue to work, while new features provide enhanced functionality and better user experience.