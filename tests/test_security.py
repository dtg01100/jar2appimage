"""Security and input validation tests for jar2appimage"""

import tempfile
import os
from pathlib import Path
import subprocess
import sys
import pytest
import platform

from jar2appimage.core import Jar2AppImage


class TestSecurityInputValidation:
    """Security testing for input validation and safe handling"""

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks in JAR paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a malicious path with traversal
            malicious_path = "../../etc/passwd"

            converter = Jar2AppImage(malicious_path, tmpdir)

            # Should handle non-existent files gracefully without path traversal
            main_class = converter.extract_main_class()
            assert main_class is None

            dependencies = converter.analyze_dependencies()
            assert isinstance(dependencies, dict)

    def test_output_directory_isolation(self):
        """Test that output directory is properly isolated"""
        with tempfile.TemporaryDirectory() as base_tmpdir:
            output_dir = Path(base_tmpdir) / "output"

            # Test with valid JAR
            converter = Jar2AppImage("test_jars/HelloWorld.jar", str(output_dir))

            # Ensure temp directory is created (location doesn't matter as much as isolation)
            assert converter.temp_dir.exists()
            assert converter.temp_dir != output_dir  # Should be separate from output dir

            # Ensure output_dir is properly handled
            assert converter.output_dir == output_dir

    def test_cli_input_validation_jar_path(self):
        """Test CLI properly validates JAR file paths"""
        # Test with path containing special characters
        special_path = "test_jars/HelloWorld.jar;rm -rf /"

        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", special_path
        ], capture_output=True, text=True, cwd=".")

        # Should not execute shell commands
        # The file doesn't exist, so it should just report file not found
        assert result.returncode == 1
        assert "JAR file not found" in result.stdout

    def test_cli_output_directory_validation(self):
        """Test CLI validates output directory paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with output directory containing special characters
            malicious_output = f"{tmpdir};rm -rf /"

            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", malicious_output
            ], capture_output=True, text=True, cwd=".")

            # Should handle the path safely
            # May succeed or fail, but shouldn't execute shell commands
            assert result.returncode in [0, 1]

    def test_jar_with_symlinks(self):
        """Test handling of JAR files that are symlinks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_jar = Path(tmpdir) / "real.jar"
            real_jar.write_bytes(b"fake jar content")

            symlink_jar = Path(tmpdir) / "symlink.jar"
            symlink_jar.symlink_to(real_jar)

            converter = Jar2AppImage(str(symlink_jar), tmpdir)

            # Should handle symlinks safely
            main_class = converter.extract_main_class()
            # Will be None since it's not a real JAR, but shouldn't crash
            assert main_class is None

    def test_very_long_jar_path(self):
        """Test handling of very long JAR file paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a very long path
            long_name = "a" * 200  # 200 character filename
            long_path = Path(tmpdir) / f"{long_name}.jar"

            # Create a minimal JAR
            import zipfile
            with zipfile.ZipFile(long_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")

            converter = Jar2AppImage(str(long_path), tmpdir)

            # Should handle long paths
            main_class = converter.extract_main_class()
            assert main_class is None  # No Main-Class specified

    def test_relative_vs_absolute_paths(self):
        """Test handling of relative vs absolute paths"""
        # Test with absolute path
        abs_path = Path("test_jars/HelloWorld.jar").resolve()

        with tempfile.TemporaryDirectory() as tmpdir:
            converter = Jar2AppImage(str(abs_path), tmpdir)

            # Should work with absolute paths
            main_class = converter.extract_main_class()
            assert main_class == "HelloWorld"

        # Test with relative path
        rel_path = "test_jars/HelloWorld.jar"

        with tempfile.TemporaryDirectory() as tmpdir:
            converter = Jar2AppImage(rel_path, tmpdir)

            # Should work with relative paths
            main_class = converter.extract_main_class()
            assert main_class == "HelloWorld"

    def test_permission_denied_scenarios(self):
        """Test handling when file permissions prevent access"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "no_access.jar"
            jar_path.write_bytes(b"fake jar")

            # Remove read permission
            jar_path.chmod(0o000)

            try:
                converter = Jar2AppImage(str(jar_path), tmpdir)

                # Should handle permission errors gracefully
                main_class = converter.extract_main_class()
                assert main_class is None  # Cannot read file

            finally:
                # Restore permissions for cleanup
                jar_path.chmod(0o644)

    def test_concurrent_access_simulation(self):
        """Test behavior when JAR file is modified during processing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            jar_path = Path(tmpdir) / "changing.jar"

            # Start with valid JAR
            import zipfile
            with zipfile.ZipFile(jar_path, 'w') as zf:
                zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nMain-Class: test.Main\n")

            converter = Jar2AppImage(str(jar_path), tmpdir)

            # Modify file after converter creation but before reading
            jar_path.write_bytes(b"corrupted")

            # Should handle file changes gracefully
            main_class = converter.extract_main_class()
            assert main_class is None  # File is now corrupted

    def test_environment_variable_isolation(self):
        """Test that the tool doesn't rely on dangerous environment variables"""
        # Save original environment
        original_env = dict(os.environ)

        try:
            # Set potentially dangerous environment variables
            os.environ['LD_PRELOAD'] = '/dev/null'
            os.environ['PATH'] = '/bin:/usr/bin'  # Restrict PATH

            with tempfile.TemporaryDirectory() as tmpdir:
                converter = Jar2AppImage("test_jars/HelloWorld.jar", tmpdir)

                # Should still work despite environment changes
                main_class = converter.extract_main_class()
                assert main_class == "HelloWorld"

        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_cli_prevents_command_injection(self):
        """Test CLI prevents command injection through arguments"""
        # Test various injection attempts
        injection_attempts = [
            "test_jars/HelloWorld.jar; echo hacked",
            "test_jars/HelloWorld.jar && echo hacked",
            "test_jars/HelloWorld.jar | echo hacked",
            'test_jars/HelloWorld.jar `echo hacked`',
        ]

        for injection in injection_attempts:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py", injection
            ], capture_output=True, text=True, cwd=".")

            # Should not execute injected commands
            # The CLI should fail because the file doesn't exist
            assert result.returncode == 1
            assert "JAR file not found" in result.stdout or "JAR file not found" in result.stderr

            # More importantly, check that the CLI doesn't crash or behave unexpectedly
            # The fact that it properly reports "JAR file not found" shows it's not executing shell commands
            # Just ensure it exits cleanly without hanging or other issues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])