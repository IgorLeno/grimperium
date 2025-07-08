"""
File format conversion service using OpenBabel.

This module provides functionality to convert between different molecular file
formats using the OpenBabel command-line tool. It supports all formats that
OpenBabel can handle, with robust error handling and path management.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from ..constants import CONVERSION_TIMEOUT, EXECUTABLE_VALIDATION_TIMEOUT


def convert_file(input_path: str, output_format: str) -> Optional[str]:
    """
    Convert a molecular structure file to a different format using OpenBabel.
    
    This function uses the OpenBabel command-line tool (obabel) to convert
    molecular structure files between different formats. The output file is
    created in the same directory as the input file with the appropriate
    file extension.
    
    Args:
        input_path: Path to the input molecular structure file
        output_format: Target file format (e.g., 'xyz', 'sdf', 'mol2', 'pdb')
        
    Returns:
        The full path to the converted output file if successful, None otherwise
        
    Example:
        >>> convert_file("repository/sdf/ethanol.sdf", "xyz")
        "/path/to/repository/sdf/ethanol.xyz"
    """
    # Set up logging
    logger = logging.getLogger(__name__)
    
    try:
        # Validate input file exists
        input_file = Path(input_path)
        if not input_file.exists():
            logger.error(f"Input file does not exist: {input_path}")
            return None
            
        if not input_file.is_file():
            logger.error(f"Input path is not a file: {input_path}")
            return None
        
        # Construct output path
        output_file = input_file.with_suffix(f".{output_format.lower()}")
        
        # Build OpenBabel command
        command = [
            "obabel",
            str(input_file.absolute()),
            "-O",
            str(output_file.absolute())
        ]
        
        logger.info(f"Converting {input_path} to {output_format} format")
        logger.debug(f"OpenBabel command: {' '.join(command)}")
        
        # Execute OpenBabel conversion
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT
        )
        
        # Check if conversion was successful
        if result.returncode != 0:
            logger.error(f"OpenBabel conversion failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"OpenBabel stderr: {result.stderr.strip()}")
            if result.stdout:
                logger.debug(f"OpenBabel stdout: {result.stdout.strip()}")
            return None
        
        # Verify output file was created
        if not output_file.exists():
            logger.error(f"Output file was not created: {output_file}")
            return None
            
        # Check if output file has content
        if output_file.stat().st_size == 0:
            logger.error(f"Output file is empty: {output_file}")
            return None
        
        logger.info(f"Successfully converted to: {output_file}")
        if result.stdout:
            logger.debug(f"OpenBabel stdout: {result.stdout.strip()}")
            
        return str(output_file.absolute())
        
    except subprocess.TimeoutExpired:
        logger.error(f"OpenBabel conversion timed out for file: {input_path}")
        return None
        
    except FileNotFoundError:
        logger.error(
            "OpenBabel (obabel) not found. Please ensure OpenBabel is installed "
            "and available in your PATH."
        )
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error during file conversion: {e}")
        return None


def get_supported_formats() -> list[str]:
    """
    Get a list of supported file formats from OpenBabel.
    
    This function queries OpenBabel to get the list of supported input and
    output formats. This can be useful for validation and user interface
    purposes.
    
    Returns:
        List of supported file format extensions, or empty list if query fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Query OpenBabel for supported formats
        result = subprocess.run(
            ["obabel", "-L", "formats"],
            capture_output=True,
            text=True,
            timeout=EXECUTABLE_VALIDATION_TIMEOUT
        )
        
        if result.returncode != 0:
            logger.warning("Could not query OpenBabel for supported formats")
            return []
        
        # Parse the output to extract format extensions
        formats = []
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('#'):
                # Format lines typically start with the extension
                parts = line.split()
                if parts and len(parts[0]) <= 5:  # Reasonable extension length
                    formats.append(parts[0].lower())
        
        return sorted(set(formats))  # Remove duplicates and sort
        
    except Exception as e:
        logger.warning(f"Error querying OpenBabel formats: {e}")
        return []