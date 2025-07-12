"""
Custom exceptions for the Grimperium application.

This module defines custom exception classes that provide better error
handling and more specific error information throughout the application.
"""


class GrimperiumError(Exception):
    """
    Base exception class for all Grimperium-specific errors.

    This class serves as the parent for all custom exceptions in the
    application, allowing for easy exception categorization and handling.
    """

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        """
        Initialize the base Grimperium exception.

        Args:
            message: Human-readable error message
            error_code: Unique error code for programmatic handling
            details: Additional error details and context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GRIMPERIUM_UNKNOWN_ERROR"
        self.details = details or {}

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({self.error_code}) [{details_str}]"
        return f"{self.message} ({self.error_code})"


class ConfigurationError(GrimperiumError):
    """
    Raised when there are configuration-related errors.

    This includes missing configuration files, invalid configuration
    sections, missing required settings, or invalid configuration values.
    """

    def __init__(self, message: str, config_path: str = None, section: str = None):
        error_code = "CONFIG_ERROR"
        details = {}

        if config_path:
            details["config_path"] = config_path
        if section:
            details["section"] = section

        super().__init__(message, error_code, details)


class ExecutableNotFoundError(GrimperiumError):
    """
    Raised when a required executable is not found or not working.

    This includes missing computational chemistry programs like CREST,
    MOPAC, or OpenBabel that are required for the pipeline to function.
    """

    def __init__(self, executable_name: str, path_searched: str = None):
        message = f"Required executable '{executable_name}' not found or not working"
        error_code = "EXECUTABLE_NOT_FOUND"
        details = {"executable": executable_name}

        if path_searched:
            details["path_searched"] = path_searched

        super().__init__(message, error_code, details)


class FileOperationError(GrimperiumError):
    """
    Raised when file operations fail.

    This includes file reading, writing, conversion, or validation errors.
    """

    def __init__(self, operation: str, file_path: str, reason: str = None):
        message = f"File operation '{operation}' failed for: {file_path}"
        if reason:
            message += f" - {reason}"

        error_code = "FILE_OPERATION_ERROR"
        details = {"operation": operation, "file_path": file_path}

        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)


class MoleculeProcessingError(GrimperiumError):
    """
    Raised when molecule processing fails.

    This includes errors in structure download, format conversion,
    conformational search, energy calculation, or database storage.
    """

    def __init__(self, stage: str, molecule_id: str, reason: str = None):
        message = f"Molecule processing failed at stage '{stage}' for: {molecule_id}"
        if reason:
            message += f" - {reason}"

        error_code = "MOLECULE_PROCESSING_ERROR"
        details = {"stage": stage, "molecule_id": molecule_id}

        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)


class CalculationError(GrimperiumError):
    """
    Raised when computational chemistry calculations fail.

    This includes CREST conformational search failures, MOPAC calculation
    errors, or energy extraction problems.
    """

    def __init__(
        self, calculation_type: str, input_file: str = None, reason: str = None
    ):
        message = f"Calculation '{calculation_type}' failed"
        if input_file:
            message += f" for input: {input_file}"
        if reason:
            message += f" - {reason}"

        error_code = "CALCULATION_ERROR"
        details = {"calculation_type": calculation_type}

        if input_file:
            details["input_file"] = input_file
        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)


class DatabaseError(GrimperiumError):
    """
    Raised when database operations fail.

    This includes connection errors, schema validation failures,
    data insertion errors, or query execution problems.
    """

    def __init__(self, operation: str, database_path: str = None, reason: str = None):
        message = f"Database operation '{operation}' failed"
        if database_path:
            message += f" for database: {database_path}"
        if reason:
            message += f" - {reason}"

        error_code = "DATABASE_ERROR"
        details = {"operation": operation}

        if database_path:
            details["database_path"] = database_path
        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)


class ValidationError(GrimperiumError):
    """
    Raised when input validation fails.

    This includes invalid file formats, missing required parameters,
    or data that doesn't meet expected criteria.
    """

    def __init__(self, field: str, value: str = None, expected: str = None):
        message = f"Validation failed for field '{field}'"
        if value:
            message += f" with value: {value}"
        if expected:
            message += f" (expected: {expected})"

        error_code = "VALIDATION_ERROR"
        details = {"field": field}

        if value:
            details["value"] = value
        if expected:
            details["expected"] = expected

        super().__init__(message, error_code, details)


class NetworkError(GrimperiumError):
    """
    Raised when network operations fail.

    This includes PubChem API failures, download timeouts,
    or connectivity issues.
    """

    def __init__(self, operation: str, url: str = None, reason: str = None):
        message = f"Network operation '{operation}' failed"
        if url:
            message += f" for URL: {url}"
        if reason:
            message += f" - {reason}"

        error_code = "NETWORK_ERROR"
        details = {"operation": operation}

        if url:
            details["url"] = url
        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)


# Error codes for programmatic handling
ERROR_CODES = {
    "GRIMPERIUM_UNKNOWN_ERROR": "An unknown error occurred",
    "CONFIG_ERROR": "Configuration related error",
    "EXECUTABLE_NOT_FOUND": "Required executable not found",
    "FILE_OPERATION_ERROR": "File operation failed",
    "MOLECULE_PROCESSING_ERROR": "Molecule processing failed",
    "CALCULATION_ERROR": "Computational chemistry calculation failed",
    "DATABASE_ERROR": "Database operation failed",
    "VALIDATION_ERROR": "Input validation failed",
    "NETWORK_ERROR": "Network operation failed",
}


def get_error_description(error_code: str) -> str:
    """
    Get a description for an error code.

    Args:
        error_code: The error code to look up

    Returns:
        Description of the error code, or a default message if not found
    """
    return ERROR_CODES.get(error_code, "Unknown error code")


def format_error_context(exception: GrimperiumError) -> dict:
    """
    Format exception context for logging or API responses.

    Args:
        exception: A GrimperiumError instance

    Returns:
        Dictionary with formatted error context
    """
    return {
        "error_type": exception.__class__.__name__,
        "error_code": exception.error_code,
        "message": exception.message,
        "details": exception.details,
        "description": get_error_description(exception.error_code),
    }
