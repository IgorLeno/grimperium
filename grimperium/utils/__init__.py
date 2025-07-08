"""
Utility modules for Grimperium.

This package provides common utilities used throughout the application:
- Base service classes
- File operation utilities  
- Subprocess execution helpers
- Configuration management
"""

from .base_service import BaseService, FileServiceMixin
from .subprocess_utils import (
    SubprocessResult,
    execute_command,
    check_executable_available,
    validate_executable_version,
    create_output_file_path
)
from .file_utils import (
    sanitize_filename,
    ensure_directory_exists,
    validate_file_exists,
    get_file_extension,
    is_supported_format,
    validate_file_format,
    find_files_by_pattern,
    get_unique_output_path,
    copy_file_safely,
    cleanup_temp_files
)
from .error_handler import (
    ErrorHandler,
    retry_on_error,
    log_exceptions,
    validate_and_convert,
    safe_execute
)

__all__ = [
    # Base service
    'BaseService',
    'FileServiceMixin',
    
    # Subprocess utilities
    'SubprocessResult',
    'execute_command',
    'check_executable_available', 
    'validate_executable_version',
    'create_output_file_path',
    
    # File utilities
    'sanitize_filename',
    'ensure_directory_exists',
    'validate_file_exists',
    'get_file_extension',
    'is_supported_format',
    'validate_file_format',
    'find_files_by_pattern',
    'get_unique_output_path',
    'copy_file_safely',
    'cleanup_temp_files',
    
    # Error handling
    'ErrorHandler',
    'retry_on_error',
    'log_exceptions',
    'validate_and_convert',
    'safe_execute'
]