"""
Test suite for error_handler module.

Tests all error handling utilities with proper mocking.
"""

import logging
import time
import unittest.mock as mock
from unittest.mock import MagicMock, patch

import pytest

from grimperium.exceptions import GrimperiumError, ValidationError
from grimperium.utils.error_handler import (
    ErrorHandler,
    log_exceptions,
    retry_on_error,
    safe_execute,
    validate_and_convert,
)


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_init_with_logger(self):
        """Test ErrorHandler initialization with custom logger."""
        logger = MagicMock(spec=logging.Logger)
        handler = ErrorHandler(logger=logger)
        assert handler.logger is logger

    def test_init_without_logger(self):
        """Test ErrorHandler initialization with default logger."""
        handler = ErrorHandler()
        assert handler.logger is not None
        assert isinstance(handler.logger, logging.Logger)

    @patch("grimperium.utils.error_handler.format_error_context")
    def test_handle_grimperium_error(self, mock_format_error):
        """Test handling of GrimperiumError."""
        logger = MagicMock(spec=logging.Logger)
        handler = ErrorHandler(logger=logger)

        error = GrimperiumError("Test error", "TEST_ERROR", {"detail": "value"})
        mock_format_error.return_value = {
            "message": "Test error",
            "error_code": "TEST_ERROR",
            "details": {"detail": "value"}
        }

        result = handler.handle_error(error, context="test_function", return_value="default")

        assert result == "default"
        logger.log.assert_called_once_with(logging.ERROR, "Grimperium error in test_function: Test error")
        logger.debug.assert_called_once()

    def test_handle_standard_error(self):
        """Test handling of standard Python exceptions."""
        logger = MagicMock(spec=logging.Logger)
        handler = ErrorHandler(logger=logger)

        error = ValueError("Standard error")
        result = handler.handle_error(error, context="test_function", return_value=42)

        assert result == 42
        logger.log.assert_called_once_with(logging.ERROR, "Unexpected error in test_function: Standard error")
        logger.debug.assert_called_once_with("Exception details", exc_info=True)

    def test_handle_error_without_context(self):
        """Test error handling without context."""
        logger = MagicMock(spec=logging.Logger)
        handler = ErrorHandler(logger=logger)

        error = RuntimeError("No context error")
        result = handler.handle_error(error, return_value=None)

        assert result is None
        logger.log.assert_called_once_with(logging.ERROR, "Unexpected error: No context error")

    def test_handle_error_custom_log_level(self):
        """Test error handling with custom log level."""
        logger = MagicMock(spec=logging.Logger)
        handler = ErrorHandler(logger=logger)

        error = Warning("Just a warning")
        handler.handle_error(error, log_level=logging.WARNING)

        logger.log.assert_called_once_with(logging.WARNING, "Unexpected error: Just a warning")

    @patch("grimperium.utils.error_handler.format_error_context")
    @patch("grimperium.utils.error_handler.time.time")
    def test_create_error_response_grimperium_error(self, mock_time, mock_format_error):
        """Test creating error response for GrimperiumError."""
        mock_time.return_value = 1234567890.0
        mock_format_error.return_value = {
            "message": "Test error",
            "error_code": "TEST_ERROR",
            "details": {"detail": "value"}
        }

        handler = ErrorHandler()
        error = GrimperiumError("Test error", "TEST_ERROR", {"detail": "value"})
        
        response = handler.create_error_response(error, success=False)

        expected = {
            "success": False,
            "error": {
                "message": "Test error",
                "error_code": "TEST_ERROR",
                "details": {"detail": "value"}
            },
            "timestamp": 1234567890.0
        }
        assert response == expected

    @patch("grimperium.utils.error_handler.time.time")
    def test_create_error_response_standard_error(self, mock_time):
        """Test creating error response for standard exceptions."""
        mock_time.return_value = 1234567890.0

        handler = ErrorHandler()
        error = ValueError("Standard error")
        
        response = handler.create_error_response(error, success=True)

        expected = {
            "success": True,
            "error": {
                "error_type": "ValueError",
                "error_code": "UNKNOWN_ERROR",
                "message": "Standard error",
                "details": {}
            },
            "timestamp": 1234567890.0
        }
        assert response == expected


class TestRetryOnError:
    """Test retry_on_error decorator."""

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_success_first_attempt(self, mock_sleep):
        """Test successful function execution on first attempt."""
        @retry_on_error(max_attempts=3)
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"
        mock_sleep.assert_not_called()

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_success_after_failure(self, mock_sleep):
        """Test successful execution after initial failures."""
        call_count = 0

        @retry_on_error(max_attempts=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)  # backoff_factor=2.0

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_max_attempts_exceeded(self, mock_sleep):
        """Test failure after exceeding max attempts."""
        @retry_on_error(max_attempts=2, delay=0.1)
        def test_func():
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            test_func()

        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(0.1)

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_specific_exceptions(self, mock_sleep):
        """Test retrying only on specific exceptions."""
        @retry_on_error(max_attempts=3, exceptions=ValueError)
        def test_func_value_error():
            raise ValueError("Retry this")

        @retry_on_error(max_attempts=3, exceptions=ValueError)
        def test_func_runtime_error():
            raise RuntimeError("Don't retry this")

        # ValueError should be retried
        with pytest.raises(ValueError):
            test_func_value_error()
        assert mock_sleep.call_count == 2

        # RuntimeError should not be retried
        mock_sleep.reset_mock()
        with pytest.raises(RuntimeError):
            test_func_runtime_error()
        mock_sleep.assert_not_called()

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_with_custom_logger(self, mock_sleep):
        """Test retry decorator with custom logger."""
        logger = MagicMock(spec=logging.Logger)

        @retry_on_error(max_attempts=2, logger=logger)
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

        logger.warning.assert_called_once()
        logger.error.assert_called_once()

    @patch("grimperium.utils.error_handler.time.sleep")
    def test_retry_backoff_factor(self, mock_sleep):
        """Test backoff factor calculation."""
        @retry_on_error(max_attempts=4, delay=1.0, backoff_factor=3.0)
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

        expected_calls = [
            mock.call(1.0),   # First retry
            mock.call(3.0),   # Second retry (1.0 * 3.0)
            mock.call(9.0),   # Third retry (3.0 * 3.0)
        ]
        mock_sleep.assert_has_calls(expected_calls)


class TestLogExceptions:
    """Test log_exceptions decorator."""

    def test_log_exceptions_success(self):
        """Test decorator with successful function execution."""
        logger = MagicMock(spec=logging.Logger)

        @log_exceptions(logger=logger)
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"
        logger.log.assert_not_called()

    def test_log_exceptions_with_reraise(self):
        """Test decorator with exception re-raising."""
        logger = MagicMock(spec=logging.Logger)

        @log_exceptions(logger=logger, reraise=True)
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_func()

        logger.log.assert_called_once_with(
            logging.ERROR,
            "Exception in test_func: Test error",
            exc_info=True
        )

    def test_log_exceptions_without_reraise(self):
        """Test decorator without re-raising exceptions."""
        logger = MagicMock(spec=logging.Logger)

        @log_exceptions(logger=logger, reraise=False)
        def test_func():
            raise ValueError("Test error")

        result = test_func()

        assert result is None
        logger.log.assert_called_once_with(
            logging.ERROR,
            "Exception in test_func: Test error",
            exc_info=True
        )

    def test_log_exceptions_custom_log_level(self):
        """Test decorator with custom log level."""
        logger = MagicMock(spec=logging.Logger)

        @log_exceptions(logger=logger, log_level=logging.WARNING, reraise=False)
        def test_func():
            raise ValueError("Test warning")

        result = test_func()

        assert result is None
        logger.log.assert_called_once_with(
            logging.WARNING,
            "Exception in test_func: Test warning",
            exc_info=True
        )

    def test_log_exceptions_default_logger(self):
        """Test decorator with default logger."""
        @log_exceptions(reraise=False)
        def test_func():
            raise ValueError("Test error")

        # Should not raise an exception due to reraise=False
        result = test_func()
        assert result is None


class TestValidateAndConvert:
    """Test validate_and_convert function."""

    def test_validate_string_success(self):
        """Test successful string validation and conversion."""
        result = validate_and_convert("  test  ", str, "field_name")
        assert result == "test"

    def test_validate_string_empty_required(self):
        """Test validation failure for empty required string."""
        with pytest.raises(ValidationError):
            validate_and_convert("", str, "field_name", required=True)

    def test_validate_string_empty_not_required(self):
        """Test validation of empty non-required string."""
        result = validate_and_convert("", str, "field_name", required=False, default="default")
        assert result == ""

    def test_validate_int_success(self):
        """Test successful integer validation and conversion."""
        result = validate_and_convert("42", int, "field_name")
        assert result == 42

    def test_validate_int_failure(self):
        """Test integer validation failure."""
        with pytest.raises(ValidationError):
            validate_and_convert("not_a_number", int, "field_name")

    def test_validate_float_success(self):
        """Test successful float validation and conversion."""
        result = validate_and_convert("3.14", float, "field_name")
        assert result == 3.14

    def test_validate_float_failure(self):
        """Test float validation failure."""
        with pytest.raises(ValidationError):
            validate_and_convert("not_a_float", float, "field_name")

    def test_validate_bool_string_true(self):
        """Test boolean validation with string true values."""
        true_values = ["true", "1", "yes", "on", "TRUE", "ON"]
        for value in true_values:
            result = validate_and_convert(value, bool, "field_name")
            assert result is True

    def test_validate_bool_string_false(self):
        """Test boolean validation with string false values."""
        false_values = ["false", "0", "no", "off", "FALSE", "OFF", "anything_else"]
        for value in false_values:
            result = validate_and_convert(value, bool, "field_name")
            assert result is False

    def test_validate_bool_non_string(self):
        """Test boolean validation with non-string values."""
        result = validate_and_convert(1, bool, "field_name")
        assert result is True
        
        result = validate_and_convert(0, bool, "field_name")
        assert result is False

    def test_validate_none_required(self):
        """Test validation failure for None required value."""
        with pytest.raises(ValidationError):
            validate_and_convert(None, str, "field_name", required=True)

    def test_validate_none_not_required(self):
        """Test validation success for None non-required value."""
        result = validate_and_convert(None, str, "field_name", required=False, default="default")
        assert result == "default"

    def test_validate_custom_type(self):
        """Test validation with custom type."""
        class CustomType:
            def __init__(self, value):
                self.value = str(value)

        result = validate_and_convert("test", CustomType, "field_name")
        assert isinstance(result, CustomType)
        assert result.value == "test"

    def test_validate_custom_type_failure(self):
        """Test validation failure with custom type."""
        class FailingType:
            def __init__(self, value):
                raise ValueError("Cannot create instance")

        with pytest.raises(ValidationError):
            validate_and_convert("test", FailingType, "field_name")


class TestSafeExecute:
    """Test safe_execute function."""

    def test_safe_execute_success(self):
        """Test successful function execution."""
        def test_func(a, b):
            return a + b

        result = safe_execute(test_func, args=(2, 3))
        assert result == 5

    def test_safe_execute_with_kwargs(self):
        """Test function execution with keyword arguments."""
        def test_func(a, b=10):
            return a * b

        result = safe_execute(test_func, args=(3,), kwargs={"b": 4})
        assert result == 12

    def test_safe_execute_failure_default_return(self):
        """Test function execution failure with default return value."""
        def test_func():
            raise ValueError("Test error")

        result = safe_execute(test_func, default_return="failed")
        assert result == "failed"

    def test_safe_execute_with_error_handler(self):
        """Test function execution with custom error handler."""
        error_handler = MagicMock(spec=ErrorHandler)
        error_handler.handle_error.return_value = "handled"

        def test_func():
            raise ValueError("Test error")

        result = safe_execute(
            test_func,
            default_return="default",
            error_handler=error_handler,
            context="test_context"
        )

        assert result == "handled"
        error_handler.handle_error.assert_called_once()

    def test_safe_execute_none_kwargs(self):
        """Test function execution with None kwargs."""
        def test_func():
            return "success"

        result = safe_execute(test_func, kwargs=None)
        assert result == "success"

    def test_safe_execute_default_error_handler(self):
        """Test function execution with default error handler."""
        def test_func():
            raise ValueError("Test error")

        # Should not raise an exception, should return default
        result = safe_execute(test_func, default_return="default")
        assert result == "default"