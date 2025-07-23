"""
Test suite for file_utils module.

Tests all file utility functions with proper mocking to isolate from filesystem.
"""

import logging
import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from grimperium.utils.file_utils import (
    cleanup_temp_files,
    copy_file_safely,
    ensure_directory_exists,
    find_files_by_pattern,
    get_file_extension,
    get_unique_output_path,
    is_supported_format,
    sanitize_filename,
    validate_file_exists,
    validate_file_format,
)


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_sanitize_basic_filename(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("normal_filename.txt")
        assert result == "normal_filename.txt"

    def test_sanitize_with_special_characters(self):
        """Test sanitization of special characters."""
        result = sanitize_filename("molecule<name>:test")
        assert result == "molecule_name_test"

    def test_sanitize_with_spaces(self):
        """Test sanitization of spaces."""
        result = sanitize_filename("file name with spaces.txt")
        assert result == "file_name_with_spaces.txt"

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        result = sanitize_filename("")
        assert result == "unnamed_file"

    def test_sanitize_only_special_characters(self):
        """Test sanitization when only special characters remain."""
        result = sanitize_filename("<>:/\\|?*")
        assert result == "unnamed_file"

    def test_sanitize_with_custom_replacement(self):
        """Test sanitization with custom replacement character."""
        result = sanitize_filename("test<>file", replacement="-")
        assert result == "test-file"

    def test_sanitize_multiple_replacements(self):
        """Test removal of multiple consecutive replacement characters."""
        result = sanitize_filename("test___file", replacement="_")
        assert result == "test_file"

    def test_sanitize_leading_trailing_dots(self):
        """Test removal of leading and trailing dots."""
        result = sanitize_filename("..test.file..")
        assert result == "test.file"

    def test_sanitize_leading_trailing_replacements(self):
        """Test removal of leading and trailing replacement characters."""
        result = sanitize_filename("__test__", replacement="_")
        assert result == "test"


class TestEnsureDirectoryExists:
    """Test ensure_directory_exists function."""

    @patch("grimperium.utils.file_utils.Path")
    def test_ensure_directory_success(self, mock_path):
        """Test successful directory creation."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir = MagicMock()

        result = ensure_directory_exists("/test/path")

        assert result is True
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("grimperium.utils.file_utils.Path")
    def test_ensure_directory_failure(self, mock_path):
        """Test directory creation failure."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir.side_effect = OSError("Permission denied")

        result = ensure_directory_exists("/test/path")

        assert result is False

    @patch("grimperium.utils.file_utils.Path")
    def test_ensure_directory_with_logger(self, mock_path):
        """Test directory creation with custom logger."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_logger = MagicMock(spec=logging.Logger)

        result = ensure_directory_exists("/test/path", logger=mock_logger)

        assert result is True
        mock_logger.debug.assert_called_once()


class TestValidateFileExists:
    """Test validate_file_exists function."""

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_exists_success(self, mock_path):
        """Test successful file validation."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 1000

        with patch("builtins.open", mock_open()):
            result, error = validate_file_exists("/test/file.txt")

        assert result is True
        assert error == ""

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_not_exists(self, mock_path):
        """Test file validation when file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        result, error = validate_file_exists("/test/nonexistent.txt")

        assert result is False
        assert "does not exist" in error

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_not_a_file(self, mock_path):
        """Test validation when path is not a file."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = False

        result, error = validate_file_exists("/test/directory")

        assert result is False
        assert "not a file" in error

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_too_small(self, mock_path):
        """Test validation when file is too small."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 50

        result, error = validate_file_exists("/test/file.txt", min_size_bytes=100)

        assert result is False
        assert "too small" in error

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_not_readable(self, mock_path):
        """Test validation when file is not readable."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 1000

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result, error = validate_file_exists("/test/file.txt")

        assert result is False
        assert "not readable" in error

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_no_readability_check(self, mock_path):
        """Test validation without readability check."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 1000

        result, error = validate_file_exists("/test/file.txt", must_be_readable=False)

        assert result is True
        assert error == ""

    @patch("grimperium.utils.file_utils.Path")
    def test_validate_file_exception_handling(self, mock_path):
        """Test exception handling in file validation."""
        mock_path.side_effect = Exception("Unexpected error")

        result, error = validate_file_exists("/test/file.txt")

        assert result is False
        assert "Error validating file" in error


class TestGetFileExtension:
    """Test get_file_extension function."""

    def test_get_extension_normal_file(self):
        """Test getting extension from normal file."""
        result = get_file_extension("molecule.SDF")
        assert result == "sdf"

    def test_get_extension_multiple_dots(self):
        """Test getting extension with multiple dots."""
        result = get_file_extension("file.backup.txt")
        assert result == "txt"

    def test_get_extension_no_extension(self):
        """Test getting extension from file without extension."""
        result = get_file_extension("filename")
        assert result == ""

    def test_get_extension_hidden_file(self):
        """Test getting extension from hidden file."""
        result = get_file_extension(".gitignore")
        assert result == ""

    def test_get_extension_uppercase(self):
        """Test extension normalization to lowercase."""
        result = get_file_extension("FILE.CSV")
        assert result == "csv"


class TestIsSupportedFormat:
    """Test is_supported_format function."""

    def test_is_supported_valid_format(self):
        """Test with valid supported format."""
        assert is_supported_format("sdf") is True
        assert is_supported_format("xyz") is True
        assert is_supported_format("mol") is True

    def test_is_supported_with_dot(self):
        """Test with format containing dot."""
        assert is_supported_format(".sdf") is True

    def test_is_supported_uppercase(self):
        """Test with uppercase format."""
        assert is_supported_format("SDF") is True

    def test_is_supported_invalid_format(self):
        """Test with unsupported format."""
        assert is_supported_format("exe") is False
        assert is_supported_format("unknown") is False


class TestValidateFileFormat:
    """Test validate_file_format function."""

    def test_validate_format_supported(self):
        """Test validation with supported format."""
        result, error = validate_file_format("molecule.sdf")
        assert result is True
        assert error == ""

    def test_validate_format_expected_formats(self):
        """Test validation with specific expected formats."""
        result, error = validate_file_format("data.csv", expected_formats=["csv", "txt"])
        assert result is True
        assert error == ""

    def test_validate_format_no_extension(self):
        """Test validation with file without extension."""
        result, error = validate_file_format("filename")
        assert result is False
        assert "no extension" in error

    def test_validate_format_too_long(self):
        """Test validation with extension too long."""
        result, error = validate_file_format("file.toolongext")
        assert result is False
        assert "too long" in error

    def test_validate_format_unexpected(self):
        """Test validation with unexpected format."""
        result, error = validate_file_format("data.exe", expected_formats=["csv"])
        assert result is False
        assert "Unexpected file format" in error

    def test_validate_format_unsupported(self):
        """Test validation with unsupported format."""
        result, error = validate_file_format("virus.exe")
        assert result is False
        assert "Unsupported file format" in error


class TestFindFilesByPattern:
    """Test find_files_by_pattern function."""

    @patch("grimperium.utils.file_utils.Path")
    def test_find_files_success(self, mock_path):
        """Test successful file finding."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.absolute.return_value = Path("/test/file1.csv")
        
        mock_file2 = MagicMock()
        mock_file2.is_file.return_value = True
        mock_file2.absolute.return_value = Path("/test/file2.csv")

        mock_path_instance.glob.return_value = [mock_file1, mock_file2]

        result = find_files_by_pattern("/test", "*.csv")

        assert len(result) == 2
        assert "/test/file1.csv" in result
        assert "/test/file2.csv" in result

    @patch("grimperium.utils.file_utils.Path")
    def test_find_files_recursive(self, mock_path):
        """Test recursive file finding."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path_instance.rglob.return_value = []

        result = find_files_by_pattern("/test", "*.csv", recursive=True)

        mock_path_instance.rglob.assert_called_once_with("*.csv")
        assert result == []

    @patch("grimperium.utils.file_utils.Path")
    def test_find_files_directory_not_exists(self, mock_path):
        """Test finding files when directory doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        result = find_files_by_pattern("/nonexistent", "*.csv")

        assert result == []

    @patch("grimperium.utils.file_utils.Path")
    def test_find_files_max_results(self, mock_path):
        """Test finding files with max results limit."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        
        mock_files = []
        for i in range(5):
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.absolute.return_value = Path(f"/test/file{i}.csv")
            mock_files.append(mock_file)

        mock_path_instance.glob.return_value = mock_files

        result = find_files_by_pattern("/test", "*.csv", max_results=3)

        assert len(result) == 3

    @patch("grimperium.utils.file_utils.Path")
    def test_find_files_exception_handling(self, mock_path):
        """Test exception handling in file finding."""
        mock_path.side_effect = Exception("Unexpected error")

        result = find_files_by_pattern("/test", "*.csv")

        assert result == []


class TestGetUniqueOutputPath:
    """Test get_unique_output_path function."""

    @patch("grimperium.utils.file_utils.Path")
    def test_unique_path_not_exists(self, mock_path):
        """Test unique path generation when file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False
        mock_path_instance.__str__ = lambda self: "output.txt"

        result = get_unique_output_path("output.txt")

        assert result == "output.txt"

    @patch("grimperium.utils.file_utils.Path")
    def test_unique_path_exists(self, mock_path):
        """Test unique path generation when file exists."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.side_effect = [True, False]  # First exists, second doesn't
        mock_path_instance.stem = "output"
        mock_path_instance.suffix = ".txt"
        mock_path_instance.parent = Path("/test")

        result = get_unique_output_path("output.txt")

        assert "output_1.txt" in result

    @patch("grimperium.utils.file_utils.Path")
    def test_unique_path_with_extension(self, mock_path):
        """Test unique path generation with new extension."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.with_suffix.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        result = get_unique_output_path("output.txt", extension="csv")

        mock_path_instance.with_suffix.assert_called_once_with(".csv")

    @patch("grimperium.utils.file_utils.Path")
    def test_unique_path_infinite_loop_protection(self, mock_path):
        """Test protection against infinite loop in unique path generation."""
        def mock_path_factory(path_str):
            mock_instance = MagicMock()
            mock_instance.exists.return_value = True  # Always exists
            mock_instance.stem = "output"
            mock_instance.suffix = ".txt"
            mock_instance.parent = MagicMock()
            mock_instance.parent.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
            return mock_instance

        mock_path.side_effect = mock_path_factory

        with pytest.raises(RuntimeError, match="Could not generate unique path"):
            get_unique_output_path("output.txt")


class TestCopyFileSafely:
    """Test copy_file_safely function."""

    @patch("shutil.copy2")
    @patch("grimperium.utils.file_utils.Path")
    @patch("grimperium.utils.file_utils.ensure_directory_exists")
    def test_copy_file_success(self, mock_ensure_dir, mock_path, mock_copy2):
        """Test successful file copying."""
        mock_source = MagicMock()
        mock_source.exists.return_value = True
        mock_source.is_file.return_value = True
        
        mock_dest = MagicMock()
        mock_dest.exists.return_value = False
        mock_dest.parent = Path("/dest")

        mock_path.side_effect = [mock_source, mock_dest]
        mock_ensure_dir.return_value = True

        result = copy_file_safely("/source/file.txt", "/dest/file.txt")

        assert result is True
        mock_copy2.assert_called_once_with(mock_source, mock_dest)

    @patch("grimperium.utils.file_utils.Path")
    def test_copy_file_source_not_exists(self, mock_path):
        """Test file copying when source doesn't exist."""
        mock_source = MagicMock()
        mock_source.exists.return_value = False
        mock_path.return_value = mock_source

        result = copy_file_safely("/nonexistent/file.txt", "/dest/file.txt")

        assert result is False

    @patch("grimperium.utils.file_utils.Path")
    def test_copy_file_source_not_file(self, mock_path):
        """Test file copying when source is not a file."""
        mock_source = MagicMock()
        mock_source.exists.return_value = True
        mock_source.is_file.return_value = False
        mock_path.return_value = mock_source

        result = copy_file_safely("/source/directory", "/dest/file.txt")

        assert result is False

    @patch("grimperium.utils.file_utils.Path")
    def test_copy_file_destination_exists_no_overwrite(self, mock_path):
        """Test file copying when destination exists and overwrite is False."""
        mock_source = MagicMock()
        mock_source.exists.return_value = True
        mock_source.is_file.return_value = True
        
        mock_dest = MagicMock()
        mock_dest.exists.return_value = True

        mock_path.side_effect = [mock_source, mock_dest]

        result = copy_file_safely("/source/file.txt", "/dest/file.txt", overwrite=False)

        assert result is False

    @patch("shutil.copy2")
    @patch("grimperium.utils.file_utils.Path")
    @patch("grimperium.utils.file_utils.ensure_directory_exists")
    def test_copy_file_with_logger(self, mock_ensure_dir, mock_path, mock_copy2):
        """Test file copying with custom logger."""
        mock_source = MagicMock()
        mock_source.exists.return_value = True
        mock_source.is_file.return_value = True
        
        mock_dest = MagicMock()
        mock_dest.exists.return_value = False
        mock_dest.parent = Path("/dest")

        mock_path.side_effect = [mock_source, mock_dest]
        mock_ensure_dir.return_value = True
        mock_logger = MagicMock(spec=logging.Logger)

        result = copy_file_safely("/source/file.txt", "/dest/file.txt", logger=mock_logger)

        assert result is True
        mock_logger.debug.assert_called_once()


class TestCleanupTempFiles:
    """Test cleanup_temp_files function."""

    @patch("grimperium.utils.file_utils.Path")
    def test_cleanup_success(self, mock_path):
        """Test successful cleanup of temporary files."""
        mock_file1 = MagicMock()
        mock_file1.exists.return_value = True
        mock_file1.is_file.return_value = True
        
        mock_file2 = MagicMock()
        mock_file2.exists.return_value = True
        mock_file2.is_file.return_value = True

        mock_path.side_effect = [mock_file1, mock_file2]

        result = cleanup_temp_files(["/temp/file1.tmp", "/temp/file2.tmp"])

        assert result == 2
        mock_file1.unlink.assert_called_once()
        mock_file2.unlink.assert_called_once()

    @patch("grimperium.utils.file_utils.Path")
    def test_cleanup_file_not_exists(self, mock_path):
        """Test cleanup when file doesn't exist."""
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_path.return_value = mock_file

        result = cleanup_temp_files(["/temp/nonexistent.tmp"])

        assert result == 0
        mock_file.unlink.assert_not_called()

    @patch("grimperium.utils.file_utils.Path")
    def test_cleanup_with_exception(self, mock_path):
        """Test cleanup with exception handling."""
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.is_file.return_value = True
        mock_file.unlink.side_effect = OSError("Permission denied")
        mock_path.return_value = mock_file

        result = cleanup_temp_files(["/temp/file.tmp"])

        assert result == 0

    @patch("grimperium.utils.file_utils.Path")
    def test_cleanup_with_logger(self, mock_path):
        """Test cleanup with custom logger."""
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.is_file.return_value = True
        mock_path.return_value = mock_file
        mock_logger = MagicMock(spec=logging.Logger)

        result = cleanup_temp_files(["/temp/file.tmp"], logger=mock_logger)

        assert result == 1
        mock_logger.debug.assert_called_once()