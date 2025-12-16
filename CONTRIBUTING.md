# Contributing to jar2appimage

Thank you for contributing to jar2appimage! This guide covers development setup, testing procedures, and architecture details for the enhanced portable Java system.

## Development Setup

### 1. Repository Setup

```bash
# Clone the repository
git clone https://github.com/dtg01100/jar2appimage.git
cd jar2appimage

# Install development dependencies
uv pip install -e .

# Install appimagetool for testing
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

### 2. Portable Java System Architecture

The portable Java system consists of several core components:

```
jar2appimage/
├── portable_java_manager.py           # Core portable Java management
├── enhanced_jar2appimage_cli.py       # Enhanced CLI with portable Java
├── java_auto_downloader.py            # Existing auto-downloader (legacy)
├── smart_java_bundler.py             # Existing smart bundler
└── src/jar2appimage/
    ├── core.py                        # Core jar2appimage functionality
    └── java_bundler.py               # Core Java bundler
```

#### Core Classes

**`PortableJavaManager`**: Main class providing comprehensive Java detection and management
```python
class PortableJavaManager:
    def detect_system_java(self) -> Optional[Dict]
    def analyze_jar_requirements(self, jar_path: str) -> Dict[str, Any]
    def check_java_download_needed(self, system_java: Optional[Dict], jar_requirements: Dict) -> Tuple[bool, str]
    def offer_portable_java(self, download_needed: bool, reason: str, java_version: str) -> bool
    def download_portable_java(self, java_version: str, force: bool = False) -> Optional[str]
    def create_portable_java_integration(self, java_dir: str, appimage_dir: str) -> bool
```

**Convenience Functions**:
```python
def detect_and_manage_java(jar_path: str, interactive: bool = True) -> Tuple[Optional[str], bool]
def get_java_detection_summary() -> Dict[str, Any]
```

### 3. Key Development Files

#### Portable Java Manager (`portable_java_manager.py`)
- **Purpose**: Core Java detection, analysis, and management
- **Key Features**: System detection, JAR analysis, download management, user consent
- **Testing**: Unit tests for each component, integration tests

#### Enhanced CLI (`enhanced_jar2appimage_cli.py`)
- **Purpose**: CLI integration with portable Java features
- **Key Features**: Command-line interface, platform checking, error handling
- **Testing**: CLI tests, end-to-end tests

#### Java Detection Logic
The system follows this flow:

```
1. System Java Detection
   ├─ Check PATH for java command
   ├─ Search common installation locations
   ├─ Parse version output with regex
   ├─ Determine Java distribution type
   └─ Validate compatibility

2. JAR Requirements Analysis
   ├─ Extract and parse MANIFEST.MF
   ├─ Check for module-info.class files
   ├─ Identify Main-Class attribute
   └─ Parse Require-Capability directives

3. Download Decision Logic
   ├─ Compare system Java version with requirements
   ├─ Check for module system requirements
   ├─ Consider compatibility constraints
   └─ Apply user preferences

4. User Consent Flow
   ├─ Present analysis results
   ├─ Show download information with estimates
   ├─ Wait for user choice (Y/n/i)
   └─ Handle detailed information requests
```

## Testing the Portable Java System

### 1. Unit Testing

Test individual components:

```bash
# Test Java detection
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
java_info = manager.detect_system_java()
print(f'Detected Java: {java_info}')
"

# Test JAR analysis
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
requirements = manager.analyze_jar_requirements('test_jars/HelloWorld.jar')
print(f'JAR requirements: {requirements}')
"
```

### 2. Integration Testing

Test the complete workflow:

```bash
# Test with simple JAR
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --name "Hello World Test"

# Test with complex JAR
python enhanced_jar2appimage_cli.py test_jars/sqlworkbench.jar --name "SQLWorkbench Test" --bundled

# Test Java management commands
python enhanced_jar2appimage_cli.py --java-summary
python enhanced_jar2appimage_cli.py --detect-java
```

### 3. Testing Scenarios

#### Scenario 1: System Java Available
```bash
# Setup: Ensure Java is installed
java -version

# Test: Should detect and use system Java
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --name "System Java Test"
```

#### Scenario 2: No System Java (Portable Offering)
```bash
# Setup: Remove or hide system Java
export PATH=/usr/bin:/bin  # Remove Java from PATH

# Test: Should offer portable Java
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --name "Portable Java Test"
```

#### Scenario 3: Bundled AppImage Creation
```bash
# Test: Should download and bundle Java
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --bundled --name "Bundled Test"

# Verify result
ls -la *.AppImage
./HelloWorld_Test.AppImage
```

### 4. Test JAR Files

Available test files:
- `test_jars/HelloWorld.jar` - Simple application
- `test_jars/CLITester.jar` - CLI application with dependencies
- `test_jars/sqlworkbench.jar` - Complex GUI application
- `test_jars/junit-4.13.2.jar` - Library JAR

### 5. Testing Java Download and Caching

```bash
# Test cache functionality
python enhanced_jar2appimage_cli.py --clear-java-cache
python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --bundled --force-download

# Verify cache contents
ls -la ~/.jar2appimage/java_cache/downloads/
```

## Development Environment

### 1. Required Tools

- **Python 3.8+**: Core development
- **uv**: Fast Python package manager (recommended)
- **Git**: Version control
- **wget/curl**: For downloading test files
- **Java**: For testing system Java detection

### 2. Development Dependencies

```bash
# Install in development mode
uv pip install -e .

# Additional testing dependencies
uv pip install pytest pytest-cov black flake8 mypy
```

### 3. Code Style Guidelines

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Write docstrings for functions and classes using Google style
- **Line Length**: Maximum 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard library, third-party, local

#### Example Code Style
```python
from typing import Dict, Optional, Tuple, Any
import os
import sys

from portable_java_manager import PortableJavaManager


class EnhancedJar2AppImage:
    """Enhanced jar2appimage with portable Java support."""
    
    def __init__(self, jar_path: str, output_dir: str, bundled: bool = False) -> None:
        """Initialize enhanced jar2appimage.
        
        Args:
            jar_path: Path to the JAR file
            output_dir: Output directory for AppImage
            bundled: Whether to bundle portable Java
        """
        self.jar_path = jar_path
        self.output_dir = output_dir
        self.bundled = bundled
        self.portable_manager = PortableJavaManager()
```

### 4. Testing Procedures

#### Before Submitting Changes

1. **Run all tests**:
   ```bash
   pytest tests/ -v
   ```

2. **Test manually**:
   ```bash
   python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --bundled --name "Manual Test"
   ```

3. **Check code style**:
   ```bash
   black --check .
   flake8 .
   mypy portable_java_manager.py enhanced_jar2appimage_cli.py
   ```

4. **Test Java management**:
   ```bash
   python enhanced_jar2appimage_cli.py --java-summary
   python enhanced_jar2appimage_cli.py --detect-java
   python enhanced_jar2appimage_cli.py --clear-java-cache
   ```

## Architecture Details

### 1. Java Detection Strategy

The system uses a multi-layered detection approach:

1. **PATH Search**: Check if `java` is in PATH
2. **Common Locations**: Search `/usr/lib/jvm/`, `/opt/java/`, etc.
3. **Version Parsing**: Extract version using regex patterns
4. **Distribution Detection**: Identify vendor (OpenJDK, Oracle, etc.)
5. **Compatibility Check**: Validate against jar2appimage requirements

### 2. JAR Analysis Process

1. **Manifest Extraction**: Parse MANIFEST.MF for Main-Class
2. **Module Detection**: Look for module-info.class files
3. **Dependency Analysis**: Check for Java 9+ module requirements
4. **Version Requirements**: Extract minimum Java version requirements

### 3. Download Management

1. **API Integration**: Query Adoptium API for LTS versions
2. **Fallback Strategy**: Use hardcoded versions if API fails
3. **Cache Management**: Store downloads in `~/.jar2appimage/java_cache/`
4. **Verification**: Validate downloaded archives

### 4. User Consent System

The consent system provides:
- **Clear Language**: Non-technical explanations
- **Size Estimates**: Download size and time estimates
- **Detailed Information**: Technical details on request
- **Easy Cancellation**: Simple opt-out mechanism

## Debugging and Troubleshooting

### 1. Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Common Issues

#### Java Detection Failures
```bash
# Debug Java detection
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
result = manager.detect_system_java()
print(f'Result: {result}')
"
```

#### Download Issues
```bash
# Test download directly
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
result = manager.download_portable_java('21', force=True)
print(f'Download result: {result}')
"
```

#### JAR Analysis Problems
```bash
# Test JAR analysis
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
requirements = manager.analyze_jar_requirements('test_jars/HelloWorld.jar')
print(f'Requirements: {requirements}')
"
```

### 3. Cache Management

```bash
# Check cache contents
ls -la ~/.jar2appimage/java_cache/downloads/

# Clear cache
python enhanced_jar2appimage_cli.py --clear-java-cache

# Check cache info
python -c "
from portable_java_manager import PortableJavaManager
manager = PortableJavaManager()
info = manager.get_cache_info()
print(f'Cache info: {info}')
"
```

## Contributing Guidelines

### 1. Commit Messages

Use conventional commit format:
```
feat: add new portable Java detection feature
fix: resolve Java download timeout issue
docs: update quick start guide with portable Java examples
test: add integration tests for Java management commands
refactor: improve Java detection algorithm
```

### 2. Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/portable-java-enhancement
   ```

2. **Make changes and test**:
   ```bash
   # Test your changes
   python enhanced_jar2appimage_cli.py test_jars/HelloWorld.jar --bundled
   pytest tests/ -v
   ```

3. **Update documentation** if needed

4. **Submit pull request** with:
   - Clear description of changes
   - Testing results
   - Screenshots/output if applicable

### 3. Bug Reports

Include:
- Linux distribution and version
- Python version
- Steps to reproduce
- Error output with `--verbose`
- Java detection results (`--java-summary`)

### 4. Feature Requests

For new features:
- Describe the use case
- Provide implementation details
- Include testing strategy
- Consider backward compatibility

## Performance Considerations

### 1. Download Optimization
- Cache downloaded Java distributions
- Use JRE instead of JDK when possible
- Implement incremental downloads for large files

### 2. Detection Efficiency
- Cache Java detection results
- Use fast version detection methods
- Minimize file system searches

### 3. Memory Usage
- Stream large downloads
- Clean up temporary files
- Limit concurrent operations

## Security Considerations

### 1. Download Verification
- Verify Java distribution checksums
- Use HTTPS for all downloads
- Validate downloaded archives

### 2. User Safety
- Never auto-download without consent
- Provide clear download information
- Allow easy cancellation

### 3. Code Security
- Validate all inputs
- Use secure file operations
- Handle errors gracefully

## License

All contributions are licensed under the MIT License. By contributing, you agree that your contributions will be licensed under the same terms.

## Getting Help

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See [Portable Java Guide](PORTABLE_JAVA_GUIDE.md) for detailed technical information

Thank you for contributing to jar2appimage and helping make Java application packaging easier for everyone!