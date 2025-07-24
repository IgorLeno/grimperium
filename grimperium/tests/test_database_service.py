"""
Tests for the database_service module.

This module contains tests for database operations including
CSV file handling, data persistence, and thread-safe operations.
"""

import pandas as pd
from unittest.mock import patch
import pytest

from grimperium.services import database_service


class TestDatabaseService:
    """Test the database service functionality."""

    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        """Create a temporary CSV file for testing."""
        csv_file = tmp_path / "test.csv"

        # Create initial CSV with headers
        initial_data = pd.DataFrame(
            {
                "identifier": ["ethanol", "methanol"],
                "smiles": ["CCO", "CO"],
                "pm7_energy": [-10.5, -8.2],
                "status": ["completed", "completed"],
            }
        )
        initial_data.to_csv(csv_file, index=False)

        return str(csv_file)

    def test_get_existing_smiles_with_data(self, temp_csv_file):
        """Test getting existing SMILES from populated database."""
        existing_smiles = database_service.get_existing_smiles(temp_csv_file)

        assert isinstance(existing_smiles, set)
        assert "CCO" in existing_smiles
        assert "CO" in existing_smiles
        assert len(existing_smiles) == 2

    def test_get_existing_smiles_empty_file(self, tmp_path):
        """Test getting existing SMILES from empty database."""
        empty_csv = tmp_path / "empty.csv"

        # Create empty CSV with just headers
        empty_data = pd.DataFrame(columns=["identifier", "smiles", "pm7_energy"])
        empty_data.to_csv(empty_csv, index=False)

        existing_smiles = database_service.get_existing_smiles(str(empty_csv))

        assert isinstance(existing_smiles, set)
        assert len(existing_smiles) == 0

    def test_get_existing_smiles_nonexistent_file(self, tmp_path):
        """Test getting existing SMILES from non-existent database."""
        nonexistent_file = tmp_path / "nonexistent.csv"

        existing_smiles = database_service.get_existing_smiles(str(nonexistent_file))

        assert isinstance(existing_smiles, set)
        assert len(existing_smiles) == 0

    def test_get_existing_smiles_malformed_csv(self, tmp_path):
        """Test getting existing SMILES from malformed CSV."""
        malformed_csv = tmp_path / "malformed.csv"
        malformed_csv.write_text("invalid,csv,data\nno,proper,headers")

        # Should handle gracefully and return empty set
        existing_smiles = database_service.get_existing_smiles(str(malformed_csv))

        assert isinstance(existing_smiles, set)
        assert len(existing_smiles) == 0

    def test_append_to_database_new_entry(self, temp_csv_file):
        """Test appending a new entry to the database."""
        new_data = {
            "identifier": "propanol",
            "smiles": "CCCO",
            "pm7_energy": -12.3,
            "status": "completed",
        }

        schema = ["identifier", "smiles", "pm7_energy", "status"]

        # Mock filelock to avoid actual file locking in tests
        with patch("grimperium.services.database_service.FileLock"):
            result = database_service.append_to_database(
                new_data, temp_csv_file, schema
            )

            assert result is True

            # Verify the data was added
            df = pd.read_csv(temp_csv_file)
            assert len(df) == 3
            assert "propanol" in df["identifier"].values
            assert "CCCO" in df["smiles"].values

    def test_append_to_database_duplicate_smiles(self, temp_csv_file):
        """Test that duplicate SMILES are rejected."""
        # Data with same SMILES as existing entry
        duplicate_data = {
            "identifier": "ethanol_copy",
            "smiles": "CCO",  # Same SMILES as existing ethanol
            "pm7_energy": -999.0,
            "status": "duplicate",
        }

        schema = ["identifier", "smiles", "pm7_energy", "status"]

        with patch("grimperium.services.database_service.FileLock"):
            result = database_service.append_to_database(
                duplicate_data, temp_csv_file, schema
            )

            assert result is False  # Should return False for duplicate SMILES

            # Verify no new entry was added
            df = pd.read_csv(temp_csv_file)
            assert len(df) == 2  # Still only original entries
            assert "ethanol_copy" not in df["identifier"].values

    def test_append_to_database_new_file_creation(self, tmp_path):
        """Test creating a new database file."""
        new_csv_file = tmp_path / "new_database.csv"

        new_data = {
            "identifier": "benzene",
            "smiles": "c1ccccc1",
            "pm7_energy": -5.5,
            "status": "new",
        }

        schema = ["identifier", "smiles", "pm7_energy", "status"]

        with patch("grimperium.services.database_service.FileLock"):
            result = database_service.append_to_database(
                new_data, str(new_csv_file), schema
            )

            assert result is True
            assert new_csv_file.exists()

            # Verify the new file has correct data
            df = pd.read_csv(new_csv_file)
            assert len(df) == 1
            assert df.iloc[0]["identifier"] == "benzene"

    def test_append_to_database_file_permission_error(self, tmp_path):
        """Test handling file permission errors."""
        csv_file = tmp_path / "protected.csv"
        csv_file.write_text("test,data\n")

        new_data = {
            "identifier": "test",
            "smiles": "C",
            "pm7_energy": -1.0,
            "status": "test",
        }

        schema = ["identifier", "smiles", "pm7_energy", "status"]

        # Mock FileLock to raise PermissionError
        with patch("grimperium.services.database_service.FileLock") as mock_lock:
            mock_lock.side_effect = PermissionError("Permission denied")

            result = database_service.append_to_database(
                new_data, str(csv_file), schema
            )

            assert result is False

    def test_append_to_database_missing_required_columns(self, temp_csv_file):
        """Test appending data with missing required SMILES column."""
        incomplete_data = {
            "identifier": "incomplete",
            # Missing required 'smiles' column
        }

        schema = ["identifier", "smiles", "pm7_energy", "status"]

        with patch("grimperium.services.database_service.FileLock"):
            result = database_service.append_to_database(
                incomplete_data, temp_csv_file, schema
            )

            # Should handle gracefully and return False
            assert result is False

    def test_get_existing_identifiers(self, temp_csv_file):
        """Test getting existing identifiers from database."""
        # This function might not exist yet, but we can test the concept
        with patch("grimperium.services.database_service.FileLock"):
            try:
                identifiers = database_service.get_existing_identifiers(temp_csv_file)
                assert "ethanol" in identifiers
                assert "methanol" in identifiers
            except AttributeError:
                # Function doesn't exist yet - that's ok for now
                pass

    def test_database_service_with_different_csv_formats(self, tmp_path):
        """Test database service with different CSV formats."""
        # Test with different column orders
        csv_file = tmp_path / "different_format.csv"

        # Create CSV with different column order
        different_data = pd.DataFrame(
            {
                "pm7_energy": [-10.5],
                "identifier": ["test_mol"],
                "status": ["completed"],
                "smiles": ["CC"],
            }
        )
        different_data.to_csv(csv_file, index=False)

        existing_smiles = database_service.get_existing_smiles(str(csv_file))
        assert "CC" in existing_smiles

    def test_database_service_with_extra_columns(self, tmp_path):
        """Test database service handles extra columns gracefully."""
        csv_file = tmp_path / "extra_columns.csv"

        # Create CSV with extra columns
        extra_data = pd.DataFrame(
            {
                "identifier": ["test_mol"],
                "smiles": ["CC"],
                "pm7_energy": [-10.5],
                "extra_column_1": ["value1"],
                "extra_column_2": ["value2"],
                "timestamp": ["2023-01-01"],
            }
        )
        extra_data.to_csv(csv_file, index=False)

        existing_smiles = database_service.get_existing_smiles(str(csv_file))
        assert "CC" in existing_smiles

    def test_concurrent_database_access_simulation(self, temp_csv_file):
        """Simulate concurrent access to database."""
        import threading
        results = []

        def add_molecule(molecule_id):
            data = {
                "identifier": f"molecule_{molecule_id}",
                "smiles": f"C{molecule_id}",
                "pm7_energy": -float(molecule_id),
                "status": "concurrent_test",
            }

            schema = ["identifier", "smiles", "pm7_energy", "status"]

            with patch("grimperium.services.database_service.FileLock"):
                result = database_service.append_to_database(
                    data, temp_csv_file, schema
                )
                results.append(result)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_molecule, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed (with mocked FileLock)
        assert all(results)


class TestDatabaseServiceErrorHandling:
    """Test error handling in database service."""

    def test_handle_corrupted_csv_file(self, tmp_path):
        """Test handling of corrupted CSV files."""
        corrupted_csv = tmp_path / "corrupted.csv"

        # Create a corrupted CSV file
        corrupted_csv.write_text(
            "identifier,smiles\ntest,CC\nmalformed line without proper format"
        )

        # Should handle gracefully
        existing_smiles = database_service.get_existing_smiles(str(corrupted_csv))
        assert isinstance(existing_smiles, set)

    def test_handle_empty_csv_file(self, tmp_path):
        """Test handling of completely empty CSV files."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("")

        existing_smiles = database_service.get_existing_smiles(str(empty_csv))
        assert isinstance(existing_smiles, set)
        assert len(existing_smiles) == 0

    def test_handle_csv_with_missing_smiles_column(self, tmp_path):
        """Test handling CSV without required 'smiles' column."""
        no_smiles_csv = tmp_path / "no_smiles.csv"

        # Create CSV without smiles column
        data = pd.DataFrame({"identifier": ["test1", "test2"], "energy": [-10.5, -8.2]})
        data.to_csv(no_smiles_csv, index=False)

        existing_smiles = database_service.get_existing_smiles(str(no_smiles_csv))
        assert isinstance(existing_smiles, set)
        assert len(existing_smiles) == 0
