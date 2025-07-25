"""
Pipeline orchestration service for Grimperium computational chemistry
workflows.

This module coordinates the execution of the complete computational chemistry
pipeline, managing the flow of data between different services and ensuring
robust error handling throughout the process.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..constants import (
    FILENAME_SANITIZATION_PATTERN,
    MULTIPLE_UNDERSCORES_PATTERN,
    DEFAULT_CHARGE,
    DEFAULT_MULTIPLICITY,
)

from ..services import (
    pubchem_service,
    conversion_service,
    calculation_service,
    database_service,
)
from ..config.defaults import get_database_schema
from ..utils.file_utils import ensure_directory_exists


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize an identifier to create a safe directory name.

    Args:
        identifier: The molecule identifier to sanitize

    Returns:
        A sanitized directory-safe string
    """
    # Replace unsafe characters and spaces
    sanitized = re.sub(FILENAME_SANITIZATION_PATTERN, "_", identifier)
    # Remove multiple underscores
    sanitized = re.sub(MULTIPLE_UNDERSCORES_PATTERN, "_", sanitized)
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip("_.")
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

        # Convert SDF to SMILES
        smiles_file = conversion_service.convert_file(sdf_path, "smi")

        if not smiles_file:
            logger.warning(f"Could not convert SDF to SMILES: {sdf_path}")
            return None

        # Read SMILES from file
        with open(smiles_file, "r", encoding="utf-8") as f:
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


def _prepare_working_directory(
    identifier: str, config: Dict[str, Any]
) -> Optional[Path]:
    """
    Prepare the working directory for molecule processing.

    Args:
        identifier: Molecule identifier
        config: Configuration dictionary

    Returns:
        Path to working directory or None if creation failed
    """
    logger = logging.getLogger(__name__)

    try:
        sanitized_name = sanitize_identifier(identifier)
        repository_base = config.get("repository_base_path", "repository")
        work_dir = Path(repository_base) / sanitized_name

        if ensure_directory_exists(str(work_dir)):
            logger.info(f"Prepared working directory: {work_dir}")
            return work_dir
        else:
            logger.error(f"Failed to create working directory: {work_dir}")
            return None

    except Exception as e:
        logger.error(f"Error preparing working directory: {e}")
        return None


def _download_structure(identifier: str, work_dir: Path) -> Optional[str]:
    """
    Download molecular structure from PubChem.

    Args:
        identifier: Molecule identifier (name or SMILES)
        work_dir: Working directory for output

    Returns:
        Path to downloaded SDF file or None if failed
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Step 1/8: Downloading structure from PubChem...")
        sdf_path = pubchem_service.download_sdf_by_name(identifier, str(work_dir))

        if sdf_path:
            logger.info(f"Downloaded SDF structure: {sdf_path}")
            return sdf_path
        else:
            logger.error(f"Failed to download SDF structure for: {identifier}")
            return None

    except Exception as e:
        logger.error(f"Error downloading structure: {e}")
        return None


def _prepare_molecule_data(
    identifier: str,
    sdf_path: str,
    xyz_path: str,
    crest_best_xyz: str,
    pm7_energy: float,
) -> Dict[str, Any]:
    """
    Prepare molecule data dictionary for database storage.

    Args:
        identifier: Molecule identifier
        sdf_path: Path to SDF file
        xyz_path: Path to XYZ file
        crest_best_xyz: Path to best CREST conformer
        pm7_energy: Calculated PM7 energy

    Returns:
        Dictionary with molecule data ready for database storage
    """
    logger = logging.getLogger(__name__)

    # Extract SMILES from SDF
    smiles = extract_smiles_from_sdf(sdf_path)
    if not smiles:
        logger.warning(
            f"Could not extract SMILES from SDF, using identifier: " f"{identifier}"
        )
        smiles = identifier

    # Prepare molecule data
    molecule_data = {
        "smiles": smiles,
        "identifier": identifier,
        "sdf_path": str(Path(sdf_path).absolute()),
        "xyz_path": str(Path(xyz_path).absolute()),
        "crest_best_xyz_path": str(Path(crest_best_xyz).absolute()),
        "pm7_energy": pm7_energy,
        "charge": DEFAULT_CHARGE,
        "multiplicity": DEFAULT_MULTIPLICITY,
    }

    logger.info("Step 7/8: Collected molecule data")
    logger.info(f"Final results - SMILES: {smiles}, Energy: {pm7_energy} kcal/mol")

    return molecule_data


def _prepare_molecule_data_with_smiles(
    identifier: str,
    sdf_path: str,
    xyz_path: str,
    crest_best_xyz: str,
    pm7_energy: float,
    smiles: str,
) -> Dict[str, Any]:
    """
    Prepare molecule data dictionary for database storage with
    pre-extracted SMILES.

    Args:
        identifier: Molecule identifier
        sdf_path: Path to SDF file
        xyz_path: Path to XYZ file
        crest_best_xyz: Path to best CREST conformer
        pm7_energy: Calculated PM7 energy
        smiles: Pre-extracted SMILES string

    Returns:
        Dictionary with molecule data ready for database storage
    """
    logger = logging.getLogger(__name__)

    # Prepare molecule data
    molecule_data = {
        "smiles": smiles,
        "identifier": identifier,
        "sdf_path": str(Path(sdf_path).absolute()),
        "xyz_path": str(Path(xyz_path).absolute()),
        "crest_best_xyz_path": str(Path(crest_best_xyz).absolute()),
        "pm7_energy": pm7_energy,
        "charge": DEFAULT_CHARGE,
        "multiplicity": DEFAULT_MULTIPLICITY,
    }

    logger.info("Step 8/8: Collected molecule data")
    logger.info(f"Final results - SMILES: {smiles}, Energy: {pm7_energy} kcal/mol")

    return molecule_data


def _save_to_database(molecule_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Save molecule data to the database.

    Args:
        molecule_data: Molecule data dictionary
        config: Configuration dictionary

    Returns:
        True if save was successful
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Step 8/8: Saving results to database...")
        schema = get_database_schema()
        db_path = config["database"]["pm7_db_path"]

        success = database_service.append_to_database(molecule_data, db_path, schema)

        if success:
            logger.info("Successfully saved results to database")
            return True
        else:
            logger.error("Failed to save results to database")
            return False

    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False


def _save_to_database_with_overwrite(
    molecule_data: Dict[str, Any],
    config: Dict[str, Any],
    overwrite: bool = False,
) -> bool:
    """
    Save molecule data to the database with overwrite option.

    Args:
        molecule_data: Molecule data dictionary
        config: Configuration dictionary
        overwrite: If True, use update function to overwrite existing entries

    Returns:
        True if save was successful
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Step 8/8: Saving results to database...")
        schema = get_database_schema()
        db_path = config["database"]["pm7_db_path"]

        if overwrite:
            success = database_service.update_database_entry(
                molecule_data, db_path, schema
            )
        else:
            success = database_service.append_to_database(
                molecule_data, db_path, schema
            )

        if success:
            logger.info("Successfully saved results to database")
            return True
        else:
            logger.error("Failed to save results to database")
            return False

    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False


def get_molecule_smiles(identifier: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Get SMILES string for a molecule by downloading and extracting from
    PubChem.

    This function handles the initial steps of the pipeline without the
    heavy calculations:
    1. Download structure from PubChem
    2. Extract SMILES from the structure

    Args:
        identifier: Molecule identifier (name or SMILES)
        config: Configuration dictionary containing all settings

    Returns:
        SMILES string if successful, None otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting SMILES for molecule: {identifier}")

    try:
        # Step 1: Prepare working directory
        work_dir = _prepare_working_directory(identifier, config)
        if not work_dir:
            return None

        # Step 2: Download molecular structure
        sdf_path = _download_structure(identifier, work_dir)
        if not sdf_path:
            return None

        # Step 3: Extract SMILES
        smiles = extract_smiles_from_sdf(sdf_path)
        if not smiles:
            logger.warning(
                f"Could not extract SMILES from SDF, using identifier: " f"{identifier}"
            )
            smiles = identifier

        logger.info(f"Successfully extracted SMILES: {smiles}")
        return smiles

    except Exception as e:
        logger.error(f"Error getting SMILES for molecule {identifier}: {e}")
        return None


def process_single_molecule(
    identifier: str, config: Dict[str, Any], overwrite: bool = False
) -> bool:
    """
    Process a single molecule through the complete computational chemistry
    pipeline.

    This function orchestrates the complete workflow for a single molecule:
    1. Download structure from PubChem (if not already done)
    2. Extract SMILES
    3. Convert formats as needed
    4. Run conformational search with CREST
    5. Run quantum chemistry calculations with MOPAC
    6. Extract and store results in database

    Args:
        identifier: Molecule identifier (name or SMILES)
        config: Configuration dictionary containing all settings
        overwrite: Whether to overwrite existing database entries

    Returns:
        True if processing completed successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting pipeline processing for molecule: {identifier}")

    try:
        # Step 1: Prepare working directory
        work_dir = _prepare_working_directory(identifier, config)
        if not work_dir:
            return False

        # Step 2: Download molecular structure
        sdf_path = _download_structure(identifier, work_dir)
        if not sdf_path:
            return False

        # Step 3: Extract SMILES
        logger.info("Step 2/8: Extracting SMILES...")
        smiles = extract_smiles_from_sdf(sdf_path)
        if not smiles:
            logger.warning(
                f"Could not extract SMILES from SDF, using identifier: " f"{identifier}"
            )
            smiles = identifier

        # Step 4: Convert SDF to XYZ for CREST
        logger.info("Step 3/8: Converting SDF to XYZ format...")
        xyz_path = conversion_service.convert_file(sdf_path, "xyz")

        if not xyz_path:
            logger.error(f"Failed to convert SDF to XYZ for: {identifier}")
            return False

        logger.info(f"Converted to XYZ format: {xyz_path}")

        # Step 5: Run CREST conformational search
        logger.info("Step 4/8: Running CREST conformational search...")
        crest_output_dir = work_dir / "crest_output"
        crest_output_dir.mkdir(exist_ok=True)

        crest_keywords = config.get("crest_keywords", "--gfn2")
        crest_best_xyz = calculation_service.run_crest(
            xyz_path, str(crest_output_dir), crest_keywords
        )

        if not crest_best_xyz:
            logger.error(f"CREST conformational search failed for: {identifier}")
            return False

        logger.info(f"CREST completed successfully: {crest_best_xyz}")

        # Step 6: Convert best conformer to PDB for MOPAC
        logger.info("Step 5/8: Converting best conformer to PDB format...")
        pdb_path = conversion_service.convert_file(crest_best_xyz, "pdb")

        if not pdb_path:
            logger.error(f"Failed to convert best conformer to PDB for: {identifier}")
            return False

        logger.info(f"Converted best conformer to PDB: {pdb_path}")

        # Step 7: Run MOPAC energy calculation
        logger.info("Step 6/8: Running MOPAC energy calculation...")
        mopac_keywords = config.get("mopac_keywords", "PM7 PRECISE XYZ")
        mopac_output = calculation_service.run_mopac(pdb_path, mopac_keywords)

        if not mopac_output:
            logger.error(f"MOPAC calculation failed for: {identifier}")
            return False

        logger.info(f"MOPAC calculation completed: {mopac_output}")

        # Step 8: Parse MOPAC output to extract energy
        logger.info("Step 7/8: Extracting energy from MOPAC output...")
        pm7_energy = calculation_service.parse_mopac_output(mopac_output)

        if pm7_energy is None:
            logger.error(
                f"Failed to extract energy from MOPAC output for: {identifier}"
            )
            return False

        logger.info(f"Extracted PM7 energy: {pm7_energy} kcal/mol")

        # Step 9: Prepare molecule data - use extracted SMILES
        molecule_data = _prepare_molecule_data_with_smiles(
            identifier, sdf_path, xyz_path, crest_best_xyz, pm7_energy, smiles
        )

        # Step 10: Save to database (with overwrite if specified)
        if not _save_to_database_with_overwrite(molecule_data, config, overwrite):
            return False

        logger.info(f"Successfully completed pipeline processing for: {identifier}")
        return True

    except Exception as e:
        logger.error(f"Unexpected error processing molecule {identifier}: {e}")
        return False


def process_molecule_batch(
    identifiers: list[str],
    config: Dict[str, Any],
    progress_callback: Optional[callable] = None,
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

    logger.info(
        f"Batch processing completed. Success: {successful_count}, "
        f"Failed: {failed_count}"
    )

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
        # Note: Directories are now created by config_manager.py with
        # absolute paths
        repository_base = config.get("repository_base_path", "repository")
        logger.debug(f"Repository base path: {repository_base}")

        # Validate that the repository directory exists (should be created by
        # config_manager)
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
