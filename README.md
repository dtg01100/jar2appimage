# jar2appimage

A Python tool to convert Java JAR files into portable AppImage executables.

## Features

- Converts JAR files to AppImage format
- Supports bundled Java runtime or system Java usage
- Automatic Java version detection and downloading
- JAR dependency analysis and classpath management
- Desktop integration with .desktop files
- Cross-platform AppImage generation

## Requirements

- Python 3.6+
- Linux system
- appimagetool (AppImageKit)

## Installation

Clone the repository:

```bash
git clone https://github.com/dtg01100/jar2appimage.git
cd jar2appimage
```

## Usage

Basic usage with system Java:
```bash
python3 portable_bundler.py your-app.jar
```

With bundled Java:
```bash
python3 auto_java_bundler.py your-app.jar --name "My App"
```

### Scripts

- `portable_bundler.py`: Creates AppImage using system Java
- `auto_java_bundler.py`: Downloads and bundles Java runtime
- `smart_java_bundler.py`: Discovers Java download URLs

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