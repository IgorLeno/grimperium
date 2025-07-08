"""
Configuration module for Grimperium.

This module provides configuration management utilities and default values.
"""

from .defaults import (
    get_default_config,
    get_required_sections, 
    get_database_schema,
    validate_config_structure,
    DEFAULT_CONFIG,
    DATABASE_SCHEMA,
    REQUIRED_CONFIG_SECTIONS
)

__all__ = [
    'get_default_config',
    'get_required_sections',
    'get_database_schema', 
    'validate_config_structure',
    'DEFAULT_CONFIG',
    'DATABASE_SCHEMA',
    'REQUIRED_CONFIG_SECTIONS'
]