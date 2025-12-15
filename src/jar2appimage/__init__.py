# jar2appimage package initialization

__version__ = "0.1.0"

# Import main classes directly to avoid circular imports
try:
    from jar2appimage.core import Jar2AppImage
except ImportError as e:
    print(f"Warning: Could not import core module: {e}")

try:
    from jar2appimage.analyzer import JarDependencyAnalyzer
except ImportError as e:
    print(f"Warning: Caution: Could not import analyzer module: {e}")

try:
    from jar2appimage.runtime import JavaRuntimeManager
except ImportError as e:
    print(f"Warning: Caution: Could not import runtime module: {e}")

__all__ = ["Jar2AppImage", "JarDependencyAnalyzer", "JavaRuntimeManager"]
