"""
Tests for the startup environment validation system.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from rich.console import Console

from grimperium.utils.startup_validator import (
    StartupValidator,
    ValidationResult,
    validate_startup_environment
)


class TestValidationResult:
    """Test the ValidationResult class."""
    
    def test_validation_result_creation(self):
        """Test basic ValidationResult creation."""
        result = ValidationResult(
            success=True,
            message="Test message",
            suggestions=["suggestion1", "suggestion2"]
        )
        
        assert result.success is True
        assert result.message == "Test message"
        assert result.suggestions == ["suggestion1", "suggestion2"]
    
    def test_validation_result_no_suggestions(self):
        """Test ValidationResult with no suggestions."""
        result = ValidationResult(success=False, message="Error message")
        
        assert result.success is False
        assert result.message == "Error message"
        assert result.suggestions == []


class TestStartupValidator:
    """Test the StartupValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console(file=None)  # Don't write to stdout during tests
        self.validator = StartupValidator(self.console)
        
        # Sample configuration for testing
        self.sample_config = {
            'executables': {
                'crest': 'crest',
                'mopac': 'mopac',
                'obabel': 'obabel'
            },
            'repository_base_path': 'test_repository',
            'database': {
                'cbs_db_path': 'test_data/cbs.csv',
                'pm7_db_path': 'test_data/pm7.csv'
            },
            'logging': {
                'log_file': 'test_logs/test.log'
            }
        }
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = StartupValidator()
        assert validator.console is not None
        assert validator.logger is not None
        
        # Test with custom console
        custom_console = Console()
        validator_custom = StartupValidator(custom_console)
        assert validator_custom.console is custom_console
    
    @patch.dict(os.environ, {'CONDA_DEFAULT_ENV': 'test_env'})
    def test_validate_virtual_environment_conda(self):
        """Test virtual environment validation with Conda."""
        result = self.validator._validate_virtual_environment()
        
        assert result.success is True
        assert "Conda environment: test_env" in result.message
        assert len(result.suggestions) == 0
    
    @patch.dict(os.environ, {'VIRTUAL_ENV': '/path/to/venv'}, clear=True)
    def test_validate_virtual_environment_venv(self):
        """Test virtual environment validation with venv."""
        result = self.validator._validate_virtual_environment()
        
        assert result.success is True
        assert "Virtual Environment" in result.message
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.prefix', '/usr')
    @patch('sys.base_prefix', '/usr')
    def test_validate_virtual_environment_none(self):
        """Test virtual environment validation with no virtual environment."""
        result = self.validator._validate_virtual_environment()
        
        assert result.success is False
        assert "No virtual environment detected" in result.message
        assert len(result.suggestions) > 0
        assert any("conda activate" in suggestion for suggestion in result.suggestions)
    
    @patch('grimperium.utils.startup_validator.__import__')
    def test_validate_python_dependencies_success(self, mock_import):
        """Test Python dependencies validation - all packages available."""
        # Mock successful imports
        mock_import.return_value = MagicMock()
        
        result = self.validator._validate_python_dependencies()
        
        assert result.success is True
        assert "Python dependencies are installed" in result.message
    
    @patch('grimperium.utils.startup_validator.__import__')
    def test_validate_python_dependencies_missing(self, mock_import):
        """Test Python dependencies validation - some packages missing."""
        # Mock failed imports for some packages
        def side_effect(package):
            if package in ['pandas', 'typer']:
                return MagicMock()
            else:
                raise ImportError(f"No module named '{package}'")
        
        mock_import.side_effect = side_effect
        
        result = self.validator._validate_python_dependencies()
        
        assert result.success is False
        assert "Missing" in result.message
        assert len(result.suggestions) > 0
        assert any("pip install" in suggestion for suggestion in result.suggestions)
    
    @patch('shutil.which')
    def test_validate_external_tools_success(self, mock_which):
        """Test external tools validation - all tools available."""
        # Mock all tools as available
        mock_which.return_value = '/usr/bin/tool'
        
        with patch.object(self.validator, '_get_tool_version') as mock_version:
            mock_version.return_value = "Tool v1.0"
            
            result = self.validator._validate_external_tools(self.sample_config)
            
            assert result.success is True
            assert "All external tools available" in result.message
    
    @patch('shutil.which')
    def test_validate_external_tools_missing(self, mock_which):
        """Test external tools validation - some tools missing."""
        # Mock some tools as missing
        def which_side_effect(tool):
            if tool == 'crest':
                return '/usr/bin/crest'
            else:
                return None
        
        mock_which.side_effect = which_side_effect
        
        with patch.object(self.validator, '_get_tool_version') as mock_version:
            mock_version.return_value = "CREST v1.0"
            
            result = self.validator._validate_external_tools(self.sample_config)
            
            assert result.success is False
            assert "Missing or non-functional tools" in result.message
            assert len(result.suggestions) > 0
            assert any("MOPAC" in suggestion for suggestion in result.suggestions)
    
    def test_validate_external_tools_no_config(self):
        """Test external tools validation with missing configuration."""
        empty_config = {}
        
        result = self.validator._validate_external_tools(empty_config)
        
        assert result.success is False
        assert "No executables configuration found" in result.message
    
    def test_validate_directory_permissions_success(self):
        """Test directory permissions validation - success case."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config that uses the temporary directory
            config = {
                'repository_base_path': temp_dir,
                'database': {
                    'cbs_db_path': f'{temp_dir}/cbs.csv',
                    'pm7_db_path': f'{temp_dir}/pm7.csv'
                },
                'logging': {
                    'log_file': f'{temp_dir}/test.log'
                }
            }
            
            result = self.validator._validate_directory_permissions(config)
            
            assert result.success is True
            assert "required directories are accessible" in result.message
    
    def test_validate_directory_permissions_failure(self):
        """Test directory permissions validation - failure case."""
        # Use a non-existent parent directory that cannot be created
        config = {
            'repository_base_path': '/nonexistent/readonly/path',
            'database': {
                'cbs_db_path': '/nonexistent/readonly/path/cbs.csv'
            }
        }
        
        result = self.validator._validate_directory_permissions(config)
        
        assert result.success is False
        assert "Directory permission issues" in result.message
        assert len(result.suggestions) > 0
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_crest(self, mock_execute):
        """Test getting version for CREST tool."""
        # Mock successful command execution
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "CREST version 2.12\nOther output"
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('crest', 'crest')
        
        assert version == "CREST version 2.12"
        mock_execute.assert_called_once()
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_failure(self, mock_execute):
        """Test getting version when tool fails."""
        # Mock failed command execution
        mock_result = MagicMock()
        mock_result.success = False
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('crest', 'crest')
        
        assert version is None
    
    def test_validate_environment_integration(self):
        """Test the complete validate_environment method."""
        with patch.object(self.validator, '_validate_virtual_environment') as mock_venv, \
             patch.object(self.validator, '_validate_python_dependencies') as mock_deps, \
             patch.object(self.validator, '_validate_external_tools') as mock_tools, \
             patch.object(self.validator, '_validate_directory_permissions') as mock_dirs:
            
            # Mock all validations as successful
            mock_venv.return_value = ValidationResult(True, "venv ok")
            mock_deps.return_value = ValidationResult(True, "deps ok")
            mock_tools.return_value = ValidationResult(True, "tools ok")
            mock_dirs.return_value = ValidationResult(True, "dirs ok")
            
            success, results = self.validator.validate_environment(self.sample_config)
            
            assert success is True
            assert len(results) == 4
            assert all(result.success for result in results)
    
    def test_validate_environment_failure(self):
        """Test validate_environment with some failures."""
        with patch.object(self.validator, '_validate_virtual_environment') as mock_venv, \
             patch.object(self.validator, '_validate_python_dependencies') as mock_deps, \
             patch.object(self.validator, '_validate_external_tools') as mock_tools, \
             patch.object(self.validator, '_validate_directory_permissions') as mock_dirs:
            
            # Mock mixed success/failure
            mock_venv.return_value = ValidationResult(True, "venv ok")
            mock_deps.return_value = ValidationResult(False, "deps failed")
            mock_tools.return_value = ValidationResult(True, "tools ok")
            mock_dirs.return_value = ValidationResult(False, "dirs failed")
            
            success, results = self.validator.validate_environment(self.sample_config)
            
            assert success is False
            assert len(results) == 4
            assert sum(1 for result in results if not result.success) == 2


class TestValidateStartupEnvironment:
    """Test the convenience function."""
    
    def test_validate_startup_environment_success(self):
        """Test the convenience function with successful validation."""
        sample_config = {'executables': {'crest': 'crest'}}
        
        with patch('grimperium.utils.startup_validator.StartupValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_environment.return_value = (
                True, 
                [ValidationResult(True, "All good")]
            )
            
            result = validate_startup_environment(sample_config)
            
            assert result is True
            mock_validator.validate_environment.assert_called_once_with(sample_config)
            mock_validator.display_validation_results.assert_called_once()
    
    def test_validate_startup_environment_failure(self):
        """Test the convenience function with failed validation."""
        sample_config = {'executables': {'crest': 'crest'}}
        
        with patch('grimperium.utils.startup_validator.StartupValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_environment.return_value = (
                False, 
                [ValidationResult(False, "Something failed", ["Fix it"])]
            )
            
            result = validate_startup_environment(sample_config)
            
            assert result is False
            mock_validator.display_validation_results.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])