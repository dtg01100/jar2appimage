import subprocess
import sys
from pathlib import Path


class TestEnhancedCLI:
    def test_cli_flags_exist(self):
        """Test that --assume-yes and --assume-no flags are available"""
        script_path = Path(__file__).parent.parent / "enhanced_jar2appimage_cli.py"
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True, timeout=10)

        # Check that the script runs and has the flags
        assert result.returncode == 0
        assert "--assume-yes" in result.stdout
        assert "--assume-no" in result.stdout
        assert "Assume 'yes' to all prompts" in result.stdout
        assert "Assume 'no' to all prompts" in result.stdout


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])