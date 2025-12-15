# jar2appimage

A Python tool to convert Java JAR files into portable AppImage executables.

## Features

- Converts JAR files to AppImage format
- **Automatic on-demand download of appimagetool** - no need to install separately
- Supports bundled Java runtime or system Java usage
- Automatic Java version detection and downloading
- JAR dependency analysis and classpath management
- Desktop integration with .desktop files
- Cross-platform AppImage generation

## Requirements

- Python 3.8+
- Linux system (x86_64 or aarch64)
- Internet connection (for first-time appimagetool download)

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

Basic usage:
```bash
jar2appimage your-app.jar
```

With custom output directory:
```bash
jar2appimage your-app.jar --output ~/Applications
```

### First Run

On first use, `jar2appimage` will automatically download `appimagetool` to `~/.cache/jar2appimage/`. Subsequent runs will use the cached version.

### Manual appimagetool Installation

If you prefer to use a system-installed `appimagetool`, it will be detected and used automatically:

```bash
# Download appimagetool manually
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

### Options

- `--name, -n`: Application name
- `--output, -o`: Output directory
- `--arch, -a`: Target architecture (auto-detected by default)

## Examples

Create AppImage with system Java:
```bash
python3 portable_bundler.py myapp.jar --name "My Application"
```

Create AppImage with bundled Java:
```bash
python3 auto_java_bundler.py myapp.jar --name "My Application"
```

Test with SQL Workbench/J:
```bash
python3 portable_bundler.py test_jars/sqlworkbench.jar --name SQLWorkbench
```

## License

MIT License - see LICENSE file for details.