"""
Constants and configuration values for the Grimperium application.

This module centralizes all magic numbers, timeout values, and other
constants used throughout the computational chemistry pipeline.
"""

# Timeout constants (in seconds)
CREST_TIMEOUT = 3600  # 1 hour for conformational search
MOPAC_TIMEOUT = 1800  # 30 minutes for quantum calculations
CONVERSION_TIMEOUT = 60  # 1 minute for file format conversions
EXECUTABLE_VALIDATION_TIMEOUT = 10  # 10 seconds for executable checks
DATABASE_LOCK_TIMEOUT = 30  # 30 seconds for database file locking

# Default molecular properties
DEFAULT_CHARGE = 0
DEFAULT_MULTIPLICITY = 1

# File format extensions
SUPPORTED_FORMATS = {
    'sdf': 'Structure Data Format',
    'xyz': 'XYZ Coordinates',
    'pdb': 'Protein Data Bank',
    'smi': 'SMILES',
    'mol': 'MDL Molfile',
    'mol2': 'Tripos MOL2'
}

# Database configuration
DATABASE_SCHEMA = [
    'smiles',
    'identifier', 
    'sdf_path',
    'xyz_path',
    'crest_best_xyz_path',
    'pm7_energy',
    'charge',
    'multiplicity'
]

# File size constants
BYTES_PER_MB = 1024 * 1024
SECONDS_PER_HOUR = 3600
MINUTES_PER_HOUR = 60

# Regular expression patterns
FILENAME_SANITIZATION_PATTERN = r'[<>:"/\\|?*\s]'
MULTIPLE_UNDERSCORES_PATTERN = r'_+'
ENERGY_EXTRACTION_PATTERN = r'FINAL HEAT OF FORMATION\s*=\s*([-+]?\d+\.?\d*)\s*KCAL/MOL'

# Default values for calculations
DEFAULT_CREST_KEYWORDS = '--gfn2'
DEFAULT_MOPAC_KEYWORDS = 'PM7 PRECISE XYZ'
DEFAULT_TIME_PER_MOLECULE = 300.0  # 5 minutes in seconds

# Data quality thresholds
DATA_QUALITY_THRESHOLDS = {
    'excellent': 0.95,
    'good': 0.85,
    'acceptable': 0.70,
    'poor': 0.50
}

# Progress report time conversion thresholds
TIME_DISPLAY_THRESHOLDS = {
    'days': 24 * SECONDS_PER_HOUR,
    'hours': SECONDS_PER_HOUR,
    'minutes': 60
}

# PubChem service constants
PUBCHEM_FILENAME_FALLBACK = "unknown_compound"
PUBCHEM_SANITIZATION_REPLACEMENT = "_"

# File validation constants
MAX_EXTENSION_LENGTH = 5
MIN_IDENTIFIER_LENGTH = 1

# Executable names
REQUIRED_EXECUTABLES = ['crest', 'mopac', 'obabel']

# Default directories
DEFAULT_REPOSITORY_PATH = 'repository'
DEFAULT_DATA_PATH = 'data'
DEFAULT_LOGS_PATH = 'logs'