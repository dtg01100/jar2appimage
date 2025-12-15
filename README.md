# jar2appimage

A modern Python tool to convert Java JAR files into portable AppImages, bundling all necessary dependencies.

## ✨ Features

- 🚀 **Modern Python Package** - Installable via `uv` or `pip`
- 📦 **FUSE2-Free AppImages** - Works on modern Linux systems without FUSE2
- 🔒 **Fully Self-Contained** - Downloads portable JRE, never relies on system Java
- 🔄 **On-Demand Downloads** - Fetches JRE and tools as needed
- 🧩 **Smart Dependency Analysis** - Automatically detects and bundles JAR dependencies  
- ☕ **Portable Java Runtime** - Bundles optimized JDK/JRE from Adoptium LTS versions (8, 11, 17, 21, 23)
- 🎯 **Automatic Icons** - Generates placeholder icons if none provided
- 🖥️ **Desktop Integration** - Creates proper .desktop files and menu entries
- 🐧 **Universal Compatibility** - Runs on any Linux distribution

## Requirements

- Python 3.6+
- Java Runtime Environment (JRE) 8 or later
- AppImageKit (appimagetool)
- Linux system

## Installation

### Recommended: Using uv (modern Python package manager)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install jar2appimage
git clone <repository-url>
cd jar2appimage
./install.sh
```

### Alternative: Traditional setup

```bash
# Clone the repository
git clone <repository-url>
cd jar2appimage

# Run the legacy setup script
./setup.sh
```

### From PyPI (when published)

```bash
uv pip install jar2appimage
```

## Usage

Basic usage:
```bash
python3 jar2appimage.py your-app.jar
```

With options:
```bash
python3 jar2appimage.py your-app.jar \
    -o output/directory \
    -n "My Application" \
    --java-version 17
```

### Options

- `jar`: Input JAR file (required)
- `-o, --output`: Output directory (default: current directory)
- `-n, --name`: Application name (default: JAR filename)
- `--java-version`: Java version to bundle (default: 17)

## How It Works

1. **AppDir Creation**: Creates the standard AppDir directory structure
2. **JAR Analysis**: Extracts manifest information and main class
3. **Java Runtime**: Bundles the appropriate Java runtime
4. **Desktop Integration**: Creates .desktop files and AppRun script
5. **AppImage Generation**: Uses appimagetool to create the final AppImage

## Examples

Convert a simple JAR:
```bash
jar2appimage your-app.jar
```

Convert with custom name and output directory:
```bash
jar2appimage your-app.jar -n "Cool App" -o ~/Applications/
```

Real-world example - SQL Workbench/J:
```bash
# Download SQL Workbench/J
wget https://www.sql-workbench.eu/Workbench-Build132-with-optional-libs.zip
unzip Workbench-Build132-with-optional-libs.zip

# Create AppImage
jar2appimage sqlworkbench.jar -n "SQL Workbench/J" -o ~/Applications

# Result: 27MB portable AppImage with bundled JRE and all dependencies
```

Convert with custom name and output directory:
```bash
python3 jar2appimage.py MyApplication.jar -n "Cool App" -o ~/Applications/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Automatic dependency analysis
- [ ] Java runtime optimization with jlink
- [ ] Support for external dependencies
- [ ] GUI interface
- [ ] Icon customization
- [ ] Splash screen support