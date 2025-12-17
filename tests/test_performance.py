"""Performance tests for jar2appimage"""

import time
import tempfile
from pathlib import Path

import pytest
import platform

from jar2appimage.core import Jar2AppImage


class TestPerformance:
    """Performance tests for JAR to AppImage conversion"""

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_helloworld_conversion_performance(self):
        """Test performance of converting HelloWorld.jar"""
        jar_path = "test_jars/HelloWorld.jar"

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            with Jar2AppImage(jar_path, tmpdir) as converter:
                appimage_path = converter.create()

                end_time = time.time()
                conversion_time = end_time - start_time

                # Basic performance assertions
                assert conversion_time < 30  # Should complete in under 30 seconds
                assert Path(appimage_path).exists()

                # Log performance metrics for monitoring
                appimage_size = Path(appimage_path).stat().st_size / 1024 / 1024  # MB
                print(f"HelloWorld conversion time: {conversion_time:.2f}s")
                print(f"AppImage size: {appimage_size:.2f}MB")

                # Ensure reasonable file size (should be > 10MB for bundled JRE)
                assert appimage_size > 10

    @pytest.mark.skipif(platform.system() != "Linux", reason="AppImage execution only supported on Linux")
    def test_sqlworkbench_conversion_performance(self):
        """Test performance of converting SQL Workbench JAR (larger real-world JAR)"""
        jar_path = "real_world_jars/sqlworkbench.jar"

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            with Jar2AppImage(jar_path, tmpdir) as converter:
                appimage_path = converter.create()

                end_time = time.time()
                conversion_time = end_time - start_time

                # Performance assertions for larger JAR
                assert conversion_time < 60  # Should complete in under 60 seconds
                assert Path(appimage_path).exists()

                # Log performance metrics
                appimage_size = Path(appimage_path).stat().st_size / 1024 / 1024  # MB
                print(f"SQL Workbench conversion time: {conversion_time:.2f}s")
                print(f"AppImage size: {appimage_size:.2f}MB")

                # SQL Workbench AppImage should be reasonably sized (> 1MB)
                assert appimage_size > 1

    def test_dependency_analysis_performance(self):
        """Test performance of dependency analysis on different JAR sizes"""
        test_jars = [
            ("test_jars/HelloWorld.jar", "small"),
            ("real_world_jars/sqlworkbench.jar", "medium"),
            ("real_world_jars/tika-app-3.2.3.jar", "large")
        ]

        for jar_path, size_category in test_jars:
            if not Path(jar_path).exists():
                continue

            start_time = time.time()

            with tempfile.TemporaryDirectory() as tmpdir:
                converter = Jar2AppImage(jar_path, tmpdir)
                dependencies = converter.analyze_dependencies()

                end_time = time.time()
                analysis_time = end_time - start_time

                # Dependency analysis should be reasonable (under 15 seconds for large JARs)
                assert analysis_time < 15
                assert isinstance(dependencies, dict)

                print(f"Dependency analysis time for {size_category} JAR: {analysis_time:.2f}s")

    def test_main_class_extraction_performance(self):
        """Test performance of main class extraction"""
        test_jars = [
            "test_jars/HelloWorld.jar",
            "real_world_jars/sqlworkbench.jar",
            "real_world_jars/tika-app-3.2.3.jar"
        ]

        for jar_path in test_jars:
            if not Path(jar_path).exists():
                continue

            start_time = time.time()

            with tempfile.TemporaryDirectory() as tmpdir:
                converter = Jar2AppImage(jar_path, tmpdir)
                main_class = converter.extract_main_class()

                end_time = time.time()
                extraction_time = end_time - start_time

                # Main class extraction should be very fast
                assert extraction_time < 2  # Under 2 seconds
                assert main_class is not None
                assert isinstance(main_class, str)

                print(f"Main class extraction time for {Path(jar_path).name}: {extraction_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])