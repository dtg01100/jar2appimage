# On-Demand Tool Download Implementation

## Summary

Implemented automatic on-demand downloading of `appimagetool` instead of bundling it in the repository. This reduces repository size and ensures users always have the latest version of the tool.

## Changes Made

### New Files

1. **`src/jar2appimage/tools.py`**
   - New `ToolManager` class for downloading and caching external tools
   - Automatically downloads `appimagetool` on first use
   - Caches downloaded tools in `~/.cache/jar2appimage/`
   - Supports both x86_64 and aarch64 architectures
   - Checks for existing tools in PATH before downloading
   - Provides `clear_cache()` method for cleanup

2. **`tests/test_tools.py`**
   - Comprehensive test suite for `ToolManager`
   - Tests for cache initialization, download, reuse, and cleanup
   - Mocked tests to avoid actual downloads during testing

### Modified Files

1. **`src/jar2appimage/core.py`**
   - Updated `_create_standard_appimage()` to use `ToolManager`
   - Removed hardcoded PATH-based lookup
   - Now downloads appimagetool automatically if not found

2. **`.gitignore`**
   - Added `appimagetool`, `appimagetool-*`, and `AppRun` to ignore list
   - Prevents accidentally committing downloaded binaries

3. **`README.md`**
   - Updated to reflect automatic download feature
   - Documented cache location (`~/.cache/jar2appimage/`)
   - Added information about first-run behavior

4. **`QUICKSTART.md`**
   - Updated features list to highlight on-demand downloads
   - Added "Smart Caching" feature
   - Updated "How It Works" section

5. **`pyproject.toml`**
   - Bumped version to 0.1.2

## User Experience

### Before
- Users had to manually install `appimagetool` or it was bundled in the repo
- Repository included large binary files
- No automatic updates to tools

### After
- First run: Automatically downloads `appimagetool` (~8.5MB)
- Subsequent runs: Uses cached version (instant)
- Clean repository without bundled binaries
- Always uses latest version from GitHub releases

## Technical Details

### Download Source
- **URL**: `https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-{arch}.AppImage`
- **Supported Architectures**: x86_64, aarch64
- **Cache Location**: `~/.cache/jar2appimage/` (respects `XDG_CACHE_HOME`)

### Tool Detection Priority
1. Check if tool exists in system PATH
2. Check if tool exists in cache
3. Download tool to cache

### Error Handling
- Graceful fallback if download fails
- Clear error messages
- Timeout protection (60 seconds)

## Testing

All 14 tests pass:
- 7 existing tests (unchanged)
- 7 new tests for ToolManager

### Test Coverage
- Cache initialization (default and custom)
- Finding tools in PATH
- Downloading when not cached
- Reusing existing tools
- Reusing cached tools
- Cache clearing

## Benefits

1. **Smaller Repository**: No large binary files committed
2. **Always Updated**: Downloads latest continuous build
3. **Better UX**: Zero manual setup required
4. **Cross-Platform**: Automatically detects architecture
5. **Offline Support**: Works offline after first download
6. **Developer Friendly**: Clear cache for testing

## Example Usage

```bash
# First run - downloads appimagetool
$ jar2appimage myapp.jar
📦 Downloading appimagetool for x86_64...
✅ Downloaded appimagetool to ~/.cache/jar2appimage/appimagetool-x86_64
✅ Created AppImage: myapp.AppImage

# Second run - uses cached version
$ jar2appimage otherapp.jar
✅ Using cached appimagetool: ~/.cache/jar2appimage/appimagetool-x86_64
✅ Created AppImage: otherapp.AppImage

# Clear cache if needed
$ python -c "from jar2appimage.tools import ToolManager; ToolManager().clear_cache()"
✅ Cleared tool cache: ~/.cache/jar2appimage
```

## Future Enhancements

Potential additions:
- Support for other tools (runtime-fuse3, etc.)
- Version pinning for reproducible builds
- Progress bars for downloads
- Checksum verification
- Mirror support for faster downloads
