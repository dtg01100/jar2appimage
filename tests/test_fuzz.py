"""Fuzz testing for jar2appimage with malformed JAR files"""

import tempfile
import zipfile
from pathlib import Path
import pytest
import platform

from jar2appimage.core import Jar2AppImage


class TestFuzzJAR:
    """Fuzz testing with malformed or edge-case JAR files"""

    def create_malformed_jar(self, tmpdir: str, corruption_type: str) -> str:
        """Create a malformed JAR file for testing"""
        jar_path = Path(tmpdir) / f"malformed_{corruption_type}.jar"

        if corruption_type == "empty":
            # Create empty file
            jar_path.touch()
            return str(jar_path)

        if corruption_type == "not_zip":
            # Create file that's not a ZIP/JAR
            jar_path.write_text("This is not a JAR file")
            return str(jar_path)

        if corruption_type == "corrupted_zip":
            # Create corrupted ZIP file
            jar_path.write_bytes(b"PK\x03\x04corrupted")
            return str(jar_path)

        if corruption_type == "missing_manifest":
            # Create JAR without MANIFEST.MF
            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("com/example/Main.class", b"fake class data")
            return str(jar_path)

        if corruption_type == "empty_manifest":
            # Create JAR with empty MANIFEST.MF
            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "")
                zf.writestr("com/example/Main.class", b"fake class data")
            return str(jar_path)

        if corruption_type == "malformed_manifest":
            # Create JAR with malformed MANIFEST.MF
            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "Not a valid manifest\nInvalid format")
                zf.writestr("com/example/Main.class", b"fake class data")
            return str(jar_path)

        if corruption_type == "huge_file":
            # Create JAR with very large file
            with zipfile.ZipFile(jar_path, 'w') as zf:
                # Add a large file (but not too large for testing)
                large_data = b"x" * (1024 * 1024)  # 1MB
                zf.writestr("large_file.dat", large_data)
                zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: com.example.Main\n")
                zf.writestr("com/example/Main.class", b"fake class data")
            return str(jar_path)

        return str(jar_path)

    def test_empty_jar_file(self):
        """Test handling of empty JAR file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "empty")

            converter = Jar2AppImage(jar_path, tmpdir)

            # Should handle gracefully
            main_class = converter.extract_main_class()
            assert main_class is None  # No manifest to read

    def test_non_zip_jar_file(self):
        """Test handling of file that's not a ZIP/JAR"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "not_zip")

            converter = Jar2AppImage(jar_path, tmpdir)

            # Should handle gracefully
            main_class = converter.extract_main_class()
            assert main_class is None

    def test_corrupted_zip_jar_file(self):
        """Test handling of corrupted ZIP file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "corrupted_zip")

            converter = Jar2AppImage(jar_path, tmpdir)

            # Should handle gracefully
            main_class = converter.extract_main_class()
            assert main_class is None

    def test_jar_without_manifest(self):
        """Test JAR file without MANIFEST.MF"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "missing_manifest")

            converter = Jar2AppImage(jar_path, tmpdir)

            main_class = converter.extract_main_class()
            assert main_class is None  # No Main-Class in manifest

    def test_jar_with_empty_manifest(self):
        """Test JAR file with empty MANIFEST.MF"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "empty_manifest")

            converter = Jar2AppImage(jar_path, tmpdir)

            main_class = converter.extract_main_class()
            assert main_class is None  # No Main-Class entry

    def test_jar_with_malformed_manifest(self):
        """Test JAR file with malformed MANIFEST.MF"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "malformed_manifest")

            converter = Jar2AppImage(jar_path, tmpdir)

            main_class = converter.extract_main_class()
            assert main_class is None  # Cannot parse malformed manifest

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage creation only supported on Linux")
    def test_large_jar_file(self):
        """Test handling of JAR with large files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = self.create_malformed_jar(tmpdir, "huge_file")

            converter = Jar2AppImage(jar_path, tmpdir)

            # Should still work with large files
            main_class = converter.extract_main_class()
            assert main_class == "com.example.Main"

            # Test dependency analysis on large JAR
            dependencies = converter.analyze_dependencies()
            assert isinstance(dependencies, dict)

    def test_dependency_analysis_on_malformed_jars(self):
        """Test dependency analysis robustness with malformed JARs"""
        test_cases = ["empty", "not_zip", "corrupted_zip", "missing_manifest", "empty_manifest", "malformed_manifest"]

        for corruption_type in test_cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                jar_path = self.create_malformed_jar(tmpdir, corruption_type)

                converter = Jar2AppImage(jar_path, tmpdir)

                # Dependency analysis should not crash
                dependencies = converter.analyze_dependencies()
                assert isinstance(dependencies, dict)
                assert "found_local_jars" in dependencies
                assert "missing_jars" in dependencies

    def test_unicode_filenames_in_jar(self):
        """Test JAR with Unicode filenames"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "unicode_jar.jar"

            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: test.Main\n")
                zf.writestr("test/Main.class", b"fake class")
                zf.writestr("测试/文件.class", b"unicode filename")  # Chinese characters
                zf.writestr("файл.class", b"cyrillic")  # Cyrillic characters

            converter = Jar2AppImage(str(jar_path), tmpdir)

            main_class = converter.extract_main_class()
            assert main_class == "test.Main"

            dependencies = converter.analyze_dependencies()
            assert isinstance(dependencies, dict)

    def test_nested_jar_files(self):
        """Test JAR containing other JAR files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "nested_jar.jar"

            # Create a nested JAR structure
            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: com.example.Main\n")

                # Create a fake nested JAR
                nested_jar_data = b"PK\x03\x04nested jar data"
                zf.writestr("lib/nested.jar", nested_jar_data)

                zf.writestr("com/example/Main.class", b"main class")
                zf.writestr("com/example/Util.class", b"util class")

            converter = Jar2AppImage(str(jar_path), tmpdir)

            main_class = converter.extract_main_class()
            assert main_class == "com.example.Main"

            dependencies = converter.analyze_dependencies()
            assert isinstance(dependencies, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])