"""
PubChem integration service for molecular structure retrieval.

This module provides functionality to download molecular structures from the
PubChem database in SDF format. It handles compound lookup by name and manages
file downloads with proper error handling and path sanitization.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import pubchempy as pcp

from ..constants import (
    FILENAME_SANITIZATION_PATTERN,
    PUBCHEM_FILENAME_FALLBACK,
    PUBCHEM_SANITIZATION_REPLACEMENT
)


def sanitize_filename(name: str) -> str:
    """
    Sanitize a molecule name to create a safe filename.
    
    Removes or replaces characters that are not safe for filenames,
    ensuring cross-platform compatibility.
    
    Args:
        name: The molecule name to sanitize
        
    Returns:
        A sanitized filename-safe string
    """
    # Replace unsafe characters and spaces using constants
    sanitized = re.sub(FILENAME_SANITIZATION_PATTERN, PUBCHEM_SANITIZATION_REPLACEMENT, name)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Ensure we have something left
    if not sanitized:
        sanitized = PUBCHEM_FILENAME_FALLBACK
    return sanitized


def download_sdf_by_name(name: str, output_dir: str) -> Optional[str]:
    """
    Download a 3D SDF structure file for a compound by name from PubChem.
    
    This function searches PubChem for a compound by name, retrieves its 3D
    structure data, and saves it as an SDF file in the specified directory.
    The function includes robust error handling for network issues and
    missing compounds.
    
    Args:
        name: The compound name to search for in PubChem
        output_dir: Directory where the SDF file should be saved
        
    Returns:
        The full path to the downloaded SDF file if successful, None otherwise
        
    Raises:
        No exceptions are raised; all errors are logged and None is returned
    """
    # Set up logging
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Search for the compound by name
        logger.info(f"Searching PubChem for compound: {name}")
        compounds = pcp.get_compounds(name, 'name')
        
        if not compounds:
            logger.warning(f"No compounds found in PubChem for name: {name}")
            return None
            
        # Get the first compound (most relevant match)
        compound = compounds[0]
        logger.info(f"Found compound: {compound.iupac_name or name} (CID: {compound.cid})")
        
        # Try to get 3D SDF data
        try:
            sdf_data = pcp.get_sdf(compound.cid, record_type='3d')
            if not sdf_data:
                logger.warning(f"No 3D structure available for compound {name} (CID: {compound.cid})")
                return None
        except Exception as e:
            logger.warning(f"Failed to retrieve 3D SDF for {name}: {e}")
            # Fallback to 2D structure
            try:
                logger.info(f"Attempting to retrieve 2D structure for {name}")
                sdf_data = pcp.get_sdf(compound.cid, record_type='2d')
                if not sdf_data:
                    logger.error(f"No structure data available for compound {name}")
                    return None
            except Exception as e2:
                logger.error(f"Failed to retrieve any structure for {name}: {e2}")
                return None
        
        # Create sanitized filename
        sanitized_name = sanitize_filename(name)
        sdf_filename = f"{sanitized_name}.sdf"
        sdf_path = output_path / sdf_filename
        
        # Write SDF data to file
        with open(sdf_path, 'w', encoding='utf-8') as f:
            f.write(sdf_data)
        
        logger.info(f"Successfully downloaded SDF file: {sdf_path}")
        return str(sdf_path.absolute())
        
    except pcp.NotFoundError:
        logger.warning(f"Compound '{name}' not found in PubChem database")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error downloading SDF for '{name}': {e}")
        return None