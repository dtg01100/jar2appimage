# Contributing to jar2appimage

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dtg01100/jar2appimage.git
   cd jar2appimage
   ```

2. Install appimagetool for testing:
   ```bash
   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x appimagetool-x86_64.AppImage
   ```

## Testing

Test with sample JAR files:
```bash
python3 portable_bundler.py test_jars/HelloWorld.jar --name "Hello World"
```

## Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Write docstrings for functions and classes

## Commit Messages

Use conventional commit format:
```
feat: add new feature
fix: bug fix
docs: documentation changes
test: add tests
```

## Pull Requests

1. Create a feature branch from master
2. Make changes and test them
3. Update documentation if needed
4. Submit a pull request

## Bug Reports

When reporting bugs, include:
- Linux distribution and version
- Python version
- Steps to reproduce
- Error output

## License

Contributions are licensed under the MIT License.