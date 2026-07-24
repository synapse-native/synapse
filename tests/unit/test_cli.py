import sys
import subprocess
import subprocess as sp
from unittest.mock import patch, MagicMock
import pytest


class TestCLIHelpFlag:
    def test_help_flag_exits_before_linker_invocation(self, monkeypatch):
        """Test that --help exits with code 0 and does NOT invoke the linker (GCC)."""
        mock_system = MagicMock(return_value=0)
        monkeypatch.setattr("os.system", mock_system)

        with pytest.raises(SystemExit) as exc_info:
            from cli import main
            with patch.object(sys, "argv", ["synapse.exe", "--help"]):
                main()

        assert exc_info.value.code == 0
        mock_system.assert_not_called()

    def test_help_flag_exits_with_code_zero(self):
        """Test that --help exits with code 0 without invoking linker."""
        result = subprocess.run(
            [sys.executable, "-m", "cli", "--help"],
            cwd="D:/proyecto_synapse",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()
        assert "gcc" not in result.stdout.lower()
        assert "gcc" not in result.stderr.lower()
        assert "gcc" not in str(result.returncode).lower()

    def test_version_flag_exits_with_code_zero(self):
        """Test that --version exits with code 0 without invoking linker."""
        result = subprocess.run(
            [sys.executable, "-m", "cli", "--version"],
            cwd="D:/proyecto_synapse",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "gcc" not in result.stdout.lower()
        assert "gcc" not in result.stderr.lower()
        assert "gcc" not in str(result.returncode).lower()

    def test_help_flag_does_not_invoke_os_system(self, monkeypatch):
        """Direct unit test mocking os.system to verify linker is never called."""
        mock_system = MagicMock()
        monkeypatch.setattr("os.system", mock_system)

        from cli import main
        with patch.object(sys, "argv", ["synapse.exe", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_system.assert_not_called()


class TestCLIVersionFlag:
    def test_version_flag_exits_with_code_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "cli", "--version"],
            cwd="D:/proyecto_synapse",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "gcc" not in result.stdout.lower()
        assert "gcc" not in result.stderr.lower()
        assert "linker" not in result.stdout.lower()
        assert "gcc" not in str(result.returncode).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])