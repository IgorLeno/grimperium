"""
Test suite for base_service module.

Tests the BaseService abstract class and FileServiceMixin with proper mocking.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from grimperium.utils.base_service import BaseService, FileServiceMixin


class ConcreteService(BaseService):
    """Concrete implementation of BaseService for testing."""

    def __init__(self, service_name=None):
        super().__init__(service_name)


class ConcreteServiceWithFileMixin(BaseService, FileServiceMixin):
    """Test service that combines BaseService and FileServiceMixin."""

    def __init__(self, service_name=None):
        super().__init__(service_name)


class TestBaseService:
    """Test BaseService class."""

    def test_init_with_service_name(self):
        """Test BaseService initialization with custom service name."""
        service = ConcreteService("CustomService")
        assert service.service_name == "CustomService"
        assert service.logger is not None
        assert isinstance(service.logger, logging.Logger)

    def test_init_without_service_name(self):
        """Test BaseService initialization with default service name."""
        service = ConcreteService()
        assert service.service_name == "ConcreteService"
        assert service.logger is not None

    def test_setup_logger(self):
        """Test logger setup."""
        service = ConcreteService("TestLogger")
        assert service.logger.name == "grimperium.testlogger"

    def test_log_info(self):
        """Test info logging."""
        service = ConcreteService("ConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        service.log_info("Test message")

        service.logger.info.assert_called_once_with("[ConcreteService] Test message")

    def test_log_info_with_args(self):
        """Test info logging with arguments."""
        service = ConcreteService("ConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        service.log_info("Test message %s", "arg1", extra={"key": "value"})

        service.logger.info.assert_called_once_with(
            "[ConcreteService] Test message %s", "arg1", extra={"key": "value"}
        )

    def test_log_debug(self):
        """Test debug logging."""
        service = ConcreteService("ConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        service.log_debug("Debug message")

        service.logger.debug.assert_called_once_with("[ConcreteService] Debug message")

    def test_log_warning(self):
        """Test warning logging."""
        service = ConcreteService("ConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        service.log_warning("Warning message")

        service.logger.warning.assert_called_once_with(
            "[ConcreteService] Warning message"
        )

    def test_log_error(self):
        """Test error logging."""
        service = ConcreteService("ConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        service.log_error("Error message")

        service.logger.error.assert_called_once_with("[ConcreteService] Error message")

    def test_validate_string_input_valid(self):
        """Test valid string input validation."""
        service = ConcreteService()
        result = service.validate_string_input("  valid string  ", "test_param")
        assert result == "valid string"

    def test_validate_string_input_none_not_allowed(self):
        """Test string validation with None when not allowed."""
        service = ConcreteService()
        with pytest.raises(ValueError, match="test_param cannot be None"):
            service.validate_string_input(None, "test_param")

    def test_validate_string_input_none_allowed(self):
        """Test string validation with None when allowed."""
        service = ConcreteService()
        result = service.validate_string_input(None, "test_param", allow_empty=True)
        assert result is None

    def test_validate_string_input_not_string(self):
        """Test string validation with non-string input."""
        service = ConcreteService()
        with pytest.raises(ValueError, match="test_param must be a string, got int"):
            service.validate_string_input(123, "test_param")

    def test_validate_string_input_empty_not_allowed(self):
        """Test string validation with empty string when not allowed."""
        service = ConcreteService()
        with pytest.raises(ValueError, match="test_param cannot be empty"):
            service.validate_string_input("   ", "test_param")

    def test_validate_string_input_empty_allowed(self):
        """Test string validation with empty string when allowed."""
        service = ConcreteService()
        result = service.validate_string_input("   ", "test_param", allow_empty=True)
        assert result == ""

    @patch("pathlib.Path")
    def test_validate_path_input_valid(self, mock_path):
        """Test valid path input validation."""
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = "/resolved/path"
        mock_path.return_value = mock_path_instance

        service = ConcreteService()
        result = service.validate_path_input("  /test/path  ", "test_path")

        assert result == "/resolved/path"
        mock_path.assert_called_once_with("/test/path")

    @patch("pathlib.Path")
    def test_validate_path_input_must_exist(self, mock_path):
        """Test path validation when path must exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        service = ConcreteService()
        with pytest.raises(ValueError, match="test_path does not exist"):
            service.validate_path_input(
                "/nonexistent/path", "test_path", must_exist=True
            )

    @patch("pathlib.Path")
    def test_validate_path_input_exists(self, mock_path):
        """Test path validation when path exists."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = "/resolved/existing/path"
        mock_path.return_value = mock_path_instance

        service = ConcreteService()
        result = service.validate_path_input(
            "/existing/path", "test_path", must_exist=True
        )

        assert result == "/resolved/existing/path"
        mock_path_instance.exists.assert_called_once()

    def test_handle_service_error(self):
        """Test service error handling."""
        service = ConcreteService("ErrorConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        error = ValueError("Test error")
        result = service.handle_service_error(error, "test operation", "default_value")

        assert result == "default_value"
        service.logger.error.assert_called_once_with(
            "[ErrorConcreteService] Error during test operation: Test error"
        )
        service.logger.debug.assert_called_once_with(
            "[ErrorConcreteService] Error details for test operation", exc_info=True
        )

    def test_handle_service_error_default_return(self):
        """Test service error handling with default return value."""
        service = ConcreteService()
        service.logger = MagicMock(spec=logging.Logger)

        error = RuntimeError("Runtime error")
        result = service.handle_service_error(error, "failed operation")

        assert result is None

    def test_create_service_result_success(self):
        """Test creating successful service result."""
        service = ConcreteService("ResultConcreteService")

        result = service.create_service_result(
            success=True, data={"key": "value"}, metadata={"operation_time": 1.5}
        )

        expected = {
            "success": True,
            "service": "ResultConcreteService",
            "data": {"key": "value"},
            "error": None,
            "metadata": {"operation_time": 1.5},
        }
        assert result == expected

    def test_create_service_result_failure(self):
        """Test creating failure service result."""
        service = ConcreteService("ResultConcreteService")

        result = service.create_service_result(
            success=False, error_message="Operation failed"
        )

        expected = {
            "success": False,
            "service": "ResultConcreteService",
            "data": None,
            "error": "Operation failed",
            "metadata": {},
        }
        assert result == expected

    def test_create_service_result_minimal(self):
        """Test creating minimal service result."""
        service = ConcreteService("MinimalService")

        result = service.create_service_result(success=True)

        expected = {
            "success": True,
            "service": "MinimalService",
            "data": None,
            "error": None,
            "metadata": {},
        }
        assert result == expected


class TestFileServiceMixin:
    """Test FileServiceMixin class."""

    @patch("pathlib.Path")
    def test_ensure_directory_exists_success(self, mock_path):
        """Test successful directory creation."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        mixin = ConcreteServiceWithFileMixin()
        result = mixin.ensure_directory_exists("/test/directory")

        assert result is True
        mock_path.assert_called_once_with("/test/directory")
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("pathlib.Path")
    def test_ensure_directory_exists_failure(self, mock_path):
        """Test directory creation failure."""
        mock_path_instance = MagicMock()
        mock_path_instance.mkdir.side_effect = OSError("Permission denied")
        mock_path.return_value = mock_path_instance

        mixin = ConcreteServiceWithFileMixin()
        mixin.logger = MagicMock(spec=logging.Logger)
        result = mixin.ensure_directory_exists("/forbidden/directory")

        assert result is False
        mixin.logger.error.assert_called_once()

    def test_ensure_directory_exists_no_logger(self):
        """Test directory creation with object that has no logger."""

        class MinimalMixin(FileServiceMixin):
            pass

        mixin = MinimalMixin()

        with patch("pathlib.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.mkdir.side_effect = OSError("Error")
            mock_path.return_value = mock_path_instance

            result = mixin.ensure_directory_exists("/test/path")
            assert result is False

    @patch("pathlib.Path")
    def test_check_file_exists_and_readable_success(self, mock_path):
        """Test successful file existence and readability check."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 1000
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.check_file_exists_and_readable("/test/file.txt")

        assert result is True
        mock_path.assert_called_once_with("/test/file.txt")

    @patch("pathlib.Path")
    def test_check_file_exists_and_readable_not_exists(self, mock_path):
        """Test file check when file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.check_file_exists_and_readable("/nonexistent/file.txt")

        assert result is False

    @patch("pathlib.Path")
    def test_check_file_exists_and_readable_not_file(self, mock_path):
        """Test file check when path is not a file."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = False
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.check_file_exists_and_readable("/test/directory")

        assert result is False

    @patch("pathlib.Path")
    def test_check_file_exists_and_readable_empty_file(self, mock_path):
        """Test file check when file is empty."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.stat.return_value.st_size = 0
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.check_file_exists_and_readable("/test/empty.txt")

        assert result is False

    @patch("pathlib.Path")
    def test_check_file_exists_and_readable_exception(self, mock_path):
        """Test file check with exception."""
        mock_path.side_effect = Exception("Error")

        mixin = FileServiceMixin()
        result = mixin.check_file_exists_and_readable("/test/file.txt")

        assert result is False

    @patch("pathlib.Path")
    def test_get_file_size_mb_success(self, mock_path):
        """Test successful file size calculation."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.stat.return_value.st_size = 1048576  # 1 MB
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.get_file_size_mb("/test/file.txt")

        assert result == 1.0
        mock_path.assert_called_once_with("/test/file.txt")

    @patch("pathlib.Path")
    def test_get_file_size_mb_not_exists(self, mock_path):
        """Test file size when file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.get_file_size_mb("/nonexistent/file.txt")

        assert result == 0.0

    @patch("pathlib.Path")
    def test_get_file_size_mb_exception(self, mock_path):
        """Test file size calculation with exception."""
        mock_path.side_effect = Exception("Error")

        mixin = FileServiceMixin()
        result = mixin.get_file_size_mb("/test/file.txt")

        assert result == 0.0

    @patch("pathlib.Path")
    def test_get_file_size_mb_large_file(self, mock_path):
        """Test file size calculation for large file."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.stat.return_value.st_size = 5242880  # 5 MB
        mock_path.return_value = mock_path_instance

        mixin = FileServiceMixin()
        result = mixin.get_file_size_mb("/test/largefile.txt")

        assert result == 5.0


class ConcreteServiceIntegration:
    """Integration tests for combined BaseService and FileServiceMixin."""

    def test_combined_service_functionality(self):
        """Test combined service with both base and file functionality."""
        service = ConcreteServiceWithFileMixin("IntegratedService")

        # Test BaseService functionality
        assert service.service_name == "IntegratedService"
        assert service.logger is not None

        # Test that both sets of methods are available
        assert hasattr(service, "log_info")
        assert hasattr(service, "validate_string_input")
        assert hasattr(service, "ensure_directory_exists")
        assert hasattr(service, "check_file_exists_and_readable")

    @patch("pathlib.Path")
    def test_error_logging_in_mixin(self, mock_path):
        """Test that file mixin uses service logging when available."""
        mock_path_instance = MagicMock()
        mock_path_instance.mkdir.side_effect = OSError("Test error")
        mock_path.return_value = mock_path_instance

        service = ConcreteServiceWithFileMixin("LoggingConcreteService")
        service.logger = MagicMock(spec=logging.Logger)

        result = service.ensure_directory_exists("/test/path")

        assert result is False
        service.logger.error.assert_called_once()
