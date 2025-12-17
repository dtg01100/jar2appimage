import io
import os
from pathlib import Path

import pytest

import portable_java_manager
from portable_java_manager import PortableJavaManager


class _FakeResponse:
    def __init__(self, data: bytes, content_length: int | None = None):
        self._data = io.BytesIO(data)
        self._content_length = content_length

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self, n=-1):
        return self._data.read(n)

    def getheader(self, name):
        if name.lower() == 'content-length' and self._content_length is not None:
            return str(self._content_length)
        return None


def test_download_from_url_success(tmp_path, monkeypatch):
    """Successful download should be saved and returned"""
    # Create >12MB payload (above default 10MB threshold)
    data = b'a' * (12 * 1024 * 1024)

    def fake_urlopen(req, timeout=None):
        return _FakeResponse(data, content_length=len(data))

    monkeypatch.setattr(portable_java_manager.urllib.request, 'urlopen', fake_urlopen)

    manager = PortableJavaManager(interactive_mode=False, cache_dir=str(tmp_path))

    result = manager._download_from_url('https://example.com/fake.tar.gz', '17')

    assert result is not None
    path = Path(result)
    assert path.exists()
    assert path.stat().st_size >= 12 * 1024 * 1024


def test_download_from_url_small_file_removed(tmp_path, monkeypatch):
    """Small downloads should be removed and return None"""
    data = b'small content'

    def fake_urlopen(req, timeout=None):
        return _FakeResponse(data, content_length=len(data))

    monkeypatch.setattr(portable_java_manager.urllib.request, 'urlopen', fake_urlopen)

    manager = PortableJavaManager(interactive_mode=False, cache_dir=str(tmp_path))

    result = manager._download_from_url('https://example.com/fake_small.tar.gz', '17')

    assert result is None

    # Ensure no file remains in cache
    files = list(Path(manager.download_cache).glob('*'))
    assert len(files) == 0
