"""
Tests for the startup environment validation system.
"""

import os
import tempfile
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


class TestStartupValidatorAdditionalScenarios:
    """Additional comprehensive tests for StartupValidator edge cases and scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console(file=None)
        self.validator = StartupValidator(self.console)
    
    def test_validation_result_equality(self):
        """Test ValidationResult equality comparison."""
        result1 = ValidationResult(True, "message", ["suggestion"])
        result2 = ValidationResult(True, "message", ["suggestion"])
        result3 = ValidationResult(False, "message", ["suggestion"])
        
        # Test that ValidationResult objects can be compared meaningfully
        assert result1.success == result2.success
        assert result1.message == result2.message
        assert result1.suggestions == result2.suggestions
        assert result1.success != result3.success
    
    def test_validation_result_empty_message(self):
        """Test ValidationResult with empty message."""
        result = ValidationResult(True, "", [])
        assert result.success is True
        assert result.message == ""
        assert result.suggestions == []
    
    def test_validation_result_none_suggestions(self):
        """Test ValidationResult with None suggestions (should default to empty list)."""
        result = ValidationResult(False, "Error", None)
        assert result.suggestions == []
    
    @patch.dict(os.environ, {'CONDA_DEFAULT_ENV': ''})
    def test_validate_virtual_environment_empty_conda_env(self):
        """Test virtual environment validation with empty CONDA_DEFAULT_ENV."""
        result = self.validator._validate_virtual_environment()
        
        # Should handle empty conda env gracefully
        assert result.success is False
        assert "No virtual environment detected" in result.message
    
    @patch.dict(os.environ, {'VIRTUAL_ENV': ''}, clear=True)
    def test_validate_virtual_environment_empty_venv(self):
        """Test virtual environment validation with empty VIRTUAL_ENV."""
        result = self.validator._validate_virtual_environment()
        
        assert result.success is False
        assert "No virtual environment detected" in result.message
    
    @patch('sys.prefix', '/opt/miniconda3/envs/test')
    @patch('sys.base_prefix', '/opt/miniconda3')
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_virtual_environment_prefix_detection(self):
        """Test virtual environment detection via sys.prefix comparison."""
        result = self.validator._validate_virtual_environment()
        
        assert result.success is True
        assert "Virtual Environment" in result.message
    
    @patch('grimperium.utils.startup_validator.__import__')
    def test_validate_python_dependencies_partial_failure(self, mock_import):
        """Test Python dependencies validation with mixed success/failure."""
        failed_packages = ['numpy', 'scipy']
        
        def side_effect(package):
            if package in failed_packages:
                raise ImportError(f"No module named '{package}'")
            return MagicMock()
        
        mock_import.side_effect = side_effect
        
        result = self.validator._validate_python_dependencies()
        
        assert result.success is False
        assert "Missing" in result.message
        # Should suggest installing the missing packages
        suggestions_text = ' '.join(result.suggestions)
        for package in failed_packages:
            assert package in suggestions_text
    
    @patch('grimperium.utils.startup_validator.__import__')
    def test_validate_python_dependencies_all_missing(self, mock_import):
        """Test Python dependencies validation when all packages are missing."""
        mock_import.side_effect = ImportError("No module found")
        
        result = self.validator._validate_python_dependencies()
        
        assert result.success is False
        assert "Missing" in result.message
        assert len(result.suggestions) > 0
        assert any("pip install" in suggestion for suggestion in result.suggestions)
    
    @patch('grimperium.utils.startup_validator.__import__')
    def test_validate_python_dependencies_import_error_handling(self, mock_import):
        """Test handling of various ImportError scenarios."""
        def side_effect(package):
            if package == 'pandas':
                raise ImportError("DLL load failed")
            elif package == 'numpy':
                raise ModuleNotFoundError("No module named 'numpy'")
            else:
                return MagicMock()
        
        mock_import.side_effect = side_effect
        
        result = self.validator._validate_python_dependencies()
        
        assert result.success is False
        assert "Missing" in result.message
    
    @patch('shutil.which')
    def test_validate_external_tools_empty_executables(self, mock_which):
        """Test external tools validation with empty executables config."""
        config = {'executables': {}}
        
        result = self.validator._validate_external_tools(config)
        
        assert result.success is True  # No tools to validate means success
        assert "No external tools configured" in result.message or "available" in result.message
    
    @patch('shutil.which')
    def test_validate_external_tools_version_check_failure(self, mock_which):
        """Test external tools validation when version check fails."""
        mock_which.return_value = '/usr/bin/tool'
        
        with patch.object(self.validator, '_get_tool_version') as mock_version:
            mock_version.return_value = None  # Version check failed
            
            config = {'executables': {'crest': 'crest'}}
            result = self.validator._validate_external_tools(config)
            
            # Tool exists but version check failed - should still be considered available
            assert result.success is True
            assert "crest" in result.message.lower()
    
    @patch('shutil.which')
    def test_validate_external_tools_mixed_availability(self, mock_which):
        """Test external tools validation with mixed tool availability."""
        def which_side_effect(tool):
            return '/usr/bin/tool' if tool in ['crest', 'obabel'] else None
        
        mock_which.side_effect = which_side_effect
        
        with patch.object(self.validator, '_get_tool_version') as mock_version:
            mock_version.return_value = "Tool v1.0"
            
            config = {
                'executables': {
                    'crest': 'crest',
                    'mopac': 'mopac',
                    'obabel': 'obabel',
                    'missing_tool': 'missing_tool'
                }
            }
            
            result = self.validator._validate_external_tools(config)
            
            assert result.success is False
            assert "Missing or non-functional tools" in result.message
            # Should mention the missing tools
            suggestions_text = ' '.join(result.suggestions)
            assert 'mopac' in suggestions_text.lower()
            assert 'missing_tool' in suggestions_text.lower()
    
    def test_validate_directory_permissions_nested_paths(self):
        """Test directory permissions validation with deeply nested paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, 'deep', 'nested', 'path')
            config = {
                'repository_base_path': nested_path,
                'database': {
                    'cbs_db_path': os.path.join(nested_path, 'data', 'cbs.csv')
                },
                'logging': {
                    'log_file': os.path.join(nested_path, 'logs', 'app.log')
                }
            }
            
            result = self.validator._validate_directory_permissions(config)
            
            assert result.success is True
            assert "accessible" in result.message
    
    def test_validate_directory_permissions_missing_config_keys(self):
        """Test directory permissions validation with missing configuration keys."""
        config = {
            'repository_base_path': '/tmp'
            # Missing database and logging sections
        }
        
        result = self.validator._validate_directory_permissions(config)
        
        # Should handle missing keys gracefully
        assert result.success is True  # Only validates existing paths
    
    def test_validate_directory_permissions_relative_paths(self):
        """Test directory permissions validation with relative paths."""
        config = {
            'repository_base_path': './test_repo',
            'database': {
                'cbs_db_path': './data/cbs.csv'
            }
        }
        
        result = self.validator._validate_directory_permissions(config)
        
        # Should handle relative paths appropriately
        assert isinstance(result.success, bool)
        assert isinstance(result.message, str)
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_mopac(self, mock_execute):
        """Test getting version for MOPAC tool with specific version format."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "MOPAC2016 (Version: 21.298L)"
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('mopac', 'mopac')
        
        assert "MOPAC2016" in version
        assert "21.298L" in version
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_obabel(self, mock_execute):
        """Test getting version for Open Babel tool."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Open Babel 3.1.1\nCopyright (C) 1998-2020"
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('obabel', 'obabel')
        
        assert "Open Babel 3.1.1" in version
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_unknown_tool(self, mock_execute):
        """Test getting version for unknown/custom tool."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "CustomTool v2.5.3\nAdditional info"
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('custom_tool', 'custom_tool')
        
        assert "CustomTool v2.5.3" in version
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_empty_output(self, mock_execute):
        """Test getting version when tool returns empty output."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = ""
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('silent_tool', 'silent_tool')
        
        assert version is None or version == ""
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_multiline_output(self, mock_execute):
        """Test getting version from multiline tool output."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = """Tool Name: MyTool
Version: 1.2.3
Build: 20240101
Platform: Linux x86_64"""
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('mytool', 'mytool')
        
        # Should extract the first meaningful line
        assert "Tool Name: MyTool" in version or "Version: 1.2.3" in version
    
    def test_validate_environment_exception_handling(self):
        """Test validate_environment handles exceptions gracefully."""
        with patch.object(self.validator, '_validate_virtual_environment') as mock_venv:
            # Mock an exception during validation
            mock_venv.side_effect = Exception("Unexpected error")
            
            success, results = self.validator.validate_environment({})
            
            # Should handle exceptions and continue with other validations
            assert success is False
            assert len(results) >= 1  # Should have at least some results
    
    def test_validate_environment_empty_config(self):
        """Test validate_environment with completely empty configuration."""
        success, results = self.validator.validate_environment({})
        
        assert isinstance(success, bool)
        assert isinstance(results, list)
        assert len(results) > 0  # Should perform some validations
    
    def test_startup_validator_with_none_console(self):
        """Test StartupValidator initialization with None console."""
        validator = StartupValidator(None)
        
        # Should handle None console gracefully
        assert validator.console is not None  # Should create default console
    
    def test_display_validation_results_all_success(self):
        """Test display_validation_results with all successful validations."""
        results = [
            ValidationResult(True, "Test 1 passed"),
            ValidationResult(True, "Test 2 passed"),
            ValidationResult(True, "Test 3 passed")
        ]
        
        # Should not raise exception
        try:
            self.validator.display_validation_results(results)
        except Exception as e:
            pytest.fail(f"display_validation_results raised exception: {e}")
    
    def test_display_validation_results_with_failures(self):
        """Test display_validation_results with some failures."""
        results = [
            ValidationResult(True, "Test 1 passed"),
            ValidationResult(False, "Test 2 failed", ["Fix suggestion 1", "Fix suggestion 2"]),
            ValidationResult(False, "Test 3 failed", ["Another fix"])
        ]
        
        # Should not raise exception and handle suggestions
        try:
            self.validator.display_validation_results(results)
        except Exception as e:
            pytest.fail(f"display_validation_results raised exception: {e}")
    
    def test_display_validation_results_empty_list(self):
        """Test display_validation_results with empty results list."""
        results = []
        
        try:
            self.validator.display_validation_results(results)
        except Exception as e:
            pytest.fail(f"display_validation_results raised exception: {e}")


class TestValidationResultComprehensive:
    """Comprehensive tests for ValidationResult edge cases."""
    
    def test_validation_result_with_long_message(self):
        """Test ValidationResult with very long message."""
        long_message = "A" * 1000  # Very long message
        result = ValidationResult(True, long_message, [])
        
        assert result.message == long_message
        assert len(result.message) == 1000
    
    def test_validation_result_with_unicode_message(self):
        """Test ValidationResult with unicode characters in message."""
        unicode_message = "Test with unicode: αβγδε 中文 🚀"
        result = ValidationResult(False, unicode_message, ["Fix unicode"])
        
        assert result.message == unicode_message
        assert result.success is False
    
    def test_validation_result_with_many_suggestions(self):
        """Test ValidationResult with many suggestions."""
        many_suggestions = [f"Suggestion {i}" for i in range(100)]
        result = ValidationResult(False, "Many suggestions test", many_suggestions)
        
        assert len(result.suggestions) == 100
        assert all(isinstance(s, str) for s in result.suggestions)
    
    def test_validation_result_with_empty_suggestions(self):
        """Test ValidationResult with empty string suggestions."""
        empty_suggestions = ["", "Valid suggestion", "", "Another valid"]
        result = ValidationResult(False, "Mixed suggestions", empty_suggestions)
        
        assert result.suggestions == empty_suggestions
        assert "" in result.suggestions


class TestStartupValidatorErrorScenarios:
    """Test error scenarios and edge cases for StartupValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StartupValidator()
    
    @patch('os.access')
    def test_validate_directory_permissions_access_denied(self, mock_access):
        """Test directory permissions when access is denied."""
        mock_access.return_value = False
        
        config = {
            'repository_base_path': '/restricted/path',
            'database': {'cbs_db_path': '/restricted/path/data.csv'}
        }
        
        result = self.validator._validate_directory_permissions(config)
        
        assert result.success is False
        assert "permission" in result.message.lower()
    
    @patch('pathlib.Path.mkdir')
    def test_validate_directory_permissions_mkdir_failure(self, mock_mkdir):
        """Test directory creation failure scenarios."""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        config = {
            'repository_base_path': '/tmp/test_grimperium',
            'logging': {'log_file': '/tmp/test_grimperium/logs/app.log'}
        }
        
        result = self.validator._validate_directory_permissions(config)
        
        assert result.success is False
        assert len(result.suggestions) > 0
    
    @patch('grimperium.utils.startup_validator.execute_command')
    def test_get_tool_version_command_timeout(self, mock_execute):
        """Test tool version check with command timeout."""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.stderr = "Command timed out"
        mock_execute.return_value = mock_result
        
        version = self.validator._get_tool_version('slow_tool', 'slow_tool')
        
        assert version is None
    
    def test_validate_startup_environment_with_custom_console(self):
        """Test validate_startup_environment with custom console."""
        from io import StringIO
        
        custom_output = StringIO()
        
        with patch('grimperium.utils.startup_validator.StartupValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_environment.return_value = (True, [])
            
            # This should work without specifying console parameter
            result = validate_startup_environment({})
            
            assert isinstance(result, bool)


class TestStartupValidatorIntegrationScenarios:
    """Integration-style tests for complete validation workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StartupValidator()
    
    def test_complete_validation_workflow_realistic_config(self):
        """Test complete validation with realistic configuration."""
        realistic_config = {
            'executables': {
                'python': 'python3',
                'git': 'git'
            },
            'repository_base_path': '/tmp/grimperium_test',
            'database': {
                'cbs_db_path': '/tmp/grimperium_test/data/cbs.csv',
                'pm7_db_path': '/tmp/grimperium_test/data/pm7.csv'
            },
            'logging': {
                'log_file': '/tmp/grimperium_test/logs/grimperium.log',
                'level': 'INFO'
            }
        }
        
        # This will run actual validation methods
        success, results = self.validator.validate_environment(realistic_config)
        
        # Verify structure of results
        assert isinstance(success, bool)
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Each result should be a ValidationResult
        for result in results:
            assert hasattr(result, 'success')
            assert hasattr(result, 'message')
            assert hasattr(result, 'suggestions')
            assert isinstance(result.success, bool)
            assert isinstance(result.message, str)
            assert isinstance(result.suggestions, list)
    
    @patch.dict(os.environ, {'CONDA_DEFAULT_ENV': 'grimperium'})
    @patch('shutil.which')
    @patch('grimperium.utils.startup_validator.__import__')
    def test_all_validations_pass_scenario(self, mock_import, mock_which):
        """Test scenario where all validations should pass."""
        # Mock all dependencies as available
        mock_import.return_value = MagicMock()
        mock_which.return_value = '/usr/bin/tool'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'executables': {'python': 'python3'},
                'repository_base_path': temp_dir,
                'database': {'cbs_db_path': f'{temp_dir}/cbs.csv'},
                'logging': {'log_file': f'{temp_dir}/app.log'}
            }
            
            with patch.object(self.validator, '_get_tool_version') as mock_version:
                mock_version.return_value = "Tool v1.0"
                
                success, results = self.validator.validate_environment(config)
                
                assert success is True
                assert all(result.success for result in results)