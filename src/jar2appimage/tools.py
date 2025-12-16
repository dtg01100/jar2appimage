#!/usr/bin/env python3
"""
Tool downloader and manager for jar2appimage
Downloads required tools like appimagetool on demand
"""

import os
import platform
import stat
from pathlib import Path
from typing import Optional

import requests


class ToolManager:
    """Manages downloading and caching of external tools"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize tool manager

        Args:
            cache_dir: Directory to cache downloaded tools (default:
                ~/.cache/jar2appimage)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use XDG_CACHE_HOME if available, otherwise ~/.cache
            xdg_cache = os.environ.get("XDG_CACHE_HOME")
            if xdg_cache:
                self.cache_dir = Path(xdg_cache) / "jar2appimage"
            else:
                self.cache_dir = Path.home() / ".cache" / "jar2appimage"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_appimagetool(self) -> str:
        """
        Get path to appimagetool, downloading if necessary

        Returns:
            Path to appimagetool executable

        Raises:
            RuntimeError: If download fails or platform is unsupported
        """
        # First check if appimagetool is already in PATH
        existing_tool = self._find_in_path("appimagetool")
        if existing_tool:
            print(f"✅ Using existing appimagetool: {existing_tool}")
            return existing_tool

        # Determine architecture
        machine = platform.machine()
        arch_map = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "aarch64": "aarch64",
            "arm64": "aarch64",
        }

        arch = arch_map.get(machine)
        if not arch:
            raise RuntimeError(f"Unsupported architecture: {machine}")

        # Check cache
        cached_tool = self.cache_dir / f"appimagetool-{arch}"
        if cached_tool.exists() and os.access(cached_tool, os.X_OK):
            print(f"✅ Using cached appimagetool: {cached_tool}")
            return str(cached_tool)

        # Download appimagetool
        print(f"📦 Downloading appimagetool for {arch}...")
        url = f"https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-{arch}.AppImage"

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            # Save to cache
            with open(cached_tool, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Make executable
            st = os.stat(cached_tool)
            perms = st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(cached_tool, perms)

            print(f"✅ Downloaded appimagetool to {cached_tool}")
            return str(cached_tool)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to download appimagetool: {e}") from e

    def _find_in_path(self, tool_name: str) -> Optional[str]:
        """
        Find a tool in PATH

        Args:
            tool_name: Name of the tool to find

        Returns:
            Path to tool if found, None otherwise
        """
        import shutil
        return shutil.which(tool_name)

    def clear_cache(self) -> None:
        """Clear the tool cache directory"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Cleared tool cache: {self.cache_dir}")
