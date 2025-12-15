# jar2appimage Quick Start Guide

## Installation

```bash
# Install using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <your-repo>
cd jar2appimage
./install.sh

# Or install with pip
pip install jar2appimage
```

## Basic Usage

```bash
# Convert a simple JAR
jar2appimage MyApp.jar

# With custom name and output directory  
jar2appimage MyApp.jar -n "My Cool App" -o ~/Applications

# Specify Java version
jar2appimage MyApp.jar --java-version 21

# Skip dependency analysis (faster)
jar2appimage MyApp.jar --no-dependencies

# Verbose output
jar2appimage MyApp.jar --verbose
```

## Real-World Example: SQL Workbench/J

```bash
# Download SQL Workbench/J
wget https://www.sql-workbench.eu/Workbench-Build132-with-optional-libs.zip
unzip Workbench-Build132-with-optional-libs.zip

# Create AppImage (≈30MB with bundled Java 17)
jar2appimage sqlworkbench.jar -n "SQL Workbench/J" -o ~/Applications

# Run it
~/Applications/SQL_Workbench_J.AppImage
```

## Features

- ✅ **Self-Contained** - Never requires system Java
- ✅ **FUSE2-Free** - Works on modern Linux systems  
- ✅ **Automatic Dependencies** - Analyzes and bundles JAR dependencies
- ✅ **Cross-Platform** - Runs on any Linux distribution
- ✅ **Java LTS Versions** - Uses stable Java 8/11/17/21/23 LTS releases
- ✅ **On-Demand Downloads** - Downloads appimagetool and JRE as needed (no manual setup)
- ✅ **Desktop Integration** - Creates proper .desktop entries
- ✅ **Smart Caching** - Downloads tools once, reuses them forever

## How It Works

1. **Analyze** - Reads JAR manifest and class dependencies
2. **Download Tools** - Fetches appimagetool on first run (cached in `~/.cache/jar2appimage/`)
3. **Download Java** - (Optional) Fetches portable JDK/JRE from Adoptium LTS releases
4. **Extract** - Creates minimal JRE with essential binaries and libraries
5. **Bundle** - Copies JAR, dependencies, and JRE into AppDir
6. **Package** - Creates modern AppImage using appimagetool

## Output

- **AppImage Size**: Typically 25-50MB (including Java runtime)
- **Java Version**: LTS versions for stability (defaults to Java 17)
- **Compatibility**: Works on any Linux distribution without FUSE2
- **Portability**: No external dependencies required

## Troubleshooting

### Download Issues
```bash
# If JDK download fails, the tool creates minimal structure and continues
# This allows the AppImage to be built even with network issues
```

### Permission Issues
```bash
# Make AppImage executable
chmod +x YourApp.AppImage

# Run it
./YourApp.AppImage
```

### Missing Dependencies
```bash
# The tool warns about missing dependencies but continues
# Check the ext/ directory next to your JAR for missing libraries
```