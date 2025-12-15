"""Tests for jar2appimage tool manager"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from jar2appimage.tools import ToolManager


class TestToolManager:
    def test_initialization_default_cache(self):
        """Test ToolManager initialization with default cache directory"""
        manager = ToolManager()
        
        # Should use ~/.cache/jar2appimage by default
        assert manager.cache_dir.exists()
        assert "jar2appimage" in str(manager.cache_dir)

    def test_initialization_custom_cache(self):
        """Test ToolManager initialization with custom cache directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolManager(cache_dir=tmpdir)
            
            assert manager.cache_dir == Path(tmpdir)
            assert manager.cache_dir.exists()

    def test_find_in_path(self):
        """Test finding tools in PATH"""
        manager = ToolManager()
        
        # Test with a tool that should exist
        python_path = manager._find_in_path("python3")
        assert python_path is not None or manager._find_in_path("python") is not None
        
        # Test with a tool that shouldn't exist
        nonexistent = manager._find_in_path("nonexistent-tool-12345")
        assert nonexistent is None

    @patch('jar2appimage.tools.requests.get')
    @patch('shutil.which')
    def test_get_appimagetool_download(self, mock_which, mock_get):
        """Test downloading appimagetool when not in cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolManager(cache_dir=tmpdir)
            
            # Mock successful download
            mock_response = MagicMock()
            mock_response.iter_content = lambda chunk_size: [b"fake data"]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            # Mock shutil.which to return None (not in PATH)
            mock_which.return_value = None
            
            tool_path = manager.get_appimagetool()
            
            # Should have downloaded
            assert tool_path
            assert Path(tool_path).exists()
            assert "appimagetool" in tool_path

    @patch('shutil.which')
    def test_get_appimagetool_uses_existing(self, mock_which):
        """Test that existing appimagetool in PATH is used"""
        manager = ToolManager()
        
        # Mock shutil.which to return a path
        fake_path = "/usr/bin/appimagetool"
        mock_which.return_value = fake_path
        
        tool_path = manager.get_appimagetool()
        
        # Should use existing tool
        assert tool_path == fake_path

    @patch('shutil.which')
    def test_get_appimagetool_uses_cache(self, mock_which):
        """Test that cached appimagetool is reused"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolManager(cache_dir=tmpdir)
            
            # Create a fake cached tool
            import platform
            machine = platform.machine()
            arch_map = {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64"}
            arch = arch_map.get(machine, machine)
            
            cached_tool = Path(tmpdir) / f"appimagetool-{arch}"
            cached_tool.write_text("fake tool")
            cached_tool.chmod(0o755)
            
            # Mock shutil.which to return None (not in PATH)
            mock_which.return_value = None
            
            tool_path = manager.get_appimagetool()
            
            # Should use cached tool
            assert tool_path == str(cached_tool)

    def test_clear_cache(self):
        """Test clearing the cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolManager(cache_dir=tmpdir)
            
            # Create some fake cached files
            (Path(tmpdir) / "test_file").write_text("test")
            
            # Clear cache
            manager.clear_cache()
            
            # Cache dir should exist but be empty
            assert manager.cache_dir.exists()
            assert len(list(manager.cache_dir.iterdir())) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
