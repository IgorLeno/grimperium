"""
Tests for the pipeline orchestrator module.

This module contains comprehensive tests for the pipeline orchestration
functionality, using mocks to simulate external dependencies like
computational chemistry software and network requests.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call
import pytest
import pandas as pd

from grimperium.services.pipeline_orchestrator import (
    process_single_molecule,
    sanitize_identifier,
    extract_smiles_from_sdf
)


class TestSanitizeIdentifier:
    """Test the identifier sanitization function."""
    
    def test_basic_sanitization(self):
        """Test basic character sanitization."""
        assert sanitize_identifier("simple_name") == "simple_name"
        assert sanitize_identifier("ethanol") == "ethanol"
    
    def test_special_characters(self):
        """Test sanitization of special characters."""
        assert sanitize_identifier("complex/name:with<>symbols") == "complex_name_with_symbols"
        assert sanitize_identifier("name with spaces") == "name_with_spaces"
        assert sanitize_identifier("multiple___underscores") == "multiple_underscores"
    
    def test_edge_cases(self):
        """Test edge cases for sanitization."""
        assert sanitize_identifier("") == "unknown_molecule"
        assert sanitize_identifier("...") == "unknown_molecule"
        assert sanitize_identifier("___") == "unknown_molecule"


class TestPipelineOrchestrator:
    """Test the main pipeline orchestration functionality."""
    
    def setup_mock_subprocess(self, mocker, tmp_path):
        """
        Set up intelligent subprocess mocking that creates appropriate output files.
        
        This mock simulates the behavior of external programs by:
        - Creating output files that the real programs would create
        - Returning appropriate exit codes
        - Handling different command patterns
        """
        def mock_subprocess_run(command, **kwargs):
            """Mock subprocess.run with intelligent file creation."""
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Mock stdout"
            mock_result.stderr = ""
            
            # Handle different command patterns
            if "obabel" in command[0]:
                # OpenBabel conversion
                if "-O" in command:
                    output_idx = command.index("-O") + 1
                    if output_idx < len(command):
                        output_path = Path(command[output_idx])
                        # Create the output file
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Create appropriate content based on file type
                        if output_path.suffix == ".xyz":
                            content = "3\nMock XYZ file\nC 0.0 0.0 0.0\nH 1.0 0.0 0.0\nH -1.0 0.0 0.0\n"
                        elif output_path.suffix == ".pdb":
                            content = "HEADER    Mock PDB file\nATOM      1  C   MOL     1       0.000   0.000   0.000\nEND\n"
                        elif output_path.suffix == ".smi":
                            content = "CCO ethanol\n"
                        else:
                            content = "Mock file content\n"
                            
                        output_path.write_text(content)
            
            elif "crest" in command[0]:
                # CREST conformational search
                cwd = kwargs.get('cwd', '.')
                crest_output = Path(cwd) / "crest_best.xyz"
                crest_output.parent.mkdir(parents=True, exist_ok=True)
                crest_output.write_text("3\nCREST best conformer\nC 0.0 0.0 0.0\nH 1.0 0.0 0.0\nH -1.0 0.0 0.0\n")
            
            elif "mopac" in command[0]:
                # MOPAC quantum chemistry calculation
                # Determine output file path (same as input but with .out extension)
                input_file = None
                for arg in command[1:]:
                    if not arg.startswith('-') and Path(arg).exists():
                        input_file = Path(arg)
                        break
                
                if input_file:
                    output_file = input_file.with_suffix(".out")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create MOPAC output with energy value
                    mopac_output = """
 MOPAC Mock Output File
 **********************
 
 FINAL HEAT OF FORMATION = -12.345 KCAL/MOL
 
 COMPUTATION TIME = 0.01 SECONDS
"""
                    output_file.write_text(mopac_output)
            
            return mock_result
        
        return mocker.patch('subprocess.run', side_effect=mock_subprocess_run)
    
    def setup_mock_pubchem(self, mocker, expected_sdf_path):
        """Set up mock for PubChem service."""
        def mock_download_sdf(name, output_dir):
            """Mock PubChem download that creates a fake SDF file."""
            # Ensure the directory structure exists
            expected_sdf_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create mock SDF file at expected location
            sdf_content = """
  Mrv2014 01012021 2D          
 
  3  2  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
   -1.0000    0.0000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
M  END
$$$$
"""
            expected_sdf_path.write_text(sdf_content)
            return str(expected_sdf_path.absolute())
        
        return mocker.patch(
            'grimperium.services.pubchem_service.download_sdf_by_name',
            side_effect=mock_download_sdf
        )
    
    def test_process_single_molecule_success(self, mocker, tmp_path):
        """
        Test successful processing of a single molecule through the entire pipeline.
        
        This test verifies that:
        1. All pipeline steps execute successfully
        2. Appropriate files are created
        3. Data is correctly saved to the database
        4. The function returns True for success
        """
        # Setup test environment
        work_dir = tmp_path / "test_work"
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Configure test config
        test_config = {
            'executables': {
                'crest': 'crest',
                'mopac': 'mopac', 
                'obabel': 'obabel'
            },
            'crest_keywords': '--gfn2',
            'mopac_keywords': 'PM7 PRECISE XYZ',
            'repository_base_path': str(work_dir),
            'database': {
                'pm7_db_path': str(data_dir / 'thermo_pm7.csv')
            }
        }
        
        # Calculate expected SDF path
        expected_sdf_path = work_dir / "ethanol" / "ethanol.sdf"
        
        # Setup mocks
        mock_subprocess = self.setup_mock_subprocess(mocker, tmp_path)
        mock_pubchem = self.setup_mock_pubchem(mocker, expected_sdf_path)
        
        # Change to temporary directory for test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Execute the pipeline
            result = process_single_molecule("ethanol", test_config)
            
            # Verify success
            assert result is True, "Pipeline should return True for successful processing"
            
            # Verify PubChem was called
            mock_pubchem.assert_called_once()
            
            # Verify subprocess was called multiple times (obabel, crest, mopac)
            assert mock_subprocess.call_count >= 3, "Should call subprocess multiple times"
            
            # Verify database file was created
            db_path = Path(test_config['database']['pm7_db_path'])
            assert db_path.exists(), "Database file should be created"
            
            # Verify database content
            df = pd.read_csv(db_path)
            assert len(df) == 1, "Database should contain one entry"
            assert df.iloc[0]['identifier'] == 'ethanol', "Should save correct identifier"
            assert df.iloc[0]['pm7_energy'] == -12.345, "Should save correct energy value"
            
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_process_single_molecule_pubchem_failure(self, mocker, tmp_path):
        """Test pipeline behavior when PubChem download fails."""
        # Setup config
        test_config = {
            'repository_base_path': str(tmp_path),
            'database': {'pm7_db_path': str(tmp_path / 'test.csv')}
        }
        
        # Mock PubChem to return None (failure)
        mocker.patch(
            'grimperium.services.pubchem_service.download_sdf_by_name',
            return_value=None
        )
        
        # Change to temporary directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = process_single_molecule("nonexistent_molecule", test_config)
            assert result is False, "Should return False when PubChem download fails"
        finally:
            os.chdir(original_cwd)
    
    def test_process_single_molecule_conversion_failure(self, mocker, tmp_path):
        """Test pipeline behavior when file conversion fails."""
        # Calculate expected SDF path
        expected_sdf_path = tmp_path / "test_molecule" / "test_molecule.sdf"
        
        # Setup mocks
        mock_pubchem = self.setup_mock_pubchem(mocker, expected_sdf_path)
        
        # Mock conversion service to fail
        mocker.patch(
            'grimperium.services.conversion_service.convert_file',
            return_value=None
        )
        
        test_config = {
            'repository_base_path': str(tmp_path),
            'database': {'pm7_db_path': str(tmp_path / 'test.csv')}
        }
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = process_single_molecule("test_molecule", test_config)
            assert result is False, "Should return False when conversion fails"
        finally:
            os.chdir(original_cwd)
    
    def test_process_single_molecule_crest_failure(self, mocker, tmp_path):
        """Test pipeline behavior when CREST calculation fails."""
        # Calculate expected SDF path
        expected_sdf_path = tmp_path / "test_molecule" / "test_molecule.sdf"
        
        # Setup mocks for early stages
        mock_pubchem = self.setup_mock_pubchem(mocker, expected_sdf_path)
        
        # Mock conversion to succeed
        mocker.patch(
            'grimperium.services.conversion_service.convert_file',
            return_value=str(tmp_path / 'test.xyz')
        )
        
        # Mock CREST to fail
        mocker.patch(
            'grimperium.services.calculation_service.run_crest',
            return_value=None
        )
        
        test_config = {
            'crest_keywords': '--gfn2',
            'repository_base_path': str(tmp_path),
            'database': {'pm7_db_path': str(tmp_path / 'test.csv')}
        }
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = process_single_molecule("test_molecule", test_config)
            assert result is False, "Should return False when CREST fails"
        finally:
            os.chdir(original_cwd)


class TestExtractSmilesFromSdf:
    """Test SMILES extraction from SDF files."""
    
    def test_extract_smiles_success(self, mocker, tmp_path):
        """Test successful SMILES extraction."""
        # Create mock SDF file
        sdf_file = tmp_path / "test.sdf"
        sdf_file.write_text("Mock SDF content")
        
        # Mock conversion service
        smiles_file = tmp_path / "test.smi"
        smiles_file.write_text("CCO ethanol")
        
        mocker.patch(
            'grimperium.services.conversion_service.convert_file',
            return_value=str(smiles_file)
        )
        
        result = extract_smiles_from_sdf(str(sdf_file))
        assert result == "CCO", "Should extract SMILES correctly"
    
    def test_extract_smiles_conversion_failure(self, mocker, tmp_path):
        """Test SMILES extraction when conversion fails."""
        sdf_file = tmp_path / "test.sdf" 
        sdf_file.write_text("Mock SDF content")
        
        # Mock conversion to fail
        mocker.patch(
            'grimperium.services.conversion_service.convert_file',
            return_value=None
        )
        
        result = extract_smiles_from_sdf(str(sdf_file))
        assert result is None, "Should return None when conversion fails"
    
    def test_extract_smiles_file_not_found(self):
        """Test SMILES extraction with non-existent file."""
        result = extract_smiles_from_sdf("/nonexistent/file.sdf")
        assert result is None, "Should return None for non-existent file"


# Pytest fixtures for common test setup
@pytest.fixture
def sample_config(tmp_path):
    """Provide a sample configuration for testing."""
    return {
        'executables': {
            'crest': 'crest',
            'mopac': 'mopac',
            'obabel': 'obabel'
        },
        'crest_keywords': '--gfn2',
        'mopac_keywords': 'PM7 PRECISE XYZ',
        'repository_base_path': str(tmp_path),
        'database': {
            'pm7_db_path': str(tmp_path / 'thermo_pm7.csv'),
            'cbs_db_path': str(tmp_path / 'thermo_cbs.csv')
        }
    }


@pytest.fixture
def mock_all_external_services(mocker):
    """Mock all external services for isolated testing."""
    mocks = {
        'pubchem': mocker.patch('grimperium.services.pubchem_service.download_sdf_by_name'),
        'conversion': mocker.patch('grimperium.services.conversion_service.convert_file'),
        'crest': mocker.patch('grimperium.services.calculation_service.run_crest'),
        'mopac': mocker.patch('grimperium.services.calculation_service.run_mopac'),
        'parse_mopac': mocker.patch('grimperium.services.calculation_service.parse_mopac_output'),
        'database': mocker.patch('grimperium.services.database_service.append_to_database')
    }
    return mocks