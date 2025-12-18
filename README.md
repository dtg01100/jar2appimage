# jar2appimage

A Python tool to convert Java JAR files into portable AppImage executables with intelligent Java detection and management.

## Features

- Converts JAR files to AppImage format
- **Automatic on-demand download of appimagetool** - no need to install separately
- **🆕 Portable Java Support** - Intelligent Java detection and user-consented downloads
- **🔍 Smart Java Analysis** - Automatic JAR requirement analysis and version detection
- **📦 Self-Contained AppImages** - Bundle portable Java for true portability
- **🤝 User Consent System** - Explicit opt-in for Java downloads with clear information
- **⚡ LTS Java Versions** - Automatic selection of latest stable Java releases (8, 11, 17, 21)
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

### Basic usage (automatic detection)
```bash
python enhanced_jar2appimage_cli.py application.jar
```

### With custom output directory:
```bash
python enhanced_jar2appimage_cli.py application.jar --output ~/Applications
```

### Bundled with portable Java (consent required)
```bash
python enhanced_jar2appimage_cli.py application.jar --bundled
```

### Java management commands
```bash
# Show Java detection summary
python enhanced_jar2appimage_cli.py --java-summary

# Detect and analyze system Java
python enhanced_jar2appimage_cli.py --detect-java

# Clear Java download cache
python enhanced_jar2appimage_cli.py --clear-java-cache

# Disable portable Java detection (use system Java only)
python enhanced_jar2appimage_cli.py application.jar --no-portable
```

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

## Usage Examples

### System Java Available (Automatic Detection)
```bash
# Detects system Java and analyzes JAR requirements
python enhanced_jar2appimage_cli.py application.jar

# Output will show:
# ✅ Java version determined: 17
# 🚀 Creating AppImage for application.jar...
# ✅ AppImage created successfully!
```

### No System Java (Portable Java Offering)
```bash
# System will analyze JAR and offer portable Java
python enhanced_jar2appimage_cli.py application.jar

# Output will show consent prompt:
# 🔍 System Java Analysis: No compatible Java found
# 📦 Portable Java Analysis: JAR requires Java 17 or higher
# 
# Download Java 21 (latest LTS)? [Y/n/i]:
# Y = Download and bundle
# n = Skip, use system Java if available  
# i = Show detailed information
```

### Bundled AppImage Creation
```bash
# Create self-contained AppImage with portable Java
python enhanced_jar2appimage_cli.py application.jar --bundled

# Output will show:
# 🎯 Auto-detected Java version: 21
# 📥 Portable Java download consented
# 📦 Enhanced Java bundling: ENABLED
# ✅ AppImage created successfully!
# 📦 Includes portable Java 21
#   Self-contained AppImage (no external dependencies)
```

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