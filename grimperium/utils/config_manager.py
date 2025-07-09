"""
Configuration management utilities for Grimperium.

This module provides functionality to load and validate configuration
from YAML files, ensuring all required settings are present and valid.
Refactored version with smaller, focused functions.
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
    REQUIRED_EXECUTABLES
)
from ..config.defaults import (
    get_database_schema,
    validate_config_structure
)


def _load_yaml_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load and parse a YAML configuration file.
    
    Args:
        config_path: Path to the configuration YAML file
        
    Returns:
        Dictionary from YAML file, None if loading fails
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
            
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration file: {e}")
        return None


def _validate_config_sections(config: Dict[str, Any]) -> bool:
    """
    Validate that all required configuration sections are present.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if all required sections are present
    """
    logger = logging.getLogger(__name__)
    
    # Use the validation function from defaults
    errors = validate_config_structure(config)
    
    if errors:
        for error in errors:
            logger.error(f"Configuration validation error: {error}")
        return False
    
    return True


def _resolve_config_paths(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """
    Resolve relative paths in configuration to absolute paths.
    
    Args:
        config: Configuration dictionary
        project_root: Project root directory for path resolution
        
    Returns:
        Configuration with resolved absolute paths
    """
    logger = logging.getLogger(__name__)
    
    # Create a copy to avoid modifying the original
    resolved_config = config.copy()
    
    # Resolve repository base path
    if 'repository_base_path' in resolved_config:
        repo_path = Path(resolved_config['repository_base_path'])
        if not repo_path.is_absolute():
            repo_path = project_root / repo_path
        resolved_config['repository_base_path'] = str(repo_path.absolute())
        logger.debug(f"Resolved repository_base_path: {resolved_config['repository_base_path']}")
    
    # Resolve database paths
    if 'database' in resolved_config:
        db_config = resolved_config['database'].copy()
        
        for db_key in ['cbs_db_path', 'pm7_db_path']:
            if db_key in db_config:
                db_path = Path(db_config[db_key])
                if not db_path.is_absolute():
                    db_path = project_root / db_path
                db_config[db_key] = str(db_path.absolute())
                logger.debug(f"Resolved {db_key}: {db_config[db_key]}")
        
        resolved_config['database'] = db_config
    
    return resolved_config


def _create_required_directories(config: Dict[str, Any]) -> bool:
    """
    Create directories required by the configuration.
    
    Args:
        config: Configuration dictionary with resolved paths
        
    Returns:
        True if all directories were created successfully
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create repository base directory
        if 'repository_base_path' in config:
            repo_path = Path(config['repository_base_path'])
            repo_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created repository directory: {repo_path}")
        
        # Create database directories
        if 'database' in config:
            db_config = config['database']
            for db_key in ['cbs_db_path', 'pm7_db_path']:
                if db_key in db_config:
                    db_path = Path(db_config[db_key])
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created database directory: {db_path.parent}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating required directories: {e}")
        return False


def load_config(config_path: str, project_root: Path) -> Optional[Dict[str, Any]]:
    """
    Load configuration from a YAML file and resolve relative paths to absolute paths.
    
    This function orchestrates the complete configuration loading process:
    1. Load and parse YAML file
    2. Validate required sections
    3. Resolve relative paths to absolute paths
    4. Create required directories
    
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
    
    # Step 1: Load YAML configuration
    config = _load_yaml_config(config_path)
    if config is None:
        return None
    
    # Step 2: Validate configuration structure
    if not _validate_config_sections(config):
        return None
    
    # Step 3: Resolve relative paths to absolute paths
    resolved_config = _resolve_config_paths(config, project_root)
    
    # Step 4: Create required directories
    if not _create_required_directories(resolved_config):
        logger.warning("Some directories could not be created")
    
    logger.info("Configuration loaded and validated successfully")
    return resolved_config


def _validate_single_executable(name: str, executable: str) -> bool:
    """
    Validate a single executable.
    
    Args:
        name: Name of the executable (crest, mopac, obabel)
        executable: Path or command for the executable
        
    Returns:
        True if executable is available and working
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Choose appropriate validation command based on executable
        if name == 'crest':
            command = [executable, '--help']
        elif name == 'mopac':
            command = [executable, '--help']
        elif name == 'obabel':
            command = [executable, '-V']
        else:
            logger.warning(f"Unknown executable type: {name}")
            return False
        
        # Try to run the command
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=EXECUTABLE_VALIDATION_TIMEOUT
        )
        
        # Check if command succeeded
        if result.returncode == 0:
            logger.debug(f"Executable '{name}' validated successfully")
            return True
        else:
            logger.error(f"Executable '{name}' validation failed (return code: {result.returncode})")
            if result.stderr:
                logger.debug(f"Error output: {result.stderr.decode().strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout validating executable '{name}'")
        return False
    except FileNotFoundError:
        logger.error(f"Executable '{name}' not found: {executable}")
        return False
    except Exception as e:
        logger.error(f"Error validating executable '{name}': {e}")
        return False


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
        executables = config.get('executables', {})
        
        if not executables:
            logger.error("No executables configuration found")
            return False
        
        # Validate each required executable
        all_valid = True
        for name in REQUIRED_EXECUTABLES:
            if name not in executables:
                logger.error(f"Required executable '{name}' not configured")
                all_valid = False
                continue
            
            executable_path = executables[name]
            if not _validate_single_executable(name, executable_path):
                all_valid = False
        
        if all_valid:
            logger.info("All required executables validated successfully")
        else:
            logger.error("One or more executables failed validation")
        
        return all_valid
        
    except Exception as e:
        logger.error(f"Error during executable validation: {e}")
        return False


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup logging configuration with separate console and file handlers.
    
    This function configures logging to:
    - Always log detailed information (INFO level) to file
    - Show INFO messages on console only if verbose=True
    - Always show WARNING+ messages on console
    
    Args:
        config: Configuration dictionary containing logging and general settings
    """
    # Get logging configuration
    logging_config = config.get('logging', {})
    general_settings = config.get('general_settings', {})
    
    # Extract settings with defaults
    log_file = logging_config.get('log_file', 'logs/grim_details.log')
    verbose = general_settings.get('verbose', False)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Setup file handler (always INFO level for detailed logging)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Setup console handler (level depends on verbose setting)
    console_handler = logging.StreamHandler()
    if verbose:
        console_handler.setLevel(logging.INFO)
    else:
        console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - File: {log_file}, Console verbose: {verbose}")
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)