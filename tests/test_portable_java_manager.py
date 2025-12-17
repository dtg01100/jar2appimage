"""Tests for the portable Java manager"""

import sys
import os
import urllib.error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import platform
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from portable_java_manager import PortableJavaManager


class TestPortableJavaManager:
    @patch('portable_java_manager.urllib.request.urlopen')
    def test_get_dynamic_download_url_success(self, mock_urlopen):
        """Test successful dynamic URL generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PortableJavaManager(cache_dir=tmpdir)

            # Mock the API response
            mock_response = MagicMock()
            mock_response.url = "https://example.com/java.tar.gz"
            mock_urlopen.return_value.__enter__.return_value = mock_response

            url = manager._get_dynamic_download_url("17")

            assert url == "https://example.com/java.tar.gz"
            
            # Verify the API URL was called correctly
            os_type = manager.current_platform["system"].lower()
            arch = manager.current_platform["arch"]
            expected_api_url = (
                f"https://api.adoptium.net/v3/binary/latest/17/ga/{os_type}/{arch}/jre/hotspot/normal/eclipse"
                f"?project=temurin"
            )
            mock_urlopen.assert_called_once_with(expected_api_url, timeout=10)

    @patch('portable_java_manager.urllib.request.urlopen')
    def test_get_dynamic_download_url_404(self, mock_urlopen):
        """Test dynamic URL generation with a 404 error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PortableJavaManager(cache_dir=tmpdir)

            # Mock a 404 error
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="", code=404, msg="Not Found", hdrs={}, fp=None
            )

            url = manager._get_dynamic_download_url("99")

            assert url is None

    @patch('portable_java_manager.PortableJavaManager._get_dynamic_download_url')
    @patch('portable_java_manager.PortableJavaManager._download_from_url')
    def test_download_portable_java_dynamic_first(self, mock_download_from_url, mock_get_dynamic_url):
        """Test that download_portable_java tries the dynamic URL first"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PortableJavaManager(cache_dir=tmpdir)

            # Mock the dynamic URL and download functions
            mock_get_dynamic_url.return_value = "https://example.com/dynamic.tar.gz"
            mock_download_from_url.return_value = "/path/to/java.tar.gz"

            result = manager.download_portable_java("17")

            assert result == "/path/to/java.tar.gz"
            mock_get_dynamic_url.assert_called_once_with("17")
            mock_download_from_url.assert_called_once_with("https://example.com/dynamic.tar.gz", "17")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
