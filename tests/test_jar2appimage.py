"""Tests for jar2appimage"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import platform

from jar2appimage.analyzer import JarDependencyAnalyzer
from jar2appimage.core import Jar2AppImage
from jar2appimage.runtime import JavaRuntimeManager


class TestJar2AppImage:
    def test_initialization(self):
        """Test Jar2AppImage initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "test.jar"
            jar_path.touch()

            converter = Jar2AppImage(str(jar_path), tmpdir)

            assert converter.jar_path == jar_path
            assert converter.output_dir == Path(tmpdir)
            assert converter.app_name == "test"
            assert converter.temp_dir.exists()

    def test_extract_main_class_from_manifest(self):
        """Test main class extraction from a real JAR manifest"""
        jar_path = "test_jars/HelloWorld.jar"
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = Jar2AppImage(jar_path, tmpdir)
            main_class = converter.extract_main_class()
            assert main_class == "HelloWorld"

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_create_appimage_end_to_end(self):
        """Test creating an AppImage from HelloWorld.jar and running it"""
        jar_path = "test_jars/HelloWorld.jar"
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the context manager to ensure cleanup
            with Jar2AppImage(jar_path, tmpdir) as converter:
                appimage_path = converter.create()

                # Ensure the AppImage was created
                assert Path(appimage_path).exists()
                assert Path(appimage_path).name == "HelloWorld.AppImage"

                # Make the AppImage executable
                Path(appimage_path).chmod(0o755)

                # Run the AppImage and capture output
                result = subprocess.run([appimage_path], capture_output=True, text=True, timeout=30)
                
                assert result.returncode == 0
                assert "Hello, World!" in result.stdout

    def test_analyze_dependencies(self):
        """Test dependency analysis"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "test.jar"
            jar_path.touch()

            converter = Jar2AppImage(str(jar_path), tmpdir)

            with patch.object(
                converter.dependency_analyzer, "analyze_jar"
            ) as mock_analyze:
                mock_analyze.return_value = {"found_local_jars": [], "missing_jars": []}

                result = converter.analyze_dependencies()

                assert "found_local_jars" in result
                assert "missing_jars" in result
                mock_analyze.assert_called_once_with(Path(jar_path))


class TestDependencyAnalyzer:
    def test_extract_dependencies_from_manifest(self):
        """Test manifest dependency extraction"""
        analyzer = JarDependencyAnalyzer()

        # This would need a proper JAR file for testing
        # For now, test method exists
        assert hasattr(analyzer, "extract_dependencies_from_manifest")

    def test_analyze_class_references(self):
        """Test class reference analysis"""
        analyzer = JarDependencyAnalyzer()

        # This would need a proper JAR file for testing
        # For now, test method exists
        assert hasattr(analyzer, "analyze_class_references")


class TestJavaRuntimeManager:
    def test_get_system_java(self):
        """Test system Java detection"""
        manager = JavaRuntimeManager()

        java_path = manager.get_system_java()

        # Should return a Path or None
        assert java_path is None or isinstance(java_path, Path)

    def test_initialization(self):
        """Test JavaRuntimeManager initialization"""
        manager = JavaRuntimeManager()

        assert manager.temp_dir.exists()
        assert manager.temp_dir.name.startswith("java_runtime_")

        # Cleanup
        manager.cleanup()
        assert not manager.temp_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__])
