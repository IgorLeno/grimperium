"""
Database service for persistent storage of molecular calculation results.

This module provides thread-safe and process-safe mechanisms for storing
molecular calculation results in CSV format. It uses file locking to prevent
race conditions and pandas for efficient data manipulation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd
from filelock import FileLock

from ..constants import DATABASE_LOCK_TIMEOUT


def get_existing_smiles(db_path: str) -> Set[str]:
    """
    Efficiently retrieve all existing SMILES from the database.

    This function reads only the 'smiles' column from the CSV database
    to quickly determine which molecules have already been processed.
    This is much more efficient than loading the entire DataFrame.

    Args:
        db_path: Path to the CSV database file

    Returns:
        Set of existing SMILES strings, empty set if file doesn't exist
        or on error

    Example:
        >>> existing = get_existing_smiles("data/thermo_pm7.csv")
        >>> "CCO" in existing
        True
    """
    logger = logging.getLogger(__name__)

    try:
        # Check if database file exists
        db_file = Path(db_path)
        if not db_file.exists():
            logger.debug(f"Database file does not exist: {db_path}")
            return set()

        if not db_file.is_file():
            logger.error(f"Database path is not a file: {db_path}")
            return set()

        # Check if file is empty
        if db_file.stat().st_size == 0:
            logger.debug(f"Database file is empty: {db_path}")
            return set()

        logger.debug(f"Reading existing SMILES from: {db_path}")

        # Read only the 'smiles' column for efficiency
        try:
            df = pd.read_csv(db_path, usecols=["smiles"], dtype=str)
        except ValueError as e:
            if "smiles" in str(e).lower():
                logger.warning(f"Column 'smiles' not found in database: {db_path}")
                return set()
            else:
                raise e

        # Handle empty DataFrame
        if df.empty:
            logger.debug(f"Database contains no data: {db_path}")
            return set()

        # Extract unique SMILES, removing any NaN values
        smiles_series = df["smiles"].dropna()
        existing_smiles = set(smiles_series.unique())

        logger.debug(f"Found {len(existing_smiles)} unique SMILES in database")
        return existing_smiles

    except pd.errors.EmptyDataError:
        logger.warning(f"Database file is empty or corrupted: {db_path}")
        return set()

    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV database {db_path}: {e}")
        return set()

    except Exception as e:
        logger.error(f"Unexpected error reading database {db_path}: {e}")
        return set()


def update_database_entry(
    molecule_data: Dict[str, any], db_path: str, schema: List[str]
) -> bool:
    """
    Update an existing entry in the database or create a new one.

    This function updates an existing molecule entry in the database
    based on the SMILES key, or creates a new entry if it doesn't exist.

    Args:
        molecule_data: Dictionary containing molecular data to update/insert
        db_path: Path to the CSV database file
        schema: List of column names defining the database schema/order

    Returns:
        True if data was successfully updated/inserted, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate input data
        if not isinstance(molecule_data, dict):
            logger.error("molecule_data must be a dictionary")
            return False

        if "smiles" not in molecule_data:
            logger.error("molecule_data must contain 'smiles' key")
            return False

        if not molecule_data["smiles"]:
            logger.error("SMILES cannot be empty or None")
            return False

        smiles = str(molecule_data["smiles"]).strip()
        if not smiles:
            logger.error("SMILES cannot be empty after stripping")
            return False

        # Validate schema
        if not isinstance(schema, list) or not schema:
            logger.error("Schema must be a non-empty list")
            return False

        if "smiles" not in schema:
            logger.error("Schema must include 'smiles' column")
            return False

        # Create database directory if needed
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Use file locking to prevent race conditions
        lock_path = f"{db_path}.lock"
        lock = FileLock(lock_path, timeout=DATABASE_LOCK_TIMEOUT)

        logger.debug(f"Attempting to acquire lock for database: {db_path}")

        try:
            with lock:
                logger.debug(f"Lock acquired for database: {db_path}")

                # Check if database file exists
                if db_file.exists() and db_file.stat().st_size > 0:
                    # File exists and has content - read and update
                    df = pd.read_csv(db_path)

                    # Check if SMILES already exists
                    existing_mask = df["smiles"] == smiles

                    if existing_mask.any():
                        # Update existing entry
                        logger.info(
                            f"Updating existing entry with SMILES '{smiles}' in database"
                        )
                        for col in schema:
                            if col in molecule_data:
                                df.loc[existing_mask, col] = molecule_data[col]
                    else:
                        # Add new entry
                        logger.info(
                            f"Adding new entry with SMILES '{smiles}' to database"
                        )
                        row_data = {}
                        for col in schema:
                            row_data[col] = molecule_data.get(col, None)

                        new_row_df = pd.DataFrame([row_data], columns=schema)
                        df = pd.concat([df, new_row_df], ignore_index=True)

                    # Write updated DataFrame
                    df.to_csv(
                        db_path, mode="w", header=True, index=False, encoding="utf-8"
                    )

                else:
                    # File doesn't exist or is empty - create new database
                    logger.info(f"Creating new database: {db_path}")

                    # Prepare data for new file
                    row_data = {}
                    for col in schema:
                        row_data[col] = molecule_data.get(col, None)

                    # Create DataFrame with proper schema
                    new_df = pd.DataFrame([row_data], columns=schema)

                    # Write new file with header
                    new_df.to_csv(
                        db_path,
                        mode="w",  # write mode
                        header=True,  # include header
                        index=False,  # don't write index
                        encoding="utf-8",
                    )

                logger.info(f"Successfully saved molecular data to database: {db_path}")
                return True

        except Exception as e:
            logger.error(f"Error while holding database lock: {e}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error updating database: {e}")
        return False


def append_to_database(
    molecule_data: Dict[str, any], db_path: str, schema: List[str]
) -> bool:
    """
    Thread-safe append of molecular data to CSV database.

    This function safely appends a new molecular calculation result to the
    CSV database. It uses file locking to prevent race conditions when
    multiple processes try to write simultaneously. The function checks
    for duplicate SMILES before writing to avoid data duplication.

    Args:
        molecule_data: Dictionary containing molecular data to append
                      Must include 'smiles' key for duplicate checking
        db_path: Path to the CSV database file
        schema: List of column names defining the database schema/order

    Returns:
        True if data was successfully appended, False otherwise

    Example:
        >>> data = {
        ...     'smiles': 'CCO',
        ...     'identifier': 'ethanol',
        ...     'pm7_energy': -74.326,
        ...     'charge': 0,
        ...     'multiplicity': 1
        ... }
        >>> schema = ['smiles', 'identifier', 'pm7_energy', 'charge', 'multiplicity']
        >>> append_to_database(data, "data/thermo_pm7.csv", schema)
        True
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate input data
        if not isinstance(molecule_data, dict):
            logger.error("molecule_data must be a dictionary")
            return False

        if "smiles" not in molecule_data:
            logger.error("molecule_data must contain 'smiles' key")
            return False

        if not molecule_data["smiles"]:
            logger.error("SMILES cannot be empty or None")
            return False

        smiles = str(molecule_data["smiles"]).strip()
        if not smiles:
            logger.error("SMILES cannot be empty after stripping")
            return False

        # Validate schema
        if not isinstance(schema, list) or not schema:
            logger.error("Schema must be a non-empty list")
            return False

        if "smiles" not in schema:
            logger.error("Schema must include 'smiles' column")
            return False

        # Create database directory if needed
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Use file locking to prevent race conditions
        lock_path = f"{db_path}.lock"
        lock = FileLock(lock_path, timeout=DATABASE_LOCK_TIMEOUT)

        logger.debug(f"Attempting to acquire lock for database: {db_path}")

        try:
            with lock:
                logger.debug(f"Lock acquired for database: {db_path}")

                # Check if database file exists
                if db_file.exists():
                    # File exists - check for duplicates and append
                    existing_smiles = get_existing_smiles(db_path)

                    if smiles in existing_smiles:
                        logger.warning(
                            f"SMILES '{smiles}' already exists in database, skipping"
                        )
                        return False

                    # Prepare data for append
                    # Ensure all schema columns are present, fill missing with None
                    row_data = {}
                    for col in schema:
                        row_data[col] = molecule_data.get(col, None)

                    # Create DataFrame with single row
                    new_row_df = pd.DataFrame([row_data], columns=schema)

                    # Append to existing file
                    logger.info(
                        f"Appending new entry with SMILES '{smiles}' to database"
                    )
                    new_row_df.to_csv(
                        db_path,
                        mode="a",  # append mode
                        header=False,  # don't write header again
                        index=False,  # don't write index
                        encoding="utf-8",
                    )

                else:
                    # File doesn't exist - create new database
                    logger.info(f"Creating new database: {db_path}")

                    # Prepare data for new file
                    row_data = {}
                    for col in schema:
                        row_data[col] = molecule_data.get(col, None)

                    # Create DataFrame with proper schema
                    new_df = pd.DataFrame([row_data], columns=schema)

                    # Write new file with header
                    new_df.to_csv(
                        db_path,
                        mode="w",  # write mode
                        header=True,  # include header
                        index=False,  # don't write index
                        encoding="utf-8",
                    )

                logger.info(f"Successfully saved molecular data to database: {db_path}")
                return True

        except Exception as e:
            logger.error(f"Error while holding database lock: {e}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error appending to database: {e}")
        return False


def validate_database_schema(db_path: str, expected_schema: List[str]) -> bool:
    """
    Validate that an existing database matches the expected schema.

    This function checks if the columns in an existing CSV database
    match the expected schema. Useful for schema validation and migration
    detection.

    Args:
        db_path: Path to the CSV database file
        expected_schema: List of expected column names

    Returns:
        True if schema matches or file doesn't exist, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        db_file = Path(db_path)
        if not db_file.exists():
            logger.debug(
                f"Database file does not exist, schema validation passed: {db_path}"
            )
            return True

        # Read just the header to check columns
        df = pd.read_csv(db_path, nrows=0)  # Read no rows, just header
        existing_columns = list(df.columns)

        if existing_columns != expected_schema:
            logger.error(
                f"Database schema mismatch in {db_path}. "
                f"Expected: {expected_schema}, Found: {existing_columns}"
            )
            return False

        logger.debug(f"Database schema validation passed: {db_path}")
        return True

    except Exception as e:
        logger.error(f"Error validating database schema: {e}")
        return False


def get_database_stats(db_path: str) -> Dict[str, any]:
    """
    Get statistics about the database contents.

    Args:
        db_path: Path to the CSV database file

    Returns:
        Dictionary with database statistics
    """
    logger = logging.getLogger(__name__)

    try:
        db_file = Path(db_path)
        if not db_file.exists():
            return {
                "exists": False,
                "total_entries": 0,
                "unique_smiles": 0,
                "file_size_bytes": 0,
            }

        # Get file size
        file_size = db_file.stat().st_size

        if file_size == 0:
            return {
                "exists": True,
                "total_entries": 0,
                "unique_smiles": 0,
                "file_size_bytes": 0,
            }

        # Read database
        df = pd.read_csv(db_path)

        # Calculate statistics
        stats = {
            "exists": True,
            "total_entries": len(df),
            "unique_smiles": df["smiles"].nunique() if "smiles" in df.columns else 0,
            "file_size_bytes": file_size,
            "columns": list(df.columns),
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return {"exists": False, "error": str(e)}
