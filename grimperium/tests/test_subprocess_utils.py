"""
Test suite for subprocess_utils module.

Tests all subprocess utility functions with proper mocking.
"""

import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from grimperium.utils.subprocess_utils import (
    SubprocessResult,
    check_executable_available,
    create_output_file_path,
    execute_command,
    validate_executable_version,
)


class TestSubprocessResult:
    """Test SubprocessResult class."""

    def test_init(self):
        """Test SubprocessResult initialization."""
        command = ["ls", "-la"]
        result = SubprocessResult(
            command=command,
            returncode=0,
            stdout="output",
            stderr="",
            timeout_occurred=False,
            execution_time=1.5,
        )

        assert result.command == command
        assert result.returncode == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.timeout_occurred is False
        assert result.execution_time == 1.5

    def test_success_property_true(self):
        """Test success property when command succeeded."""
        result = SubprocessResult(
            command=["ls"],
            returncode=0,
            stdout="output",
            stderr="",
            timeout_occurred=False,
        )
        assert result.success is True

    def test_success_property_false_nonzero_return(self):
        """Test success property when command failed with non-zero return code."""
        result = SubprocessResult(
            command=["ls"],
            returncode=1,
            stdout="",
            stderr="error",
            timeout_occurred=False,
        )
        assert result.success is False

    def test_success_property_false_timeout(self):
        """Test success property when timeout occurred."""
        result = SubprocessResult(
            command=["ls"], returncode=0, stdout="", stderr="", timeout_occurred=True
        )
        assert result.success is False

    def test_command_str_property(self):
        """Test command_str property."""
        result = SubprocessResult(
            command=["python", "-c", "print('hello')"],
            returncode=0,
            stdout="hello",
            stderr="",
        )
        assert result.command_str == "python -c print('hello')"

    def test_str_representation_success(self):
        """Test string representation for successful command."""
        result = SubprocessResult(
            command=["ls"],
            returncode=0,
            stdout="output",
            stderr="",
            timeout_occurred=False,
        )
        expected = "SubprocessResult(ls) -> SUCCESS (code: 0)"
        assert str(result) == expected

    def test_str_representation_failure(self):
        """Test string representation for failed command."""
        result = SubprocessResult(
            command=["false"],
            returncode=1,
            stdout="",
            stderr="",
            timeout_occurred=False,
        )
        expected = "SubprocessResult(false) -> FAILED (code: 1)"
        assert str(result) == expected


class TestExecuteCommand:
    """Test execute_command function."""

    @patch("subprocess.run")
    @patch("time.time")
    def test_execute_command_success(self, mock_time, mock_run):
        """Test successful command execution."""
        mock_time.side_effect = [100.0, 101.5]  # start and end times
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        result = execute_command(["ls", "-la"])

        assert result.success is True
        assert result.returncode == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.execution_time == 1.5
        assert result.timeout_occurred is False

        mock_run.assert_called_once_with(
            ["ls", "-la"],
            cwd=None,
            timeout=None,
            capture_output=True,
            text=True,
            env=None,
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_execute_command_with_options(self, mock_time, mock_run):
        """Test command execution with custom options."""
        mock_time.side_effect = [100.0, 101.0]
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        result = execute_command(
            ["python", "script.py"],
            cwd="/tmp",
            timeout=30,
            capture_output=False,
            text=False,
            env={"VAR": "value"},
        )

        assert result.success is True
        mock_run.assert_called_once_with(
            ["python", "script.py"],
            cwd="/tmp",
            timeout=30,
            capture_output=False,
            text=False,
            env={"VAR": "value"},
        )

    @patch("subprocess.run")
    def test_execute_command_failure(self, mock_run):
        """Test command execution failure."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error message"
        )

        result = execute_command(["false"])

        assert result.success is False
        assert result.returncode == 1
        assert result.stderr == "error message"

    @patch("subprocess.run")
    @patch("time.time")
    def test_execute_command_timeout(self, mock_time, mock_run):
        """Test command execution timeout."""
        mock_time.return_value = 100.0  # Use return_value instead of side_effect
        mock_run.side_effect = subprocess.TimeoutExpired("sleep", 30)

        result = execute_command(["sleep", "60"], timeout=30)

        assert result.success is False
        assert result.returncode == -1
        assert result.timeout_occurred is True
        assert "timed out after 30 seconds" in result.stderr
        assert result.execution_time == 0.0

    @patch("subprocess.run")
    @patch("time.time")
    def test_execute_command_file_not_found(self, mock_time, mock_run):
        """Test command execution when executable not found."""
        mock_time.return_value = 100.0
        mock_run.side_effect = FileNotFoundError()

        result = execute_command(["nonexistent_command"])

        assert result.success is False
        assert result.returncode == -1
        assert "Executable not found: nonexistent_command" in result.stderr
        assert result.timeout_occurred is False

    @patch("subprocess.run")
    @patch("time.time")
    def test_execute_command_unexpected_error(self, mock_time, mock_run):
        """Test command execution with unexpected error."""
        mock_time.return_value = 100.0
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = execute_command(["ls"])

        assert result.success is False
        assert result.returncode == -1
        assert "Unexpected error executing command" in result.stderr
        assert result.timeout_occurred is False

    def test_execute_command_invalid_command(self):
        """Test execute_command with invalid command."""
        with pytest.raises(ValueError, match="Command must be a non-empty list"):
            execute_command([])

        with pytest.raises(ValueError, match="Command must be a non-empty list"):
            execute_command("ls")

    @patch("subprocess.run")
    def test_execute_command_no_capture_output(self, mock_run):
        """Test command execution without capturing output."""
        mock_run.return_value = MagicMock(returncode=0)

        result = execute_command(["ls"], capture_output=False)

        assert result.success is True
        assert result.stdout == ""
        assert result.stderr == ""

    @patch("subprocess.run")
    def test_execute_command_with_logger(self, mock_run):
        """Test command execution with custom logger."""
        logger = MagicMock(spec=logging.Logger)
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        result = execute_command(["ls"], logger=logger)

        assert result.success is True
        logger.debug.assert_called()


class TestCheckExecutableAvailable:
    """Test check_executable_available function."""

    @patch("shutil.which")
    def test_check_executable_found(self, mock_which):
        """Test checking executable that exists."""
        mock_which.return_value = "/usr/bin/python"

        result = check_executable_available("python")

        assert result is True
        mock_which.assert_called_once_with("python")

    @patch("shutil.which")
    def test_check_executable_not_found(self, mock_which):
        """Test checking executable that doesn't exist."""
        mock_which.return_value = None

        result = check_executable_available("nonexistent")

        assert result is False
        mock_which.assert_called_once_with("nonexistent")

    @patch("shutil.which")
    def test_check_executable_exception(self, mock_which):
        """Test checking executable with exception."""
        mock_which.side_effect = Exception("Error checking")

        result = check_executable_available("python")

        assert result is False

    @patch("shutil.which")
    def test_check_executable_with_logger(self, mock_which):
        """Test checking executable with custom logger."""
        mock_which.return_value = "/usr/bin/python"
        logger = MagicMock(spec=logging.Logger)

        result = check_executable_available("python", logger=logger)

        assert result is True
        logger.debug.assert_called_once()


class TestValidateExecutableVersion:
    """Test validate_executable_version function."""

    @patch("grimperium.utils.subprocess_utils.check_executable_available")
    @patch("grimperium.utils.subprocess_utils.execute_command")
    def test_validate_version_success(self, mock_execute, mock_check):
        """Test successful version validation."""
        mock_check.return_value = True
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Python 3.8.0\n"
        mock_execute.return_value = mock_result

        result = validate_executable_version("python")

        assert result == "Python 3.8.0"
        # Logger will be created internally, so we check the call without
        # comparing logger
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        assert call_args[0][0] == "python"  # First arg is executable name
        # Logger will be created internally, so we check the call without
        # comparing logger
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0] == (["python", "--version"],)
        assert call_args[1]["timeout"] == 10

    @patch("grimperium.utils.subprocess_utils.check_executable_available")
    def test_validate_version_executable_not_found(self, mock_check):
        """Test version validation when executable not found."""
        mock_check.return_value = False

        result = validate_executable_version("nonexistent")

        assert result is None
        # Logger will be created internally, so we check the call without
        # comparing logger
        mock_check.assert_called_once()
        call_args = mock_check.call_args
        assert call_args[0][0] == "nonexistent"  # First arg is executable name

    @patch("grimperium.utils.subprocess_utils.check_executable_available")
    @patch("grimperium.utils.subprocess_utils.execute_command")
    def test_validate_version_command_failed(self, mock_execute, mock_check):
        """Test version validation when version command fails."""
        mock_check.return_value = True
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.stderr = "Command failed"
        mock_execute.return_value = mock_result

        result = validate_executable_version("badprogram")

        assert result is None

    @patch("grimperium.utils.subprocess_utils.check_executable_available")
    @patch("grimperium.utils.subprocess_utils.execute_command")
    def test_validate_version_custom_args(self, mock_execute, mock_check):
        """Test version validation with custom version arguments."""
        mock_check.return_value = True
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "version 1.0"
        mock_execute.return_value = mock_result

        result = validate_executable_version(
            "myprogram", version_args=["-v"], timeout=5
        )

        assert result == "version 1.0"
        # Logger will be created internally, so we check the call without
        # comparing logger
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0] == (["myprogram", "-v"],)
        assert call_args[1]["timeout"] == 5

    @patch("grimperium.utils.subprocess_utils.check_executable_available")
    @patch("grimperium.utils.subprocess_utils.execute_command")
    def test_validate_version_with_logger(self, mock_execute, mock_check):
        """Test version validation with custom logger."""
        mock_check.return_value = True
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "version 1.0"
        mock_execute.return_value = mock_result
        logger = MagicMock(spec=logging.Logger)

        result = validate_executable_version("program", logger=logger)

        assert result == "version 1.0"
        logger.debug.assert_called_once()


class TestCreateOutputFilePath:
    """Test create_output_file_path function."""

    def test_create_output_path_same_directory(self):
        """Test creating output path in same directory as input."""
        result = create_output_file_path("/path/to/input.xyz", "pdb")
        expected = str(Path("/path/to/input.pdb").absolute())
        assert result == expected

    def test_create_output_path_custom_directory(self):
        """Test creating output path in custom directory."""
        result = create_output_file_path(
            "/path/to/input.xyz", "pdb", output_dir="/output"
        )
        expected = str(Path("/output/input.pdb").absolute())
        assert result == expected

    def test_create_output_path_extension_with_dot(self):
        """Test creating output path with extension that includes dot."""
        result = create_output_file_path("/path/to/input.xyz", ".pdb")
        expected = str(Path("/path/to/input.pdb").absolute())
        assert result == expected

    def test_create_output_path_complex_filename(self):
        """Test creating output path with complex filename."""
        result = create_output_file_path(
            "/path/to/molecule.conformer.xyz", "sdf", output_dir="/output"
        )
        expected = str(Path("/output/molecule.conformer.sdf").absolute())
        assert result == expected

    def test_create_output_path_no_extension_input(self):
        """Test creating output path when input has no extension."""
        result = create_output_file_path("/path/to/filename", "txt")
        expected = str(Path("/path/to/filename.txt").absolute())
        assert result == expected

    def test_create_output_path_relative_input(self):
        """Test creating output path with relative input path."""
        result = create_output_file_path("input.xyz", "pdb")
        # Should return absolute path
        assert Path(result).is_absolute()
        assert result.endswith("input.pdb")

    def test_create_output_path_relative_output_dir(self):
        """Test creating output path with relative output directory."""
        result = create_output_file_path("/path/input.xyz", "pdb", output_dir="output")
        # Should return absolute path
        assert Path(result).is_absolute()
        assert result.endswith("input.pdb")

    def test_create_output_path_current_directory(self):
        """Test creating output path in current directory."""
        result = create_output_file_path("input.xyz", "pdb")
        # Should return absolute path ending with input.pdb
        assert Path(result).is_absolute()
        assert result.endswith("input.pdb")
