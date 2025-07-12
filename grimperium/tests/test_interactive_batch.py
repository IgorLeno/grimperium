"""
Tests for the interactive_batch module.

This module contains comprehensive tests for the interactive batch workflow
functionality, focusing on the validation logic and user interaction scenarios.
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import pytest

from grimperium.ui.interactive_batch import InteractiveBatchWorkflow


class TestInteractiveBatchWorkflow:
    """Test the InteractiveBatchWorkflow class."""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary configuration for testing."""
        lists_dir = tmp_path / "lists"
        lists_dir.mkdir()
        repo_dir = tmp_path / "repository"
        repo_dir.mkdir()
        
        return {
            'general_settings': {'lists_directory': str(lists_dir)},
            'repository_base_path': str(repo_dir),
            'database': {'pm7_db_path': str(tmp_path / 'thermo_pm7.csv')},
            'executables': {
                'crest': 'crest',
                'mopac': 'mopac',
                'obabel': 'obabel'
            }
        }

    @pytest.fixture
    def workflow(self, temp_config):
        """Create a workflow instance for testing."""
        return InteractiveBatchWorkflow(temp_config)

    def test_init(self, workflow, temp_config):
        """Test workflow initialization."""
        assert workflow.config == temp_config
        assert workflow.molecules == []
        assert workflow.current_file is None
        assert workflow.molecule_smiles_map == {}
        assert workflow.molecules_to_overwrite == set()
        assert hasattr(workflow, '_validation_completed')
        assert not workflow._validation_completed

    def test_reset_validation_state(self, workflow):
        """Test validation state reset functionality."""
        # Set up initial state
        workflow.molecules = ["molecule1", "molecule2"]
        workflow.molecule_smiles_map = {"molecule1": "CC", "molecule2": "CCO"}
        workflow.molecules_to_overwrite = {"molecule1"}
        workflow._validation_completed = True
        
        # Reset validation state
        workflow._reset_validation_state()
        
        # Verify state was reset
        assert workflow.molecule_smiles_map == {}
        assert workflow.molecules_to_overwrite == set()
        assert not workflow._validation_completed

    def test_add_single_molecule_success(self, workflow):
        """Test successful addition of a single molecule."""
        # Mock questionary input
        with patch('questionary.text') as mock_text:
            mock_text.return_value.ask.return_value = "ethanol"
            
            initial_count = len(workflow.molecules)
            workflow._add_single_molecule()
            
            assert len(workflow.molecules) == initial_count + 1
            assert "ethanol" in workflow.molecules

    def test_add_single_molecule_duplicate(self, workflow):
        """Test adding a duplicate molecule."""
        workflow.molecules = ["ethanol"]
        
        with patch('questionary.text') as mock_text:
            mock_text.return_value.ask.return_value = "ethanol"
            
            initial_count = len(workflow.molecules)
            workflow._add_single_molecule()
            
            # Should not add duplicate
            assert len(workflow.molecules) == initial_count

    def test_add_from_another_list_success(self, workflow, temp_config):
        """Test successful addition from another list file."""
        # Create a test list file
        lists_dir = Path(temp_config['general_settings']['lists_directory'])
        test_file = lists_dir / "test.txt"
        test_file.write_text("molecule1\nmolecule2\n")
        
        # Mock questionary selection
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask.return_value = "test.txt"
            
            initial_count = len(workflow.molecules)
            workflow._add_from_another_list()
            
            assert len(workflow.molecules) == initial_count + 2
            assert "molecule1" in workflow.molecules
            assert "molecule2" in workflow.molecules

    def test_add_from_another_list_with_duplicates(self, workflow, temp_config):
        """Test adding from another list with duplicates."""
        # Set up initial molecules
        workflow.molecules = ["molecule1"]
        
        # Create a test list file with duplicates
        lists_dir = Path(temp_config['general_settings']['lists_directory'])
        test_file = lists_dir / "test.txt"
        test_file.write_text("molecule1\nmolecule2\nmolecule3\n")
        
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask.return_value = "test.txt"
            
            initial_count = len(workflow.molecules)
            workflow._add_from_another_list()
            
            # Should add only non-duplicates
            assert len(workflow.molecules) == initial_count + 2
            assert "molecule2" in workflow.molecules
            assert "molecule3" in workflow.molecules

    def test_add_from_another_list_cancelled(self, workflow, temp_config):
        """Test cancelling addition from another list."""
        lists_dir = Path(temp_config['general_settings']['lists_directory'])
        test_file = lists_dir / "test.txt"
        test_file.write_text("molecule1\nmolecule2\n")
        
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask.return_value = "← Cancelar"
            
            initial_count = len(workflow.molecules)
            workflow._add_from_another_list()
            
            # Should not add anything
            assert len(workflow.molecules) == initial_count

    def test_convert_molecules_to_smiles_success(self, workflow):
        """Test successful SMILES conversion."""
        workflow.molecules = ["ethanol", "methanol"]
        
        # Mock get_molecule_smiles
        with patch('grimperium.ui.interactive_batch.get_molecule_smiles') as mock_smiles:
            mock_smiles.side_effect = lambda mol, config: {"ethanol": "CCO", "methanol": "CO"}[mol]
            
            result = workflow._convert_molecules_to_smiles()
            
            assert result is True
            assert workflow.molecule_smiles_map["ethanol"] == "CCO"
            assert workflow.molecule_smiles_map["methanol"] == "CO"

    def test_convert_molecules_to_smiles_partial_failure(self, workflow):
        """Test SMILES conversion with some failures."""
        workflow.molecules = ["ethanol", "invalid_molecule"]
        
        # Mock get_molecule_smiles with one failure
        with patch('grimperium.ui.interactive_batch.get_molecule_smiles') as mock_smiles:
            def mock_get_smiles(mol, config):
                if mol == "ethanol":
                    return "CCO"
                return None
            
            mock_smiles.side_effect = mock_get_smiles
            
            # Mock questionary choice to continue
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Continuar (remover moléculas sem SMILES)"
                
                result = workflow._convert_molecules_to_smiles()
                
                assert result is True
                assert len(workflow.molecules) == 1
                assert "ethanol" in workflow.molecules
                assert "invalid_molecule" not in workflow.molecules

    def test_validate_database_duplicates_no_duplicates(self, workflow):
        """Test database validation with no duplicates."""
        workflow.molecules = ["ethanol", "methanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO"}
        
        # Mock database service to return no existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = set()
            
            result = workflow._validate_database_duplicates()
            
            assert result is True
            assert len(workflow.molecules) == 2

    def test_validate_database_duplicates_overwrite_all(self, workflow):
        """Test database validation choosing to overwrite all duplicates."""
        workflow.molecules = ["ethanol", "methanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO"}
        
        # Mock database service to return existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = {"CCO", "CO"}
            
            # Mock questionary choice to overwrite all
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Sobrescrever todas (recalcular)"
                
                result = workflow._validate_database_duplicates()
                
                assert result is True
                assert len(workflow.molecules) == 2
                assert workflow.molecules_to_overwrite == {"ethanol", "methanol"}

    def test_validate_database_duplicates_skip_all(self, workflow):
        """Test database validation choosing to skip all duplicates."""
        workflow.molecules = ["ethanol", "methanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO"}
        
        # Mock database service to return existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = {"CCO", "CO"}
            
            # Mock questionary choice to skip all
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Manter todas (pular duplicatas)"
                
                result = workflow._validate_database_duplicates()
                
                # Should return False when list becomes empty
                assert result is False
                assert len(workflow.molecules) == 0  # All removed

    def test_validate_database_duplicates_individual_selection(self, workflow):
        """Test database validation with individual selection."""
        workflow.molecules = ["ethanol", "methanol", "butanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO", "butanol": "CCCCO"}
        
        # Mock database service to return some existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = {"CCO", "CO"}  # ethanol and methanol exist
            
            # Mock questionary choices
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Escolher individualmente",  # Main choice
                    "Sobrescrever (recalcular)"  # Sub choice
                ]
                
                # Mock checkbox selection
                with patch('questionary.checkbox') as mock_checkbox:
                    mock_checkbox.return_value.ask.return_value = ["ethanol"]  # Select only ethanol
                    
                    result = workflow._validate_database_duplicates()
                    
                    assert result is True
                    assert "ethanol" in workflow.molecules
                    assert "methanol" not in workflow.molecules  # Should be removed
                    assert "butanol" in workflow.molecules  # Should remain
                    assert "ethanol" in workflow.molecules_to_overwrite

    def test_validate_database_duplicates_individual_cancelled(self, workflow):
        """Test database validation with individual selection cancelled."""
        workflow.molecules = ["ethanol", "methanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO"}
        
        # Mock database service to return existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = {"CCO", "CO"}
            
            # Mock questionary choices
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Escolher individualmente"
                
                # Mock checkbox selection returning None (cancelled)
                with patch('questionary.checkbox') as mock_checkbox:
                    mock_checkbox.return_value.ask.return_value = None
                    
                    result = workflow._validate_database_duplicates()
                    
                    # Should return False when user cancels
                    assert result is False

    def test_validate_database_duplicates_individual_none_selected(self, workflow):
        """Test database validation with individual selection but none selected."""
        workflow.molecules = ["ethanol", "methanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO", "methanol": "CO"}
        
        # Mock database service to return existing SMILES
        with patch('grimperium.services.database_service.get_existing_smiles') as mock_db:
            mock_db.return_value = {"CCO", "CO"}
            
            # Mock questionary choices
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Escolher individualmente"
                
                # Mock checkbox selection returning empty list
                with patch('questionary.checkbox') as mock_checkbox:
                    mock_checkbox.return_value.ask.return_value = []
                    
                    result = workflow._validate_database_duplicates()
                    
                    # Should return False when list becomes empty
                    assert result is False
                    assert len(workflow.molecules) == 0  # All should be removed

    def test_validate_pubchem_availability_all_found(self, workflow):
        """Test PubChem validation with all molecules found."""
        workflow.molecules = ["ethanol", "methanol"]
        
        # Mock PubChem search to return compounds
        with patch('pubchempy.get_compounds') as mock_pcp:
            mock_pcp.return_value = ["mock_compound"]  # Non-empty list
            
            result = workflow._validate_pubchem_availability()
            
            assert result is True
            assert len(workflow.molecules) == 2

    def test_validate_pubchem_availability_some_not_found(self, workflow):
        """Test PubChem validation with some molecules not found."""
        workflow.molecules = ["ethanol", "invalid_molecule"]
        
        # Mock PubChem search
        with patch('pubchempy.get_compounds') as mock_pcp:
            def mock_get_compounds(molecule, search_type):
                if molecule == "ethanol":
                    return ["mock_compound"]
                return []
            
            mock_pcp.side_effect = mock_get_compounds
            
            # Mock questionary choice to continue
            with patch('questionary.select') as mock_select:
                mock_select.return_value.ask.return_value = "Continuar (ignorando e salvando em not-found.txt)"
                
                # Mock save_not_found_molecules
                with patch.object(workflow, '_save_not_found_molecules') as mock_save:
                    result = workflow._validate_pubchem_availability()
                    
                    assert result is True
                    assert len(workflow.molecules) == 1
                    assert "ethanol" in workflow.molecules
                    assert "invalid_molecule" not in workflow.molecules
                    mock_save.assert_called_once_with(["invalid_molecule"])

    def test_validation_steps_complete_success(self, workflow):
        """Test complete validation steps with success."""
        workflow.molecules = ["ethanol"]
        
        # Mock all validation steps to succeed
        with patch.object(workflow, '_convert_molecules_to_smiles', return_value=True):
            with patch.object(workflow, '_validate_database_duplicates', return_value=True):
                with patch.object(workflow, '_validate_pubchem_availability', return_value=True):
                    
                    result = workflow._validation_steps()
                    
                    assert result is True

    def test_validation_steps_smiles_conversion_failure(self, workflow):
        """Test validation steps with SMILES conversion failure."""
        workflow.molecules = ["ethanol"]
        
        # Mock SMILES conversion to fail
        with patch.object(workflow, '_convert_molecules_to_smiles', return_value=False):
            
            result = workflow._validation_steps()
            
            assert result is False

    def test_validation_steps_database_validation_failure(self, workflow):
        """Test validation steps with database validation failure."""
        workflow.molecules = ["ethanol"]
        
        # Mock SMILES conversion to succeed, database validation to fail
        with patch.object(workflow, '_convert_molecules_to_smiles', return_value=True):
            with patch.object(workflow, '_validate_database_duplicates', return_value=False):
                
                result = workflow._validation_steps()
                
                assert result is False

    def test_validation_steps_pubchem_validation_failure(self, workflow):
        """Test validation steps with PubChem validation failure."""
        workflow.molecules = ["ethanol"]
        
        # Mock first two steps to succeed, PubChem to fail
        with patch.object(workflow, '_convert_molecules_to_smiles', return_value=True):
            with patch.object(workflow, '_validate_database_duplicates', return_value=True):
                with patch.object(workflow, '_validate_pubchem_availability', return_value=False):
                    
                    result = workflow._validation_steps()
                    
                    assert result is False

    def test_interactive_editing_mode_validation_reset(self, workflow):
        """Test that interactive editing mode resets validation state."""
        # Set up validation state
        workflow.molecules = ["ethanol"]
        workflow.molecule_smiles_map = {"ethanol": "CCO"}
        workflow._validation_completed = True
        
        # Mock questionary interactions
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask.side_effect = [
                "(a) Adicionar molécula única",  # First action
                "(c) Confirmar lista e continuar"  # Second action to exit
            ]
            
            # Mock add_single_molecule
            with patch.object(workflow, '_add_single_molecule'):
                with patch.object(workflow, '_display_molecule_table'):
                    
                    result = workflow._interactive_editing_mode()
                    
                    assert result is True
                    # Validation state should be reset after adding
                    assert workflow.molecule_smiles_map == {}
                    assert not workflow._validation_completed


class TestInteractiveBatchWorkflowIntegration:
    """Integration tests for the interactive batch workflow."""
    
    def test_file_import_triggers_validation_reset(self, tmp_path):
        """Test that file import triggers validation reset."""
        # Set up temporary directories
        lists_dir = tmp_path / "lists"
        lists_dir.mkdir()
        
        # Create test files
        test_file = lists_dir / "test.txt"
        test_file.write_text("molecule1\nmolecule2\n")
        
        config = {
            'general_settings': {'lists_directory': str(lists_dir)},
            'repository_base_path': str(tmp_path / "repository"),
            'database': {'pm7_db_path': str(tmp_path / 'thermo_pm7.csv')}
        }
        
        workflow = InteractiveBatchWorkflow(config)
        
        # Set up initial state
        workflow.molecules = ["existing_molecule"]
        workflow.molecule_smiles_map = {"existing_molecule": "CC"}
        workflow._validation_completed = True
        
        # Mock questionary selection
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask.return_value = "test.txt"
            
            # Test the file import
            workflow._add_from_another_list()
            
            # Verify validation state was reset
            assert not workflow._validation_completed
            assert workflow.molecule_smiles_map == {}
            assert len(workflow.molecules) == 3  # existing + 2 new

    def test_end_to_end_workflow_simulation(self, tmp_path):
        """Test a simulated end-to-end workflow."""
        # Set up temporary directories
        lists_dir = tmp_path / "lists"
        lists_dir.mkdir()
        repo_dir = tmp_path / "repository"
        repo_dir.mkdir()
        
        config = {
            'general_settings': {'lists_directory': str(lists_dir)},
            'repository_base_path': str(repo_dir),
            'database': {'pm7_db_path': str(tmp_path / 'thermo_pm7.csv')},
            'executables': {'crest': 'crest', 'mopac': 'mopac', 'obabel': 'obabel'}
        }
        
        workflow = InteractiveBatchWorkflow(config)
        
        # Simulate adding molecules
        workflow.molecules = ["ethanol", "methanol", "butanol"]
        
        # Mock successful SMILES conversion
        with patch.object(workflow, '_convert_molecules_to_smiles', return_value=True):
            # Mock no database duplicates
            with patch.object(workflow, '_validate_database_duplicates', return_value=True):
                # Mock all found in PubChem
                with patch.object(workflow, '_validate_pubchem_availability', return_value=True):
                    
                    result = workflow._validation_steps()
                    
                    assert result is True
                    assert len(workflow.molecules) == 3


# Test fixtures for pytest
@pytest.fixture
def mock_questionary_interactions():
    """Mock common questionary interactions."""
    with patch('questionary.select') as mock_select:
        with patch('questionary.checkbox') as mock_checkbox:
            with patch('questionary.text') as mock_text:
                with patch('questionary.confirm') as mock_confirm:
                    yield {
                        'select': mock_select,
                        'checkbox': mock_checkbox,
                        'text': mock_text,
                        'confirm': mock_confirm
                    }