"""
Error handling utilities for Grimperium.

This module provides utilities for consistent error handling, logging,
and retry mechanisms throughout the application.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union

from ..exceptions import GrimperiumError, format_error_context


class ErrorHandler:
    """
    Centralized error handling utility.

    This class provides methods for consistent error handling,
    logging, and response formatting across the application.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.

        Args:
            logger: Logger instance to use (creates one if None)
        """
        self.logger = logger or logging.getLogger(__name__)

    def handle_error(
        self,
        error: Exception,
        context: str = None,
        return_value: Any = None,
        log_level: int = logging.ERROR,
    ) -> Any:
        """
        Handle an error with consistent logging and return value.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            return_value: Value to return after handling the error
            log_level: Logging level to use

        Returns:
            The specified return value
        """
        if isinstance(error, GrimperiumError):
            # Handle custom exceptions with rich context
            error_info = format_error_context(error)
            message = f"Grimperium error"
            if context:
                message += f" in {context}"
            message += f": {error_info['message']}"

            self.logger.log(log_level, message)
            self.logger.debug(f"Error details: {error_info}")
        else:
            # Handle standard exceptions
            message = f"Unexpected error"
            if context:
                message += f" in {context}"
            message += f": {str(error)}"

            self.logger.log(log_level, message)
            self.logger.debug(f"Exception details", exc_info=True)

        return return_value

    def create_error_response(
        self, error: Exception, success: bool = False
    ) -> Dict[str, Any]:
        """
        Create a standardized error response dictionary.

        Args:
            error: The exception that occurred
            success: Whether to mark the response as successful

        Returns:
            Standardized error response dictionary
        """
        if isinstance(error, GrimperiumError):
            error_info = format_error_context(error)
            return {"success": success, "error": error_info, "timestamp": time.time()}
        else:
            return {
                "success": success,
                "error": {
                    "error_type": error.__class__.__name__,
                    "error_code": "UNKNOWN_ERROR",
                    "message": str(error),
                    "details": {},
                },
                "timestamp": time.time(),
            }


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """
    Decorator to retry a function on specific exceptions.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each failure
        exceptions: Exception types to retry on
        logger: Logger instance for retry messages

    Returns:
        Decorated function with retry behavior

    Example:
        @retry_on_error(max_attempts=3, delay=1.0, exceptions=NetworkError)
        def download_file(url):
            # Function that might fail due to network issues
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if logger is None:
                retry_logger = logging.getLogger(func.__module__)
            else:
                retry_logger = logger

            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed, re-raise the exception
                        retry_logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Log retry attempt
                    retry_logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )

                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


def log_exceptions(
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
) -> Callable:
    """
    Decorator to log exceptions that occur in a function.

    Args:
        logger: Logger instance to use
        log_level: Logging level for exception messages
        reraise: Whether to re-raise the exception after logging

    Returns:
        Decorated function with exception logging

    Example:
        @log_exceptions(logger=my_logger, reraise=False)
        def risky_function():
            # Function that might raise exceptions
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger

            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_logger.log(
                    log_level, f"Exception in {func.__name__}: {e}", exc_info=True
                )

                if reraise:
                    raise
                return None

        return wrapper

    return decorator


def validate_and_convert(
    value: Any,
    target_type: Type,
    field_name: str,
    required: bool = True,
    default: Any = None,
) -> Any:
    """
    Validate and convert a value to the target type with error handling.

    Args:
        value: Value to validate and convert
        target_type: Target type to convert to
        field_name: Name of the field for error messages
        required: Whether the field is required
        default: Default value if not required and value is None

    Returns:
        Converted value

    Raises:
        ValidationError: If validation fails
    """
    from ..exceptions import ValidationError

    # Handle None values
    if value is None:
        if required:
            raise ValidationError(field_name, value, f"non-None {target_type.__name__}")
        return default

    # Try to convert to target type
    try:
        if target_type == str:
            converted = str(value).strip()
            if required and not converted:
                raise ValidationError(field_name, value, "non-empty string")
            return converted
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        else:
            return target_type(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(field_name, str(value), target_type.__name__) from e


def safe_execute(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    default_return: Any = None,
    error_handler: Optional[ErrorHandler] = None,
    context: str = None,
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        default_return: Value to return if function fails
        error_handler: ErrorHandler instance for consistent error handling
        context: Context description for error messages

    Returns:
        Function result or default_return if function fails
    """
    if kwargs is None:
        kwargs = {}

    if error_handler is None:
        error_handler = ErrorHandler()

    try:
        return func(*args, **kwargs)
    except Exception as e:
        return error_handler.handle_error(
            error=e, context=context or func.__name__, return_value=default_return
        )
