"""
Default configuration values for the Grimperium application.

This module provides default configurations, required sections,
and validation schemas for the application configuration.
"""

from typing import Dict, List, Any
from pathlib import Path

# Required configuration sections
REQUIRED_CONFIG_SECTIONS = [
    "executables",
    "database",
    "repository_base_path",
    "general_settings",
]

# Required executable keys
REQUIRED_EXECUTABLES = {
    "crest": "Conformational search program",
    "mopac": "Quantum chemistry calculation program",
    "obabel": "Chemical file format conversion program",
}

# Required database keys
REQUIRED_DATABASE_KEYS = ["cbs_db_path", "pm7_db_path"]

# Default configuration template
DEFAULT_CONFIG = {
    "executables": {"crest": "crest", "mopac": "mopac", "obabel": "obabel"},
    "crest_keywords": "--gfn2",
    "mopac_keywords": "PM7 PRECISE XYZ",
    "repository_base_path": "repository",
    "general_settings": {"verbose": False, "lists_directory": "data/lists"},
    "database": {
        "cbs_db_path": "data/thermo_cbs.csv",
        "pm7_db_path": "data/thermo_pm7.csv",
    },
}

# Database schema definition
DATABASE_SCHEMA = [
    "smiles",
    "identifier",
    "sdf_path",
    "xyz_path",
    "crest_best_xyz_path",
    "pm7_energy",
    "charge",
    "multiplicity",
]

# Configuration validation rules
CONFIG_VALIDATION_RULES = {
    "executables": {"type": dict, "required": True, "keys": REQUIRED_EXECUTABLES},
    "database": {"type": dict, "required": True, "keys": REQUIRED_DATABASE_KEYS},
    "repository_base_path": {"type": str, "required": True},
    "general_settings": {
        "type": dict,
        "required": True,
        "keys": ["verbose", "lists_directory"],
    },
    "crest_keywords": {"type": str, "required": False, "default": "--gfn2"},
    "mopac_keywords": {"type": str, "required": False, "default": "PM7 PRECISE XYZ"},
}


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration dictionary.

    Returns:
        Default configuration with all required sections
    """
    return DEFAULT_CONFIG.copy()


def get_required_sections() -> List[str]:
    """
    Get the list of required configuration sections.

    Returns:
        List of required section names
    """
    return REQUIRED_CONFIG_SECTIONS.copy()


def get_database_schema() -> List[str]:
    """
    Get the database schema definition.

    Returns:
        List of database column names in order
    """
    return DATABASE_SCHEMA.copy()


def validate_config_structure(config: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of a configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check required sections
    for section in REQUIRED_CONFIG_SECTIONS:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    # Validate executables section
    if "executables" in config:
        if not isinstance(config["executables"], dict):
            errors.append("'executables' must be a dictionary")
        else:
            for exe_name in REQUIRED_EXECUTABLES:
                if exe_name not in config["executables"]:
                    errors.append(f"Missing required executable: {exe_name}")

    # Validate database section
    if "database" in config:
        if not isinstance(config["database"], dict):
            errors.append("'database' must be a dictionary")
        else:
            for db_key in REQUIRED_DATABASE_KEYS:
                if db_key not in config["database"]:
                    errors.append(f"Missing required database key: {db_key}")

    # Validate repository_base_path
    if "repository_base_path" in config:
        if not isinstance(config["repository_base_path"], str):
            errors.append("'repository_base_path' must be a string")

    # Validate general_settings section
    if "general_settings" in config:
        if not isinstance(config["general_settings"], dict):
            errors.append("'general_settings' must be a dictionary")
        else:
            if "verbose" not in config["general_settings"]:
                errors.append("Missing required general_settings key: verbose")
            elif not isinstance(config["general_settings"]["verbose"], bool):
                errors.append("'general_settings.verbose' must be a boolean")

            if "lists_directory" not in config["general_settings"]:
                errors.append("Missing required general_settings key: lists_directory")
            elif not isinstance(config["general_settings"]["lists_directory"], str):
                errors.append("'general_settings.lists_directory' must be a string")

    return errors
