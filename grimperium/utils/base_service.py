"""
Base service class providing common functionality for all Grimperium services.

This module provides a base class that encapsulates common patterns like
logging setup, error handling, and validation that are used across all services.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union


class BaseService(ABC):
    """
    Abstract base class for all Grimperium services.
    
    This class provides common functionality that all services need:
    - Standardized logging setup
    - Common error handling patterns
    - Input validation helpers
    - Service identification
    """
    
    def __init__(self, service_name: Optional[str] = None):
        """
        Initialize the base service.
        
        Args:
            service_name: Name of the service for logging purposes.
                         If None, uses the class name.
        """
        self.service_name = service_name or self.__class__.__name__
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up a logger for this service instance.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(f"grimperium.{self.service_name.lower()}")
        return logger
    
    def log_info(self, message: str, *args, **kwargs) -> None:
        """Log an info message with service context."""
        self.logger.info(f"[{self.service_name}] {message}", *args, **kwargs)
    
    def log_debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message with service context."""
        self.logger.debug(f"[{self.service_name}] {message}", *args, **kwargs)
    
    def log_warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message with service context."""
        self.logger.warning(f"[{self.service_name}] {message}", *args, **kwargs)
    
    def log_error(self, message: str, *args, **kwargs) -> None:
        """Log an error message with service context."""
        self.logger.error(f"[{self.service_name}] {message}", *args, **kwargs)
    
    def validate_string_input(self, 
                            value: Any, 
                            param_name: str,
                            allow_empty: bool = False) -> Optional[str]:
        """
        Validate and sanitize string input.
        
        Args:
            value: Value to validate
            param_name: Name of parameter for error messages
            allow_empty: Whether to allow empty strings
            
        Returns:
            Sanitized string value or None if invalid
            
        Raises:
            ValueError: If validation fails
        """
        if value is None:
            if allow_empty:
                return None
            raise ValueError(f"{param_name} cannot be None")
        
        if not isinstance(value, str):
            raise ValueError(f"{param_name} must be a string, got {type(value).__name__}")
        
        sanitized = value.strip()
        if not sanitized and not allow_empty:
            raise ValueError(f"{param_name} cannot be empty")
        
        return sanitized
    
    def validate_path_input(self, 
                          path: Any, 
                          param_name: str,
                          must_exist: bool = False) -> str:
        """
        Validate path input.
        
        Args:
            path: Path to validate
            param_name: Name of parameter for error messages
            must_exist: Whether the path must exist
            
        Returns:
            Validated path string
            
        Raises:
            ValueError: If validation fails
        """
        from pathlib import Path
        
        path_str = self.validate_string_input(path, param_name)
        path_obj = Path(path_str)
        
        if must_exist and not path_obj.exists():
            raise ValueError(f"{param_name} does not exist: {path_str}")
        
        return str(path_obj.resolve())
    
    def handle_service_error(self, 
                           error: Exception, 
                           operation: str,
                           return_value: Any = None) -> Any:
        """
        Handle service errors with consistent logging and return patterns.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            return_value: Value to return on error (default: None)
            
        Returns:
            The specified return value
        """
        error_msg = f"Error during {operation}: {str(error)}"
        self.log_error(error_msg)
        self.log_debug(f"Error details for {operation}", exc_info=True)
        return return_value
    
    def create_service_result(self, 
                            success: bool,
                            data: Any = None,
                            error_message: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a standardized service result dictionary.
        
        Args:
            success: Whether the operation was successful
            data: The result data (if successful)
            error_message: Error message (if not successful)
            metadata: Additional metadata about the operation
            
        Returns:
            Standardized result dictionary
        """
        result = {
            'success': success,
            'service': self.service_name,
            'data': data,
            'error': error_message,
            'metadata': metadata or {}
        }
        
        return result


class FileServiceMixin:
    """
    Mixin class providing common file operation utilities.
    
    This mixin can be used with BaseService to add file-related functionality.
    """
    
    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if directory exists or was created successfully
        """
        from pathlib import Path
        
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            if hasattr(self, 'log_error'):
                self.log_error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    def check_file_exists_and_readable(self, file_path: str) -> bool:
        """
        Check if a file exists and is readable.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file exists and is readable
        """
        from pathlib import Path
        
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.stat().st_size > 0
        except Exception:
            return False
    
    def get_file_size_mb(self, file_path: str) -> float:
        """
        Get file size in megabytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in MB, or 0.0 if file doesn't exist
        """
        from pathlib import Path
        from ..constants import BYTES_PER_MB
        
        try:
            path = Path(file_path)
            if path.exists():
                return path.stat().st_size / BYTES_PER_MB
            return 0.0
        except Exception:
            return 0.0