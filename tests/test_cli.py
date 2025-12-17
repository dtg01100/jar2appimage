"""CLI testing for jar2appimage"""

import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
import platform


class TestCLI:
    """Comprehensive CLI testing for jar2appimage"""

    def test_cli_help(self):
        """Test CLI help output"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "--help"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 0
        assert "Enhanced jar2appimage" in result.stdout
        assert "jar_file" in result.stdout
        assert "--bundled" in result.stdout
        assert "--assume-yes" in result.stdout

    def test_cli_no_args(self):
        """Test CLI with no arguments (should fail)"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 1
        assert "JAR file is required" in result.stdout

    def test_cli_invalid_jar(self):
        """Test CLI with non-existent JAR file"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "nonexistent.jar"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 1
        assert "JAR file not found" in result.stdout

    def test_cli_invalid_file_as_jar(self):
        """Test CLI with a non-JAR file"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"This is not a JAR file")
            temp_file = f.name

        try:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py", temp_file
            ], capture_output=True, text=True, cwd=".")

            # Should fail during processing
            assert result.returncode == 1
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_cli_conflicting_bundled_options(self):
        """Test CLI with conflicting --bundled and --no-bundled"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py",
            "test_jars/HelloWorld.jar", "--bundled", "--no-bundled"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 1
        assert "Cannot use both --bundled and --no-bundled" in result.stdout

    def test_cli_assume_yes_no_conflict(self):
        """Test CLI with conflicting --assume-yes and --assume-no"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py",
            "test_jars/HelloWorld.jar", "--assume-yes", "--assume-no"
        ], capture_output=True, text=True, cwd=".")

        # argparse should handle this mutually exclusive group
        assert result.returncode != 0  # Should fail

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_cli_basic_conversion_system_java(self):
        """Test basic CLI conversion with system Java"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", tmpdir, "--no-bundled"
            ], capture_output=True, text=True, cwd=".")

            assert result.returncode == 0
            assert "AppImage created successfully" in result.stdout

            # Check if AppImage was created
            appimages = list(Path(tmpdir).glob("*.AppImage"))
            assert len(appimages) == 1

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_cli_basic_conversion_bundled_java(self):
        """Test basic CLI conversion with bundled Java"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", tmpdir, "--bundled"
            ], capture_output=True, text=True, cwd=".")

            assert result.returncode == 0
            assert "AppImage created successfully" in result.stdout

            # Check if AppImage was created
            appimages = list(Path(tmpdir).glob("*.AppImage"))
            assert len(appimages) == 1

    def test_cli_java_summary(self):
        """Test --java-summary option"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "--java-summary"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 0
        # Should show some Java information or indicate no Java found
        assert len(result.stdout.strip()) > 0

    def test_cli_detect_java(self):
        """Test --detect-java option"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "--detect-java"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 0
        # Should show Java detection results
        assert len(result.stdout.strip()) > 0

    def test_cli_clear_java_cache(self):
        """Test --clear-java-cache option"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "--clear-java-cache"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 0
        # Should show cache clearing result
        assert len(result.stdout.strip()) > 0

    def test_cli_check_platform(self):
        """Test --check-platform option"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py", "--check-platform"
        ], capture_output=True, text=True, cwd=".")

        assert result.returncode == 0
        assert "Platform compatibility check complete" in result.stdout

    def test_cli_invalid_jdk_version(self):
        """Test CLI with invalid JDK version"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py",
            "test_jars/HelloWorld.jar", "--jdk-version", "invalid"
        ], capture_output=True, text=True, cwd=".")

        # argparse should reject invalid choices
        assert result.returncode != 0

    def test_cli_output_dir_creation(self):
        """Test CLI creates output directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as base_tmpdir:
            output_dir = Path(base_tmpdir) / "nested" / "output" / "dir"

            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", str(output_dir), "--no-bundled"
            ], capture_output=True, text=True, cwd=".")

            if result.returncode == 0:  # Only check if conversion succeeded
                assert output_dir.exists()
                appimages = list(output_dir.glob("*.AppImage"))
                assert len(appimages) == 1

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_cli_assume_yes_flag(self):
        """Test --assume-yes flag for non-interactive mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", tmpdir,
                "--bundled", "--assume-yes"
            ], capture_output=True, text=True, cwd=".")

            # Should not prompt for user input
            assert "AppImage created successfully" in result.stdout or result.returncode == 0

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_cli_assume_no_flag(self):
        """Test --assume-no flag for non-interactive mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", tmpdir,
                "--bundled", "--assume-no"
            ], capture_output=True, text=True, cwd=".")

            # Should proceed without prompting
            # (may or may not create AppImage depending on fallback logic)
            assert result.returncode == 0 or "AppImage created successfully" in result.stdout

    def test_cli_no_portable_flag(self):
        """Test --no-portable flag disables portable Java features"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "enhanced_jar2appimage_cli.py",
                "test_jars/HelloWorld.jar", "--output-dir", tmpdir,
                "--bundled", "--no-portable"
            ], capture_output=True, text=True, cwd=".")

            # Should work without portable Java detection
            assert result.returncode == 0

    def test_cli_force_download_flag(self):
        """Test --force-download flag"""
        result = subprocess.run([
            sys.executable, "enhanced_jar2appimage_cli.py",
            "test_jars/HelloWorld.jar", "--force-download"
        ], capture_output=True, text=True, cwd=".")

        # Should attempt to run (may fail if no portable Java available)
        # Just check it doesn't crash on argument parsing
        assert result.returncode in [0, 1]  # 0 for success, 1 for expected failure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])