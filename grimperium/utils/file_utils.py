"""
File operation utilities for Grimperium.

This module provides common file and path manipulation utilities
used throughout the computational chemistry pipeline.
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

from ..constants import (
    FILENAME_SANITIZATION_PATTERN,
    MULTIPLE_UNDERSCORES_PATTERN,
    MAX_EXTENSION_LENGTH,
    SUPPORTED_FORMATS
)


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize a filename to be safe for filesystem use.
    
    This function removes or replaces characters that are not safe
    for use in filenames across different operating systems.
    
    Args:
        filename: Original filename to sanitize
        replacement: Character to replace unsafe characters with
        
    Returns:
        Sanitized filename safe for filesystem use
        
    Example:
        >>> sanitize_filename("molecule<name>:test")
        "molecule_name__test"
    """
    if not filename:
        return "unnamed_file"
    
    # Replace unsafe characters
    sanitized = re.sub(FILENAME_SANITIZATION_PATTERN, replacement, filename)
    
    # Remove multiple replacement characters
    if replacement:
        pattern = re.escape(replacement) + '+'
        sanitized = re.sub(pattern, replacement, sanitized)
    
    # Remove leading/trailing replacement characters and dots
    sanitized = sanitized.strip(replacement + '.')
    
    # Ensure we have something left
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized


def ensure_directory_exists(directory_path: str, 
                          logger: Optional[logging.Logger] = None) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        logger: Logger instance for error reporting
        
    Returns:
        True if directory exists or was created successfully
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False


def validate_file_exists(file_path: str, 
                        must_be_readable: bool = True,
                        min_size_bytes: int = 0) -> Tuple[bool, str]:
    """
    Validate that a file exists and meets specified criteria.
    
    Args:
        file_path: Path to the file to validate
        must_be_readable: Whether the file must be readable
        min_size_bytes: Minimum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> valid, error = validate_file_exists("data.csv", min_size_bytes=100)
        >>> if not valid:
        ...     print(f"File validation failed: {error}")
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return False, f"File does not exist: {file_path}"
        
        if not path.is_file():
            return False, f"Path is not a file: {file_path}"
        
        file_size = path.stat().st_size
        if file_size < min_size_bytes:
            return False, f"File too small ({file_size} bytes, minimum {min_size_bytes}): {file_path}"
        
        if must_be_readable:
            try:
                with open(path, 'r', encoding='utf-8'):
                    pass
            except Exception as e:
                return False, f"File not readable: {file_path} ({str(e)})"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error validating file {file_path}: {str(e)}"


def get_file_extension(file_path: str) -> str:
    """
    Get the file extension from a file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension without the dot (lowercase)
        
    Example:
        >>> get_file_extension("molecule.SDF")
        "sdf"
    """
    path = Path(file_path)
    extension = path.suffix.lstrip('.').lower()
    return extension


def is_supported_format(file_format: str) -> bool:
    """
    Check if a file format is supported by Grimperium.
    
    Args:
        file_format: File format/extension to check
        
    Returns:
        True if format is supported
    """
    format_clean = file_format.lower().lstrip('.')
    return format_clean in SUPPORTED_FORMATS


def validate_file_format(file_path: str, 
                        expected_formats: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate that a file has an expected format.
    
    Args:
        file_path: Path to the file
        expected_formats: List of expected formats (None to allow any supported format)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    extension = get_file_extension(file_path)
    
    if not extension:
        return False, f"File has no extension: {file_path}"
    
    if len(extension) > MAX_EXTENSION_LENGTH:
        return False, f"File extension too long: {extension}"
    
    if expected_formats:
        # Check against specific expected formats
        expected_clean = [fmt.lower().lstrip('.') for fmt in expected_formats]
        if extension not in expected_clean:
            return False, f"Unexpected file format '{extension}', expected one of: {expected_formats}"
    else:
        # Check against supported formats
        if not is_supported_format(extension):
            supported = list(SUPPORTED_FORMATS.keys())
            return False, f"Unsupported file format '{extension}', supported formats: {supported}"
    
    return True, ""


def find_files_by_pattern(directory: str, 
                         pattern: str,
                         recursive: bool = False,
                         max_results: Optional[int] = None) -> List[str]:
    """
    Find files in a directory matching a pattern.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match
        recursive: Whether to search recursively
        max_results: Maximum number of results to return
        
    Returns:
        List of matching file paths
        
    Example:
        >>> files = find_files_by_pattern("/data", "*.csv", recursive=True)
        >>> print(f"Found {len(files)} CSV files")
    """
    try:
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return []
        
        if recursive:
            matches = path.rglob(pattern)
        else:
            matches = path.glob(pattern)
        
        # Convert to list and filter to files only
        result = [str(p.absolute()) for p in matches if p.is_file()]
        
        # Apply max results limit
        if max_results and len(result) > max_results:
            result = result[:max_results]
        
        return sorted(result)
        
    except Exception:
        return []


def get_unique_output_path(base_path: str, 
                          extension: Optional[str] = None) -> str:
    """
    Generate a unique output file path by adding numbers if file exists.
    
    Args:
        base_path: Base file path
        extension: New extension (keeps original if None)
        
    Returns:
        Unique file path that doesn't exist
        
    Example:
        >>> path = get_unique_output_path("output.txt")
        >>> # Returns "output.txt" if doesn't exist, or "output_1.txt", etc.
    """
    base = Path(base_path)
    
    if extension:
        base = base.with_suffix('.' + extension.lstrip('.'))
    
    if not base.exists():
        return str(base)
    
    # Generate numbered versions
    counter = 1
    while True:
        stem = base.stem
        suffix = base.suffix
        parent = base.parent
        
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        
        if not new_path.exists():
            return str(new_path)
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 1000:
            raise RuntimeError(f"Could not generate unique path for {base_path}")


def copy_file_safely(source_path: str, 
                     destination_path: str,
                     overwrite: bool = False,
                     logger: Optional[logging.Logger] = None) -> bool:
    """
    Copy a file safely with error handling and logging.
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
        overwrite: Whether to overwrite existing files
        logger: Logger instance
        
    Returns:
        True if copy was successful
    """
    import shutil
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        source = Path(source_path)
        destination = Path(destination_path)
        
        # Validate source
        if not source.exists():
            logger.error(f"Source file does not exist: {source_path}")
            return False
        
        if not source.is_file():
            logger.error(f"Source is not a file: {source_path}")
            return False
        
        # Check destination
        if destination.exists() and not overwrite:
            logger.error(f"Destination exists and overwrite=False: {destination_path}")
            return False
        
        # Ensure destination directory exists
        ensure_directory_exists(str(destination.parent), logger)
        
        # Copy file
        shutil.copy2(source, destination)
        logger.debug(f"File copied: {source_path} -> {destination_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error copying file {source_path} -> {destination_path}: {e}")
        return False


def cleanup_temp_files(file_paths: List[str], 
                      logger: Optional[logging.Logger] = None) -> int:
    """
    Clean up temporary files safely.
    
    Args:
        file_paths: List of file paths to delete
        logger: Logger instance
        
    Returns:
        Number of files successfully deleted
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    deleted_count = 0
    
    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug(f"Deleted temporary file: {file_path}")
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Could not delete temporary file {file_path}: {e}")
    
    return deleted_count