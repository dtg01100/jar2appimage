# jar2appimage Quick Start Guide

Get started with jar2appimage and the new portable Java detection system in minutes!

## Installation

```bash
# Install using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <your-repo>
cd jar2appimage
./install.sh

# Or install with uv
uv pip install jar2appimage
```

## Basic Usage

### Simple Conversion
```bash
# Convert a simple JAR (auto-detects Java requirements)
python enhanced_jar2appimage_cli.py MyApp.jar

# With custom name and output directory  
python enhanced_jar2appimage_cli.py MyApp.jar -n "My Cool App" -o ~/Applications

# Verbose output for debugging
python enhanced_jar2appimage_cli.py MyApp.jar --verbose
```

## Portable Java Scenarios

### Scenario 1: System Java Available (Automatic Detection)

**Use Case**: Your system has Java installed and you want to use it.

```bash
# Auto-detects system Java and analyzes JAR requirements
python enhanced_jar2appimage_cli.py MyApp.jar

# Expected output:
# 🔍 Using enhanced portable Java detection...
# ✅ Java version determined: 17
# 🚀 Creating AppImage for MyApp.jar...
# ☕ Java bundling: DISABLED (using system Java)
# ✅ AppImage created successfully!
```

**Features**:
- ✅ Automatic system Java detection
- ✅ JAR requirement analysis
- ✅ Compatibility checking
- ✅ No downloads required

### Scenario 2: No System Java (Portable Java Offering)

**Use Case**: No Java on system, system offers to download portable Java.

```bash
# System analyzes JAR and offers portable Java
python enhanced_jar2appimage_cli.py MyApp.jar

# Expected consent prompt:
# 🔍 System Java Analysis: No compatible Java found
# 📦 Portable Java Analysis: JAR requires Java 17 or higher
# 
# ┌─────────────────────────────────────────────────────────────┐
# │ Download portable Java 21 (latest LTS)?                    │
# │                                                             │
# │ 📊 Details:                                                 │
# │ • Download size: ~45 MB                                    │
# │ • Estimated time: 30-60 seconds                           │
# │ • Version: OpenJDK 21 (Eclipse Temurin)                   │
# │ • Benefits: Self-contained, latest security updates       │
# │                                                             │
# │ Choose: [Y]es / [N]o / [I]nfo                              │
# └─────────────────────────────────────────────────────────────┘
```

**Response Options**:
- `Y` - Download and bundle portable Java
- `N` - Skip, continue without Java (may fail)
- `I` - Show detailed technical information

### Scenario 3: Bundled AppImage Creation with Portable Java

**Use Case**: Create completely self-contained AppImage with bundled Java.

```bash
# Create self-contained AppImage with portable Java
python enhanced_jar2appimage_cli.py MyApp.jar --bundled

# Expected output:
# 🎯 Auto-detected Java version: 21
# 📥 Portable Java download consented
# 🚀 Creating AppImage with portable Java support...
# 📦 Enhanced Java bundling: ENABLED
# 📥 Portable Java management: ENABLED
# ☕ Java version: 21
# 📥 Downloading portable Java 21...
# ✅ Java 21 downloaded successfully
# ✅ AppImage created successfully!
# 📦 Includes portable Java 21
#   Self-contained AppImage (no external dependencies)
```

**Features**:
- 📦 Self-contained AppImage
- 🔒 No external Java dependency
- 🌍 Works on any Linux distribution
- 🛡️ Latest security updates

## Step-by-Step Examples

### Example 1: Hello World Application

```bash
# Test with simple application
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --name "Hello World"

# If no Java detected, you'll see:
# 🔍 System Java Analysis: No compatible Java found
# Download Java 21? [Y/n]: Y
# ✅ AppImage created: Hello_World.AppImage
```

### Example 2: SQL Workbench/J (Complex Application)

```bash
# Download and package SQL Workbench/J
wget https://www.sql-workbench.eu/Workbench-Build132-with-optional-libs.zip
unzip Workbench-Build132-with-optional-libs.zip

# Create AppImage with bundled Java (≈45MB total)
python enhanced_jar2appimage_cli.py sqlworkbench.jar --name "SQL Workbench/J" --bundled

# Run it immediately
./SQL_Workbench_J.AppImage
```

### Example 3: Enterprise Application with Specific Java Version

```bash
# Force specific Java version for compatibility
python enhanced_jar2appimage_cli.py enterprise-app.jar \
  --name "Enterprise App" \
  --bundled \
  --jdk-version 11

# Clear cache if you need to re-download
python enhanced_jar2appimage_cli.py --clear-java-cache
```

## Java Management Commands

### Check Java Status
```bash
# Show comprehensive Java detection summary
python enhanced_jar2appimage_cli.py --java-summary

# Sample output:
# 🔍 Java Detection Summary:
#    Platform: Linux x86_64
#    Latest LTS: 21
#    System Java: 17 (OpenJDK)
#    Compatible: True
#    Command: /usr/bin/java
#    Download Cache: 2 files, 87 MB
#    Cached Versions: 17, 21
```

### Detect and Analyze System Java
```bash
# Get detailed Java information
python enhanced_jar2appimage_cli.py --detect-java

# Sample output:
# ✅ Found Java 17 (OpenJDK)
#    Command: /usr/bin/java
#    Compatible: True
#    JAVA_HOME: /usr/lib/jvm/java-17-openjdk
```

### Cache Management
```bash
# Clear Java download cache to free space
python enhanced_jar2appimage_cli.py --clear-java-cache

# Force re-download even if cached
python enhanced_jar2appimage_cli.py app.jar --bundled --force-download
```

## Advanced Options

### Java Version Control
```bash
# Use specific Java version
python enhanced_jar2appimage_cli.py app.jar --bundled --jdk-version 17

# Auto-select best version (default)
python enhanced_jar2appimage_cli.py app.jar --bundled --jdk-version auto

# Disable portable Java (system Java only)
python enhanced_jar2appimage_cli.py app.jar --no-portable

# System Java mode (no bundling)
python enhanced_jar2appimage_cli.py app.jar --no-bundled
```

### Platform and Architecture
```bash
# Check platform compatibility
python enhanced_jar2appimage_cli.py --check-platform

# Specify target architecture
python enhanced_jar2appimage_cli.py app.jar --arch x86_64
```

## Features Overview

- ✅ **Self-Contained** - Never requires system Java when using `--bundled`
- ✅ **Smart Detection** - Intelligent Java requirement analysis
- ✅ **User Consent** - Explicit opt-in for Java downloads
- ✅ **FUSE2-Free** - Works on modern Linux systems  
- ✅ **Automatic Dependencies** - Analyzes and bundles JAR dependencies
- ✅ **Cross-Platform** - Runs on any Linux distribution
- ✅ **Java LTS Versions** - Uses stable Java 8/11/17/21 LTS releases
- ✅ **On-Demand Downloads** - Downloads tools and JRE as needed (no manual setup)
- ✅ **Desktop Integration** - Creates proper .desktop entries
- ✅ **Smart Caching** - Downloads tools once, reuses them forever
- ✅ **Fallback Support** - Graceful degradation when downloads fail

## How It Works

### Portable Java Detection Flow

```
1. JAR Analysis
   ├─ Extract MANIFEST.MF
   ├─ Check for module-info.class
   └─ Identify Main-Class and requirements
   
2. System Java Detection
   ├─ Check PATH for java command
   ├─ Search common installation locations
   └─ Parse version and validate compatibility
   
3. Download Decision
   ├─ Compare system Java vs requirements
   ├─ Check module system compatibility
   └─ Apply user preferences
   
4. User Consent (if needed)
   ├─ Present analysis results
   ├─ Show download information
   └─ Wait for user choice
   
5. Java Download & Integration
   ├─ Download from Adoptium LTS
   ├─ Extract and optimize JRE
   └─ Integrate with AppImage
```

## Output and Results

### AppImage Characteristics
- **Size**: Typically 25-80MB (including Java runtime when bundled)
- **Java Version**: LTS versions for stability (defaults to Java 21)
- **Compatibility**: Works on any Linux distribution without FUSE2
- **Portability**: No external dependencies when bundled

### Success Indicators
```bash
✅ AppImage created successfully!
📦 File: /path/to/YourApp.AppImage
📏 Size: 45 MB

🎯 Usage:
   Run: ./YourApp.AppImage
   Options: ./YourApp.AppImage --help

📦 Enhanced Features:
   • Self-contained AppImage with portable Java
   • No external Java dependency required
   • Works on any Linux distribution
   • Latest security updates and features
   • Intelligent Java requirement detection
   • User-consented Java downloads
```

## Troubleshooting

### Java Detection Issues

#### Problem: No Java detected
```bash
# Check what's available
python enhanced_jar2appimage_cli.py --detect-java

# If no Java found, system will offer to download portable Java
# Response: Y to download Java 21 (latest LTS)
```

#### Problem: Incompatible Java version
```bash
# Get detailed analysis
python enhanced_jar2appimage_cli.py --java-summary

# Force specific version if needed
python enhanced_jar2appimage_cli.py app.jar --bundled --jdk-version 11
```

### Download Issues

#### Problem: Download failures
```bash
# Clear cache and retry
python enhanced_jar2appimage_cli.py --clear-java-cache
python enhanced_jar2appimage_cli.py app.jar --bundled --force-download

# Check network connectivity
curl -I https://api.adoptium.net/v3/info/release_versions?jvm=hotspot&arch=x64&os=linux&type=jre&version=21
```

#### Problem: Permission issues
```bash
# Check cache directory permissions
ls -la ~/.jar2appimage/

# Fix permissions if needed
chmod -R 755 ~/.jar2appimage/
```

### AppImage Issues

#### Problem: AppImage won't run
```bash
# Make executable
chmod +x YourApp.AppImage

# Check if it runs with verbose output
./YourApp.AppImage --help

# Verify Java integration
./YourApp.AppImage -XshowSettings:properties | grep java.home
```

#### Problem: Missing dependencies
```bash
# The tool warns about missing dependencies but continues
# Check the ext/ directory next to your JAR for missing libraries

# Run with verbose output to see what's missing
python enhanced_jar2appimage_cli.py app.jar --verbose
```

## Performance Tips

### Optimize Download Speed
```bash
# Use cached Java when possible
python enhanced_jar2appimage_cli.py app.jar --bundled  # Uses cache if available

# Clear cache only when necessary
python enhanced_jar2appimage_cli.py --clear-java-cache  # Free up space
```

### Minimize AppImage Size
```bash
# Use JRE instead of JDK (default)
python enhanced_jar2appimage_cli.py app.jar --bundled

# For applications that don't need full JDK
# The system automatically selects JRE when appropriate
```

### Faster Processing
```bash
# Skip dependency analysis (faster but less accurate)
python enhanced_jar2appimage_cli.py app.jar --no-dependencies

# Use system Java to avoid downloads
python enhanced_jar2appimage_cli.py app.jar --no-portable
```

## Common Use Cases

### Development and Testing
```bash
# Quick testing with system Java
python enhanced_jar2appimage_cli.py dev-app.jar --no-portable

# Test with specific Java version
python enhanced_jar2appimage_cli.py dev-app.jar --bundled --jdk-version 17
```

### Production Deployment
```bash
# Create self-contained AppImage for distribution
python enhanced_jar2appimage_cli.py production-app.jar \
  --name "Production App" \
  --bundled \
  --jdk-version 21

# Enterprise deployment with consistent Java
python enhanced_jar2appimage_cli.py enterprise-app.jar \
  --name "Enterprise App" \
  --bundled \
  --jdk-version 11 \
  --output /opt/applications/
```

### Batch Processing
```bash
# Process multiple JARs
for jar in *.jar; do
  python enhanced_jar2appimage_cli.py "$jar" --bundled --no-portable
done
```

This quick start guide covers the most common scenarios and use cases. For more detailed technical information, see the [Portable Java Guide](PORTABLE_JAVA_GUIDE.md) and [Contributing Guide](CONTRIBUTING.md).