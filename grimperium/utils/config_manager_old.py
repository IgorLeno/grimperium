"""
Configuration management utilities for Grimperium.

This module provides functionality to load and validate configuration
from YAML files, ensuring all required settings are present and valid.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ..constants import (
    EXECUTABLE_VALIDATION_TIMEOUT,
    BYTES_PER_MB,
    REQUIRED_EXECUTABLES,
)
from ..config.defaults import get_database_schema, validate_config_structure


def load_config(config_path: str, project_root: Path) -> Optional[Dict[str, Any]]:
    """
    Load configuration from a YAML file and resolve relative paths to absolute paths.

    This function loads the Grimperium configuration from a YAML file,
    validates required sections, and converts relative paths to absolute paths
    based on the project root directory.

    Args:
        config_path: Path to the configuration YAML file
        project_root: Path object representing the project root directory

    Returns:
        Dictionary containing configuration settings with resolved absolute paths,
        None if loading fails

    Example:
        >>> from pathlib import Path
        >>> project_root = Path("/home/user/grimperium")
        >>> config = load_config("config.yaml", project_root)
        >>> print(config['database']['pm7_db_path'])
        '/home/user/grimperium/data/thermo_pm7.csv'
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate config file exists
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        if not config_file.is_file():
            logger.error(f"Configuration path is not a file: {config_path}")
            return None

        # Load YAML configuration
        logger.info(f"Loading configuration from: {config_path}")
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            logger.error("Configuration file must contain a YAML dictionary")
            return None

        # Validate required sections
        required_sections = ["executables", "logging", "database"]
        for section in required_sections:
            if section not in config:
                logger.error(f"Required configuration section missing: {section}")
                return None

        # Validate executables section
        required_executables = ["crest", "mopac", "obabel"]
        if "executables" in config:
            for exe in required_executables:
                if exe not in config["executables"]:
                    logger.error(f"Required executable missing from config: {exe}")
                    return None

        # Validate logging section
        if "logging" in config:
            required_log_keys = ["log_file", "console_level", "file_level"]
            for key in required_log_keys:
                if key not in config["logging"]:
                    logger.error(f"Required logging configuration missing: {key}")
                    return None

        # Validate database section
        if "database" in config:
            required_db_keys = ["cbs_db_path", "pm7_db_path"]
            for key in required_db_keys:
                if key not in config["database"]:
                    logger.error(f"Required database configuration missing: {key}")
                    return None

        # Set default values for optional settings
        config.setdefault("mopac_keywords", "PM7 PRECISE XYZ")
        config.setdefault("crest_keywords", "--gfn2")
        config.setdefault("repository_base_path", "repository")

        # Resolve relative paths to absolute paths based on project root
        logger.debug(f"Resolving paths relative to project root: {project_root}")

        # Resolve database paths
        if "database" in config:
            for key in ["cbs_db_path", "pm7_db_path"]:
                if key in config["database"]:
                    relative_path = config["database"][key]
                    absolute_path = project_root / relative_path
                    config["database"][key] = str(absolute_path)
                    logger.debug(f"Resolved {key}: {relative_path} -> {absolute_path}")

        # Resolve logging paths
        if "logging" in config and "log_file" in config["logging"]:
            relative_path = config["logging"]["log_file"]
            absolute_path = project_root / relative_path
            config["logging"]["log_file"] = str(absolute_path)
            logger.debug(f"Resolved log_file: {relative_path} -> {absolute_path}")

        # Resolve repository base path
        if "repository_base_path" in config:
            relative_path = config["repository_base_path"]
            absolute_path = project_root / relative_path
            config["repository_base_path"] = str(absolute_path)
            logger.debug(
                f"Resolved repository_base_path: {relative_path} -> {absolute_path}"
            )

        # Ensure required directories exist
        logger.debug("Creating required directories if they don't exist")
        required_dirs = []

        if "database" in config:
            for key in ["cbs_db_path", "pm7_db_path"]:
                if key in config["database"]:
                    db_dir = Path(config["database"][key]).parent
                    required_dirs.append(db_dir)

        if "logging" in config and "log_file" in config["logging"]:
            log_dir = Path(config["logging"]["log_file"]).parent
            required_dirs.append(log_dir)

        if "repository_base_path" in config:
            repository_dir = Path(config["repository_base_path"])
            required_dirs.append(repository_dir)

        # Create directories
        for dir_path in required_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {dir_path}")
            except Exception as e:
                logger.warning(f"Could not create directory {dir_path}: {e}")

        logger.info("Configuration loaded, validated, and paths resolved successfully")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return None


def get_database_schema() -> list[str]:
    """
    Get the standard database schema for molecular calculation results.

    This function returns the ordered list of column names that should
    be used for all database operations, ensuring consistency across
    the application.

    Returns:
        List of column names in the correct order
    """
    return [
        "smiles",
        "identifier",
        "sdf_path",
        "xyz_path",
        "crest_best_xyz_path",
        "pm7_energy",
        "charge",
        "multiplicity",
    ]


def validate_executables(config: Dict[str, Any]) -> bool:
    """
    Validate that required executables are available in the system.

    This function checks if the computational chemistry executables
    specified in the configuration are actually available and executable.

    Args:
        config: Configuration dictionary

    Returns:
        True if all executables are available, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        import subprocess

        executables = config.get("executables", {})

        for name, executable in executables.items():
            try:
                # Try to run the executable with a help or version flag
                if name == "crest":
                    result = subprocess.run(
                        [executable, "--help"],
                        capture_output=True,
                        timeout=EXECUTABLE_VALIDATION_TIMEOUT,
                    )
                elif name == "mopac":
                    result = subprocess.run(
                        [executable],
                        capture_output=True,
                        timeout=EXECUTABLE_VALIDATION_TIMEOUT,
                    )
                elif name == "obabel":
                    result = subprocess.run(
                        [executable, "--help"],
                        capture_output=True,
                        timeout=EXECUTABLE_VALIDATION_TIMEOUT,
                    )
                else:
                    # Generic executable check
                    result = subprocess.run(
                        [executable, "--help"],
                        capture_output=True,
                        timeout=EXECUTABLE_VALIDATION_TIMEOUT,
                    )

                logger.debug(f"Executable '{name}' ({executable}) is available")

            except FileNotFoundError:
                logger.error(f"Executable '{name}' not found: {executable}")
                return False
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Executable '{name}' timed out, but appears to be available"
                )
            except Exception as e:
                logger.warning(f"Could not verify executable '{name}': {e}")

        logger.info("All required executables are available")
        return True

    except Exception as e:
        logger.error(f"Error validating executables: {e}")
        return False
