"""
Computational chemistry calculation service.

This module provides functionality to execute external computational chemistry
programs (CREST and MOPAC) and parse their output files. It handles subprocess
execution, file management, and result extraction with robust error handling.
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from ..constants import (
    CREST_TIMEOUT,
    MOPAC_TIMEOUT,
    CONVERSION_TIMEOUT,
    ENERGY_EXTRACTION_PATTERN,
    EXECUTABLE_VALIDATION_TIMEOUT,
)


def run_crest(
    input_xyz_path: str, output_dir: str, crest_keywords: str
) -> Optional[str]:
    """
    Execute CREST conformational search calculations.

    This function runs the CREST program for conformational analysis and
    optimization. CREST is executed within the specified output directory
    to ensure proper file organization.

    Args:
        input_xyz_path: Path to the input XYZ coordinate file
        output_dir: Directory where CREST should run and store output files
        crest_keywords: Command-line keywords/options for CREST

    Returns:
        Path to the crest_best.xyz file if successful, None otherwise

    Example:
        >>> run_crest("molecule.xyz", "crest_output", "--gfn2")
        "/path/to/crest_output/crest_best.xyz"
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate input file
        input_file = Path(input_xyz_path)
        if not input_file.exists():
            logger.error(f"Input XYZ file does not exist: {input_xyz_path}")
            return None

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Build CREST command
        command = ["crest", str(input_file.absolute())]

        # Add keywords if provided
        if crest_keywords.strip():
            # Split keywords and add them to command
            keywords = crest_keywords.strip().split()
            command.extend(keywords)

        logger.info(f"Running CREST calculation in directory: {output_dir}")
        logger.debug(f"CREST command: {' '.join(command)}")

        # Execute CREST (run in output directory)
        result = subprocess.run(
            command,
            cwd=str(output_path.absolute()),
            capture_output=True,
            text=True,
            timeout=CREST_TIMEOUT,
        )

        # Check execution result
        if result.returncode != 0:
            logger.error(f"CREST execution failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"CREST stderr: {result.stderr.strip()}")
            if result.stdout:
                logger.debug(f"CREST stdout: {result.stdout.strip()}")
            return None

        # Look for the best conformer file
        best_xyz_path = output_path / "crest_best.xyz"
        if not best_xyz_path.exists():
            logger.error(f"CREST best conformer file not found: {best_xyz_path}")
            return None

        # Verify file has content
        if best_xyz_path.stat().st_size == 0:
            logger.error(f"CREST best conformer file is empty: {best_xyz_path}")
            return None

        logger.info(f"CREST calculation completed successfully")
        logger.info(f"Best conformer saved to: {best_xyz_path}")

        return str(best_xyz_path.absolute())

    except subprocess.TimeoutExpired:
        logger.error(f"CREST calculation timed out for file: {input_xyz_path}")
        return None

    except FileNotFoundError:
        logger.error(
            "CREST executable not found. Please ensure CREST is installed "
            "and available in your PATH."
        )
        return None

    except Exception as e:
        logger.error(f"Unexpected error during CREST calculation: {e}")
        return None


def run_mopac(input_file_path: str, mopac_keywords: str) -> Optional[str]:
    """
    Execute MOPAC quantum chemistry calculations.

    This function reads coordinates from a PDB file, creates a proper MOPAC
    input file (.mop), and runs MOPAC calculations on it.

    Args:
        input_file_path: Path to PDB file containing molecular coordinates
        mopac_keywords: Keywords/options for the MOPAC calculation

    Returns:
        Path to the MOPAC output (.out) file if successful, None otherwise

    Example:
        >>> run_mopac("crest_best.pdb", "PM7 PRECISE")
        "/path/to/crest_best.out"
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate input file
        input_file = Path(input_file_path)
        if not input_file.exists():
            logger.error(f"Input file does not exist: {input_file_path}")
            return None

        # Read coordinates from PDB file
        coordinates = []
        molecule_name = input_file.stem

        with open(input_file, "r") as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    # Extract atom symbol and coordinates from PDB format
                    atom_symbol = line[76:78].strip()
                    if not atom_symbol:
                        atom_symbol = line[12:16].strip()[:2]
                        atom_symbol = "".join(c for c in atom_symbol if c.isalpha())

                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())

                    coordinates.append(f"{atom_symbol:2} {x:12.6f} {y:12.6f} {z:12.6f}")

        if not coordinates:
            logger.error(f"No atomic coordinates found in PDB file: {input_file_path}")
            return None

        # Create MOPAC input content
        mop_content = f"{mopac_keywords}\n{molecule_name} - MOPAC Calculation\n\n"
        mop_content += "\n".join(coordinates)

        # Create .mop file
        mop_file = input_file.with_suffix(".mop")
        with open(mop_file, "w") as f:
            f.write(mop_content)

        logger.info(f"Created MOPAC input file: {mop_file}")

        # Build MOPAC command
        command = ["mopac", str(mop_file.absolute())]

        # Determine expected output file path
        output_file = mop_file.with_suffix(".out")

        logger.info(f"Running MOPAC calculation on: {mop_file}")
        logger.debug(f"MOPAC command: {' '.join(command)}")

        # Execute MOPAC
        result = subprocess.run(
            command,
            cwd=str(mop_file.parent.absolute()),
            capture_output=True,
            text=True,
            timeout=MOPAC_TIMEOUT,
        )

        # Check execution result
        if result.returncode != 0:
            logger.error(f"MOPAC execution failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"MOPAC stderr: {result.stderr.strip()}")
            if result.stdout:
                logger.debug(f"MOPAC stdout: {result.stdout.strip()}")
            return None

        # Verify output file was created
        if not output_file.exists():
            logger.error(f"MOPAC output file not found: {output_file}")
            return None

        # Verify file has content
        if output_file.stat().st_size == 0:
            logger.error(f"MOPAC output file is empty: {output_file}")
            return None

        logger.info(f"MOPAC calculation completed successfully")
        logger.info(f"Output saved to: {output_file}")

        return str(output_file.absolute())

    except subprocess.TimeoutExpired:
        logger.error(f"MOPAC calculation timed out for file: {input_file_path}")
        return None

    except FileNotFoundError:
        logger.error(
            "MOPAC executable not found. Please ensure MOPAC is installed "
            "and available in your PATH."
        )
        return None

    except Exception as e:
        logger.error(f"Unexpected error during MOPAC calculation: {e}")
        return None


def parse_mopac_output(output_file_path: str) -> Optional[float]:
    """
    Parse MOPAC output file to extract the final heat of formation.

    This function reads a MOPAC output file and extracts the final heat of
    formation value using regular expressions. The function is designed to
    handle various MOPAC output formats and provide robust error handling.

    Args:
        output_file_path: Path to the MOPAC output (.out) file

    Returns:
        The final heat of formation value in kcal/mol if found, None otherwise

    Example:
        >>> parse_mopac_output("molecule.out")
        -74.326
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate output file exists
        output_file = Path(output_file_path)
        if not output_file.exists():
            logger.error(f"MOPAC output file does not exist: {output_file_path}")
            return None

        if not output_file.is_file():
            logger.error(f"Path is not a file: {output_file_path}")
            return None

        logger.debug(f"Parsing MOPAC output file: {output_file_path}")

        # Use the standard energy extraction pattern from constants

        # Read and search the output file
        with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Search for the pattern
        matches = re.findall(ENERGY_EXTRACTION_PATTERN, content, re.IGNORECASE)

        if not matches:
            logger.warning(f"No 'FINAL HEAT OF FORMATION' found in: {output_file_path}")
            return None

        # Take the last occurrence (most relevant for optimization jobs)
        final_energy = float(matches[-1])

        logger.info(f"Extracted final heat of formation: {final_energy} kcal/mol")
        return final_energy

    except ValueError as e:
        logger.error(f"Could not convert energy value to float: {e}")
        return None

    except IOError as e:
        logger.error(f"Error reading MOPAC output file: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error parsing MOPAC output: {e}")
        return None


def validate_crest_installation() -> bool:
    """
    Check if CREST is properly installed and accessible.

    Returns:
        True if CREST is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["crest", "--help"],
            capture_output=True,
            text=True,
            timeout=EXECUTABLE_VALIDATION_TIMEOUT,
        )
        return result.returncode == 0
    except Exception:
        return False


def validate_mopac_installation() -> bool:
    """
    Check if MOPAC is properly installed and accessible.

    Returns:
        True if MOPAC is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["mopac"],
            capture_output=True,
            text=True,
            timeout=EXECUTABLE_VALIDATION_TIMEOUT,
        )
        # MOPAC typically returns non-zero when called without arguments
        # but should not raise FileNotFoundError
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return True  # Other exceptions might still indicate MOPAC is present
