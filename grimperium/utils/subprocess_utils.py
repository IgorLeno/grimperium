"""
Subprocess execution utilities for Grimperium.

This module provides wrapper functions for executing external programs
with consistent error handling, timeouts, and logging.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..constants import EXECUTABLE_VALIDATION_TIMEOUT


class SubprocessResult:
    """
    Container for subprocess execution results.

    This class provides a standardized way to handle subprocess results
    with additional metadata and helper methods.
    """

    def __init__(
        self,
        command: List[str],
        returncode: int,
        stdout: str,
        stderr: str,
        timeout_occurred: bool = False,
        execution_time: Optional[float] = None,
    ):
        """
        Initialize subprocess result.

        Args:
            command: The command that was executed
            returncode: Process return code
            stdout: Standard output
            stderr: Standard error
            timeout_occurred: Whether execution timed out
            execution_time: Execution time in seconds
        """
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timeout_occurred = timeout_occurred
        self.execution_time = execution_time

    @property
    def success(self) -> bool:
        """Check if the command executed successfully."""
        return self.returncode == 0 and not self.timeout_occurred

    @property
    def command_str(self) -> str:
        """Get the command as a string."""
        return " ".join(self.command)

    def __str__(self) -> str:
        """String representation of the result."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"SubprocessResult({self.command_str}) -> {status} (code: {self.returncode})"


def execute_command(
    command: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    text: bool = True,
    env: Optional[Dict[str, str]] = None,
    logger: Optional[logging.Logger] = None,
) -> SubprocessResult:
    """
    Execute a command with comprehensive error handling and logging.

    This function provides a standardized way to execute external commands
    with consistent error handling, timeout management, and logging.

    Args:
        command: Command and arguments to execute
        cwd: Working directory for command execution
        timeout: Timeout in seconds (None for no timeout)
        capture_output: Whether to capture stdout and stderr
        text: Whether to return output as text (vs bytes)
        env: Environment variables for the process
        logger: Logger instance for output (creates one if None)

    Returns:
        SubprocessResult containing execution details

    Example:
        >>> result = execute_command(['ls', '-la'], cwd='/tmp')
        >>> if result.success:
        ...     print("Directory listing:", result.stdout)
        ... else:
        ...     print("Command failed:", result.stderr)
    """
    import time

    if logger is None:
        logger = logging.getLogger(__name__)

    # Validate command
    if not command or not isinstance(command, list):
        raise ValueError("Command must be a non-empty list")

    # Log execution start
    command_str = " ".join(command)
    logger.debug(f"Executing command: {command_str}")
    if cwd:
        logger.debug(f"Working directory: {cwd}")
    if timeout:
        logger.debug(f"Timeout: {timeout} seconds")

    start_time = time.time()
    timeout_occurred = False

    try:
        # Execute the command
        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=text,
            env=env,
        )

        execution_time = time.time() - start_time

        # Create result object
        subprocess_result = SubprocessResult(
            command=command,
            returncode=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            timeout_occurred=False,
            execution_time=execution_time,
        )

        # Log results
        if subprocess_result.success:
            logger.debug(f"Command completed successfully in {execution_time:.2f}s")
        else:
            logger.warning(f"Command failed with return code {result.returncode}")
            if capture_output and result.stderr:
                logger.debug(f"Command stderr: {result.stderr.strip()}")

        return subprocess_result

    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        timeout_occurred = True

        logger.error(f"Command timed out after {timeout} seconds")

        return SubprocessResult(
            command=command,
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            timeout_occurred=True,
            execution_time=execution_time,
        )

    except FileNotFoundError:
        execution_time = time.time() - start_time
        error_msg = f"Executable not found: {command[0]}"
        logger.error(error_msg)

        return SubprocessResult(
            command=command,
            returncode=-1,
            stdout="",
            stderr=error_msg,
            timeout_occurred=False,
            execution_time=execution_time,
        )

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Unexpected error executing command: {str(e)}"
        logger.error(error_msg)

        return SubprocessResult(
            command=command,
            returncode=-1,
            stdout="",
            stderr=error_msg,
            timeout_occurred=False,
            execution_time=execution_time,
        )


def check_executable_available(
    executable_name: str, logger: Optional[logging.Logger] = None
) -> bool:
    """
    Check if an executable is available in the system PATH.

    Args:
        executable_name: Name of the executable to check
        logger: Logger instance (creates one if None)

    Returns:
        True if executable is available, False otherwise
    """
    import shutil

    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        path = shutil.which(executable_name)
        if path:
            logger.debug(f"Executable '{executable_name}' found at: {path}")
            return True
        else:
            logger.debug(f"Executable '{executable_name}' not found in PATH")
            return False
    except Exception as e:
        logger.error(f"Error checking executable '{executable_name}': {e}")
        return False


def validate_executable_version(
    executable_name: str,
    version_args: Optional[List[str]] = None,
    timeout: int = EXECUTABLE_VALIDATION_TIMEOUT,
    logger: Optional[logging.Logger] = None,
) -> Optional[str]:
    """
    Validate an executable and retrieve its version information.

    Args:
        executable_name: Name of the executable
        version_args: Arguments to get version (defaults to ['--version'])
        timeout: Timeout for version check
        logger: Logger instance

    Returns:
        Version string if successful, None if failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if version_args is None:
        version_args = ["--version"]

    # First check if executable exists
    if not check_executable_available(executable_name, logger):
        return None

    # Try to get version
    command = [executable_name] + version_args
    result = execute_command(command, timeout=timeout, logger=logger)

    if result.success:
        version_output = result.stdout.strip()
        logger.debug(f"Version check for '{executable_name}': {version_output}")
        return version_output
    else:
        logger.warning(
            f"Could not get version for '{executable_name}': {result.stderr}"
        )
        return None


def create_output_file_path(
    input_path: str, new_extension: str, output_dir: Optional[str] = None
) -> str:
    """
    Create an output file path based on input path and new extension.

    Args:
        input_path: Path to the input file
        new_extension: New file extension (without dot)
        output_dir: Output directory (uses input file directory if None)

    Returns:
        Path to the output file

    Example:
        >>> create_output_file_path("input.xyz", "pdb", "/output")
        "/output/input.pdb"
    """
    input_path_obj = Path(input_path)

    # Create output filename
    output_filename = input_path_obj.stem + "." + new_extension.lstrip(".")

    # Determine output directory
    if output_dir:
        output_path = Path(output_dir) / output_filename
    else:
        output_path = input_path_obj.parent / output_filename

    return str(output_path.absolute())
