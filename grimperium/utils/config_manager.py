"""
Configuration management utilities for Grimperium.

This module provides functionality to load and validate configuration
from YAML files, ensuring all required settings are present and valid.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration from a YAML file.
    
    This function loads the Grimperium configuration from a YAML file,
    validates required sections, and returns a dictionary with all
    configuration settings.
    
    Args:
        config_path: Path to the configuration YAML file
        
    Returns:
        Dictionary containing configuration settings, None if loading fails
        
    Example:
        >>> config = load_config("config.yaml")
        >>> print(config['executables']['crest'])
        'crest'
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
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if not isinstance(config, dict):
            logger.error("Configuration file must contain a YAML dictionary")
            return None
        
        # Validate required sections
        required_sections = ['executables', 'logging', 'database']
        for section in required_sections:
            if section not in config:
                logger.error(f"Required configuration section missing: {section}")
                return None
        
        # Validate executables section
        required_executables = ['crest', 'mopac', 'obabel']
        if 'executables' in config:
            for exe in required_executables:
                if exe not in config['executables']:
                    logger.error(f"Required executable missing from config: {exe}")
                    return None
        
        # Validate logging section
        if 'logging' in config:
            required_log_keys = ['log_file', 'console_level', 'file_level']
            for key in required_log_keys:
                if key not in config['logging']:
                    logger.error(f"Required logging configuration missing: {key}")
                    return None
        
        # Validate database section
        if 'database' in config:
            required_db_keys = ['cbs_db_path', 'pm7_db_path']
            for key in required_db_keys:
                if key not in config['database']:
                    logger.error(f"Required database configuration missing: {key}")
                    return None
        
        # Set default values for optional settings
        config.setdefault('mopac_keywords', 'PM7 PRECISE XYZ')
        config.setdefault('crest_keywords', '--gfn2')
        
        logger.info("Configuration loaded and validated successfully")
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
        'smiles',
        'identifier', 
        'sdf_path',
        'xyz_path',
        'crest_best_xyz_path',
        'pm7_energy',
        'charge',
        'multiplicity'
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
        
        executables = config.get('executables', {})
        
        for name, executable in executables.items():
            try:
                # Try to run the executable with a help or version flag
                if name == 'crest':
                    result = subprocess.run(
                        [executable, '--help'], 
                        capture_output=True, 
                        timeout=10
                    )
                elif name == 'mopac':
                    result = subprocess.run(
                        [executable], 
                        capture_output=True, 
                        timeout=10
                    )
                elif name == 'obabel':
                    result = subprocess.run(
                        [executable, '--help'], 
                        capture_output=True, 
                        timeout=10
                    )
                else:
                    # Generic executable check
                    result = subprocess.run(
                        [executable, '--help'], 
                        capture_output=True, 
                        timeout=10
                    )
                
                logger.debug(f"Executable '{name}' ({executable}) is available")
                
            except FileNotFoundError:
                logger.error(f"Executable '{name}' not found: {executable}")
                return False
            except subprocess.TimeoutExpired:
                logger.warning(f"Executable '{name}' timed out, but appears to be available")
            except Exception as e:
                logger.warning(f"Could not verify executable '{name}': {e}")
        
        logger.info("All required executables are available")
        return True
        
    except Exception as e:
        logger.error(f"Error validating executables: {e}")
        return False