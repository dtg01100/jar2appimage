# jar2appimage

A Python tool to convert Java JAR files into portable AppImage executables with intelligent Java detection and management.

## Features

- Converts JAR files to AppImage format with a single command
- **Automatic on-demand download of appimagetool** - no need to install separately
- **🆕 Default to Portable Java** - Bundles Java by default (opt-out with --no-bundled) for maximum portability
- **📦 Automatic Supporting Files Bundling** - Detects and bundles configs, assets, data, and libraries by default
- **🔍 Smart Java Analysis** - Automatic JAR requirement analysis and version detection
- **🤝 User Consent System** - Explicit opt-in for Java downloads with clear information
- **⚡ LTS Java Versions** - Automatic selection of latest stable Java releases (8, 11, 17, 21)
- **✨ Does The Right Thing** - Just run `python enhanced_jar2appimage_cli.py your.jar` for the best outcome
- JAR dependency analysis and classpath management
- Desktop integration with .desktop files
- Cross-platform AppImage generation
- Smart caching and fallback support

## Portable Java Support

The **Portable Java Detection and Management System** is a comprehensive solution that provides intelligent Java detection, user consent-based downloads, and seamless integration with existing bundling workflows.

### 🔍 **Automatic Java Detection**
- **Comprehensive Detection**: Finds Java installations across multiple locations
- **Version Analysis**: Extracts detailed version information including major, minor, patch
- **Compatibility Validation**: Checks if system Java meets jar2appimage requirements
- **Java Type Detection**: Identifies OpenJDK, Oracle JDK, Amazon Corretto, Eclipse Temurin, etc.
- **Architecture Support**: Detects 32-bit vs 64-bit and maps architectures correctly

### 📦 **LTS Java Versions**
- **Current Support**: Java 21 (latest LTS as of 2025-12-16)
- **Auto-Detection**: Queries Adoptium API for latest LTS versions
- **Fallback System**: Uses hardcoded LTS versions when API is unavailable
- **Version Prioritization**: Prefers LTS versions over non-LTS for stability

### 🤝 **User Consent Mechanism**
- **Clear Prompts**: Non-technical language explaining what will be downloaded
- **Size Estimates**: Provides download size and time estimates
- **Detailed Information**: Shows technical details and benefits on request
- **Opt-in Approach**: Users explicitly consent before any downloads
- **Cancellation Support**: Users can cancel without proceeding

### ⚙️ **Smart Bundling Integration**
- **Intelligent Analysis**: Analyzes JAR files for Java version requirements
- **Module Detection**: Identifies Java 9+ modules and their requirements
- **Automatic Recommendations**: Suggests portable Java when system Java is incompatible
- **Fallback Support**: Multiple download strategies with fallbacks

## Requirements

- Python 3.8+
- Linux system (x86_64 or aarch64)
- Internet connection (for first-time appimagetool download)
- Optional: Java runtime for enhanced detection (system Java auto-detected)

## Installation

### Using uv (recommended)

```bash
# Install using uv
curl -LsSf https://astral.sh/uv/install.sh | sh
cd jar2appimage
bash install.sh
```

### Manual installation

```bash
git clone https://github.com/dtg01100/jar2appimage.git
cd jar2appimage
uv tool install .
```

## Usage

### One Command Usage (Does the Right Thing™)
```bash
python enhanced_jar2appimage_cli.py application.jar
```

This single command will automatically:
- ✅ Detect if system Java is available and compatible
- ✅ Automatically bundle the latest LTS Java (21) if needed
- ✅ Analyze your JAR for specific requirements
- ✅ Bundle supporting files (configs, data, assets) if found
- ✅ Create a self-contained, portable AppImage
- ✅ Ask for consent when downloading Java (or use `--assume-yes` for automation)

### With custom output directory:
```bash
python enhanced_jar2appimage_cli.py application.jar --output ~/Applications
```

### Override defaults (opt-out approach):
```bash
# Use system Java only (opt-out of Java bundling)
python enhanced_jar2appimage_cli.py application.jar --no-bundled

# Bundle Java but exclude supporting files
python enhanced_jar2appimage_cli.py application.jar --no-supporting-files
```

### Java management commands
```bash
# Show Java detection summary
python enhanced_jar2appimage_cli.py --java-summary

# Detect and analyze system Java
python enhanced_jar2appimage_cli.py --detect-java

# Clear Java download cache
python enhanced_jar2appimage_cli.py --clear-java-cache

# Use system Java only (opt-out of portable Java detection)
python enhanced_jar2appimage_cli.py application.jar --no-portable

# Skip bundling supporting files (config, assets, etc.)
python enhanced_jar2appimage_cli.py application.jar --no-supporting-files
```

### Quick Start - Just Works! ⚡

Need to convert your JAR to an AppImage? Just run:

```bash
python enhanced_jar2appimage_cli.py your-application.jar
```

That's it! The system will:

1. **Detect your situation** - Check if system Java is available and compatible
2. **Offer portable Java** - Automatically suggest bundling the latest LTS Java if needed
3. **Analyze your app** - Scan your JAR for specific Java version requirements
4. **Bundle supporting files** - Automatically detect and include related config files and resources
5. **Create portable AppImage** - Generate a self-contained executable that works everywhere
6. **Ask for consent** - Only downloads Java when you say yes (or use `--assume-yes` to skip prompts)

### First Run

On first use, `jar2appimage` will automatically download `appimagetool` to `~/.cache/jar2appimage/`. For portable Java features, the system will ask for your consent before downloading any Java distributions.

### Manual appimagetool Installation

If you prefer to use a system-installed `appimagetool`, it will be detected and used automatically:

```bash
# Download appimagetool manually
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

## Philosophy - "Do The Right Thing" ✨

The default behavior has been carefully designed for the best user experience:

- **Portable by default** - Your JAR + Java Runtime in a single file
- **Self-contained** - Works on any Linux without external dependencies
- **Smart detection** - Automatically bundles supporting files and configs
- **User-controlled** - Consent required for all downloads
- **One command** - Just `python enhanced_jar2appimage_cli.py your-app.jar` and you're done

The defaults are chosen for maximum compatibility and usability. Use `--no-bundled` or `--no-supporting-files` to opt out of specific behaviors.

## Usage Examples

### Default Behavior (Self-Contained AppImage Creation)
```bash
# Create self-contained AppImage with bundled Java and supporting files (default)
python enhanced_jar2appimage_cli.py application.jar

# Output will show:
# 🎯 Auto-detected Java version: 21
# 📥 Portable Java download consented
# 📦 Enhanced Java bundling: ENABLED
# ✅ AppImage created successfully!
# 📦 Includes portable Java 21
#   Self-contained AppImage (no external dependencies)
```

### System Java Mode (Opt-Out of Bundling)
```bash
# Use system Java only (opt-out of Java bundling)
python enhanced_jar2appimage_cli.py application.jar --no-bundled

# Output will show:
# ✅ Java version determined: 17
# 🚀 Creating AppImage for application.jar...
# ✅ AppImage created successfully!
```

### Supporting Files Bundling
```bash
# By default, supporting files are automatically detected and bundled:
# - Config files: *.properties, *.json, *.yml, *.xml, etc.
# - Directories: config/, data/, assets/, lib/, etc.
# - Files matching JAR name pattern

# To exclude supporting files (opt-out):
python enhanced_jar2appimage_cli.py application.jar --no-supporting-files
````

### Advanced Options
```bash
# Force specific Java version
python enhanced_jar2appimage_cli.py application.jar --bundled --jdk-version 17

# Force download even if cached
python enhanced_jar2appimage_cli.py application.jar --bundled --force-download

# System Java mode only
python enhanced_jar2appimage_cli.py application.jar --no-bundled --no-portable
```

## Options

- `--name, -n`: Application name
- `--output, -o`: Output directory
- `--arch, -a`: Target architecture (auto-detected by default)
- `--no-bundled`: Create AppImage using system Java only (opt-out of bundling)
- `--bundled`: Create AppImage with bundled portable Java (default behavior)
- `--no-supporting-files`: Disable bundling of supporting files (config, assets, etc.)
- `--no-portable`: Disable portable Java detection and offering
- `--jdk-version`: Java version for bundling (8, 11, 17, 21, auto)
- `--java-summary`: Show Java detection summary and exit
- `--detect-java`: Detect and analyze system Java installation
- `--clear-java-cache`: Clear Java download cache

## Real-World Examples

### Create AppImage with System Java:
```bash
python enhanced_jar2appimage_cli.py myapp.jar --name "My Application" --no-portable
```

### Create Self-Contained AppImage:
```bash
python enhanced_jar2appimage_cli.py myapp.jar --name "My Application" --bundled
```

### Test with SQL Workbench/J:
```bash
python enhanced_jar2appimage_cli.py test_jars/sqlworkbench.jar --name SQLWorkbench --bundled
```

### Java Management:
```bash
# Check what Java is available on your system
python enhanced_jar2appimage_cli.py --java-summary

# Clear downloaded Java to free space
python enhanced_jar2appimage_cli.py --clear-java-cache
```

## Technical Details

### Portable Java Architecture
- **Core Components**: `portable_java_manager.py`, `enhanced_jar2appimage_cli.py`
- **Download Sources**: Adoptium (Eclipse Temurin) LTS releases
- **Cache Location**: `~/.jar2appimage/java_cache/downloads/`
- **Integration**: Seamless integration with existing jar2appimage workflow
- **Fallback Support**: Multiple download strategies and graceful degradation

### Compatibility and Support
- **Java Versions**: LTS versions 8, 11, 17, 21 (current latest)
- **Architectures**: x86_64, aarch64
- **Package Types**: JRE (smaller), JDK (full development)
- **Compatibility Range**: Java 8 minimum, Java 21 maximum tested

## Troubleshooting

### Java Detection Issues
```bash
# Get detailed Java information
python enhanced_jar2appimage_cli.py --detect-java

# Show comprehensive summary
python enhanced_jar2appimage_cli.py --java-summary
```

### Download Issues
```bash
# Clear cache and retry
python enhanced_jar2appimage_cli.py --clear-java-cache
python enhanced_jar2appimage_cli.py application.jar --bundled --force-download
```

### Permission Issues
```bash
# Make AppImage executable
chmod +x YourApp.AppImage

# Run it
./YourApp.AppImage
```

## License

MIT License - see LICENSE file for details.

## Additional Documentation

- [Quick Start Guide](QUICKSTART.md) - Step-by-step examples for different scenarios
- [Contributing Guide](CONTRIBUTING.md) - Development setup and testing procedures
- [Portable Java Guide](PORTABLE_JAVA_GUIDE.md) - Comprehensive technical documentation