"""
Pipeline orchestration service for Grimperium computational chemistry workflows.

This module coordinates the execution of the complete computational chemistry
pipeline, managing the flow of data between different services and ensuring
robust error handling throughout the process.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..services import (
    pubchem_service,
    conversion_service,
    calculation_service,
    database_service
)
from ..utils.config_manager import get_database_schema


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize an identifier to create a safe directory name.
    
    Args:
        identifier: The molecule identifier to sanitize
        
    Returns:
        A sanitized directory-safe string
    """
    # Replace unsafe characters and spaces
    sanitized = re.sub(r'[<>:"/\\|?*\s]', '_', identifier)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_.')
    # Ensure we have something left
    if not sanitized:
        sanitized = "unknown_molecule"
    return sanitized


def extract_smiles_from_sdf(sdf_path: str) -> Optional[str]:
    """
    Extract SMILES from an SDF file.
    
    This function reads an SDF file and attempts to extract the SMILES
    representation from the structure data.
    
    Args:
        sdf_path: Path to the SDF file
        
    Returns:
        SMILES string if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Use OpenBabel to convert SDF to SMILES
        from pathlib import Path
        sdf_file = Path(sdf_path)
        
        if not sdf_file.exists():
            logger.error(f"SDF file not found: {sdf_path}")
            return None
        
        # Create temporary SMILES file
        smiles_path = sdf_file.with_suffix('.smi')
        
        # Convert SDF to SMILES
        smiles_file = conversion_service.convert_file(sdf_path, 'smi')
        
        if not smiles_file:
            logger.warning(f"Could not convert SDF to SMILES: {sdf_path}")
            return None
        
        # Read SMILES from file
        with open(smiles_file, 'r', encoding='utf-8') as f:
            smiles_line = f.readline().strip()
            
        if smiles_line:
            # SMILES files typically have format: "SMILES molecule_name"
            smiles = smiles_line.split()[0]
            logger.debug(f"Extracted SMILES: {smiles}")
            return smiles
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting SMILES from SDF: {e}")
        return None


def process_single_molecule(identifier: str, config: Dict[str, Any]) -> bool:
    """
    Process a single molecule through the complete computational chemistry pipeline.
    
    This function orchestrates the complete workflow for a single molecule:
    1. Download structure from PubChem
    2. Convert formats as needed
    3. Run conformational search with CREST
    4. Run quantum chemistry calculations with MOPAC
    5. Extract and store results in database
    
    Args:
        identifier: Molecule identifier (name or SMILES)
        config: Configuration dictionary containing all settings
        
    Returns:
        True if processing completed successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Log start of processing
    logger.info(f"Starting pipeline processing for molecule: {identifier}")
    
    try:
        # Step 1: Prepare working directory
        sanitized_name = sanitize_identifier(identifier)
        repository_base = config.get('repository_base_path', 'repository')
        work_dir = Path(repository_base) / sanitized_name
        work_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created working directory: {work_dir}")
        
        # Step 2: Download initial structure (SDF) from PubChem
        logger.info("Step 1/8: Downloading structure from PubChem...")
        sdf_path = pubchem_service.download_sdf_by_name(
            identifier, 
            str(work_dir)
        )
        
        if not sdf_path:
            logger.error(f"Failed to download SDF structure for: {identifier}")
            return False
        
        logger.info(f"Downloaded SDF structure: {sdf_path}")
        
        # Step 3: Extract SMILES from SDF
        smiles = extract_smiles_from_sdf(sdf_path)
        if not smiles:
            logger.warning(f"Could not extract SMILES from SDF, using identifier: {identifier}")
            smiles = identifier
        
        # Step 4: Convert SDF to XYZ for CREST
        logger.info("Step 2/8: Converting SDF to XYZ format...")
        xyz_path = conversion_service.convert_file(sdf_path, "xyz")
        
        if not xyz_path:
            logger.error(f"Failed to convert SDF to XYZ for: {identifier}")
            return False
        
        logger.info(f"Converted to XYZ format: {xyz_path}")
        
        # Step 5: Run CREST conformational search
        logger.info("Step 3/8: Running CREST conformational search...")
        crest_output_dir = work_dir / "crest_output"
        crest_output_dir.mkdir(exist_ok=True)
        
        crest_keywords = config.get('crest_keywords', '--gfn2')
        crest_best_xyz = calculation_service.run_crest(
            xyz_path,
            str(crest_output_dir),
            crest_keywords
        )
        
        if not crest_best_xyz:
            logger.error(f"CREST conformational search failed for: {identifier}")
            return False
        
        logger.info(f"CREST completed successfully: {crest_best_xyz}")
        
        # Step 6: Convert best conformer to PDB for MOPAC
        logger.info("Step 4/8: Converting best conformer to PDB format...")
        pdb_path = conversion_service.convert_file(crest_best_xyz, "pdb")
        
        if not pdb_path:
            logger.error(f"Failed to convert best conformer to PDB for: {identifier}")
            return False
        
        logger.info(f"Converted best conformer to PDB: {pdb_path}")
        
        # Step 7: Run MOPAC energy calculation
        logger.info("Step 5/8: Running MOPAC energy calculation...")
        mopac_keywords = config.get('mopac_keywords', 'PM7 PRECISE XYZ')
        mopac_output = calculation_service.run_mopac(pdb_path, mopac_keywords)
        
        if not mopac_output:
            logger.error(f"MOPAC calculation failed for: {identifier}")
            return False
        
        logger.info(f"MOPAC calculation completed: {mopac_output}")
        
        # Step 8: Parse MOPAC output to extract energy
        logger.info("Step 6/8: Extracting energy from MOPAC output...")
        pm7_energy = calculation_service.parse_mopac_output(mopac_output)
        
        if pm7_energy is None:
            logger.error(f"Failed to extract energy from MOPAC output for: {identifier}")
            return False
        
        logger.info(f"Extracted PM7 energy: {pm7_energy} kcal/mol")
        
        # Step 9: Collect all results
        logger.info("Step 7/8: Collecting results...")
        molecule_data = {
            'smiles': smiles,
            'identifier': identifier,
            'sdf_path': str(Path(sdf_path).absolute()),
            'xyz_path': str(Path(xyz_path).absolute()),
            'crest_best_xyz_path': str(Path(crest_best_xyz).absolute()),
            'pm7_energy': pm7_energy,
            'charge': 0,  # Default charge
            'multiplicity': 1  # Default multiplicity
        }
        
        # Step 10: Save to database
        logger.info("Step 8/8: Saving results to database...")
        schema = get_database_schema()
        db_path = config['database']['pm7_db_path']
        
        success = database_service.append_to_database(
            molecule_data,
            db_path,
            schema
        )
        
        if not success:
            logger.error(f"Failed to save results to database for: {identifier}")
            return False
        
        # Log successful completion
        logger.info(f"Successfully completed pipeline processing for: {identifier}")
        logger.info(f"Final results - SMILES: {smiles}, Energy: {pm7_energy} kcal/mol")
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error processing molecule {identifier}: {e}")
        return False


def process_molecule_batch(
    identifiers: list[str], 
    config: Dict[str, Any],
    progress_callback: Optional[callable] = None
) -> tuple[int, int]:
    """
    Process a batch of molecules through the pipeline.
    
    Args:
        identifiers: List of molecule identifiers
        config: Configuration dictionary
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    logger = logging.getLogger(__name__)
    
    successful_count = 0
    failed_count = 0
    
    logger.info(f"Starting batch processing of {len(identifiers)} molecules")
    
    for i, identifier in enumerate(identifiers):
        if progress_callback:
            progress_callback(i, len(identifiers), identifier)
        
        try:
            success = process_single_molecule(identifier.strip(), config)
            
            if success:
                successful_count += 1
                logger.info(f"Batch progress: {identifier} - SUCCESS")
            else:
                failed_count += 1
                logger.warning(f"Batch progress: {identifier} - FAILED")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"Batch progress: {identifier} - ERROR: {e}")
    
    logger.info(f"Batch processing completed. Success: {successful_count}, Failed: {failed_count}")
    
    return successful_count, failed_count


def validate_pipeline_setup(config: Dict[str, Any]) -> bool:
    """
    Validate that the pipeline is properly configured and ready to run.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if pipeline is ready, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check if required directories exist or can be created
        # Note: Directories are now created by config_manager.py with absolute paths
        repository_base = config.get('repository_base_path', 'repository')
        logger.debug(f"Repository base path: {repository_base}")
        
        # Validate that the repository directory exists (should be created by config_manager)
        repository_path = Path(repository_base)
        if not repository_path.exists():
            repository_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created repository directory: {repository_base}")
        else:
            logger.debug(f"Repository directory exists: {repository_base}")
        
        # Validate executables
        from ..utils.config_manager import validate_executables
        if not validate_executables(config):
            logger.error("One or more required executables are not available")
            return False
        
        logger.info("Pipeline setup validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline setup validation failed: {e}")
        return False