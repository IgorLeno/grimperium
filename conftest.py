"""
Global pytest configuration and fixtures for Grimperium test suite.

This module provides shared fixtures and configuration for all tests,
including CI environment setup and external dependency mocking.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest


def pytest_configure(config):
    """Configure pytest with custom markers and CI-specific settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external dependencies"
    )
    config.addinivalue_line(
        "markers", "mock: marks tests that use mocking extensively"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that interact with database files"
    )
    config.addinivalue_line(
        "markers", "config: marks tests related to configuration management"
    )
    config.addinivalue_line(
        "markers", "pipeline: marks tests for the processing pipeline"
    )
    config.addinivalue_line(
        "markers", "pubchem: marks tests that interact with PubChem API (requires network)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test characteristics."""
    for item in items:
        # Mark tests that use external dependencies
        if "pubchem" in item.nodeid.lower() or hasattr(item, 'fixturenames') and 'mock_pubchem' in item.fixturenames:
            item.add_marker(pytest.mark.pubchem)
        
        # Mark database tests
        if "database" in item.nodeid.lower():
            item.add_marker(pytest.mark.database)
        
        # Mark pipeline tests
        if "pipeline" in item.nodeid.lower():
            item.add_marker(pytest.mark.pipeline)
        
        # Mark config tests
        if "config" in item.nodeid.lower():
            item.add_marker(pytest.mark.config)


@pytest.fixture(scope="session")
def ci_environment():
    """Detect if running in CI environment and provide CI-specific configuration."""
    ci_indicators = [
        "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", 
        "TRAVIS", "JENKINS_URL", "BUILD_NUMBER"
    ]
    
    is_ci = any(os.getenv(indicator) for indicator in ci_indicators)
    
    return {
        "is_ci": is_ci,
        "github_actions": bool(os.getenv("GITHUB_ACTIONS")),
        "runner_os": os.getenv("RUNNER_OS", "unknown"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "temp_dir": tempfile.gettempdir(),
    }


@pytest.fixture(scope="session")
def mock_external_executables():
    """Mock external chemistry software executables for CI environments."""
    return {
        "crest": "echo",  # Mock CREST with echo command
        "mopac": "echo",  # Mock MOPAC with echo command  
        "obabel": "echo",  # Mock OpenBabel with echo command
    }


@pytest.fixture
def temp_config(tmp_path, mock_external_executables):
    """Create a temporary configuration file for testing."""
    config_content = f"""
external_programs:
  crest:
    executable: "{mock_external_executables['crest']}"
    timeout: 300
  mopac:
    executable: "{mock_external_executables['mopac']}"
    timeout: 600
  obabel:
    executable: "{mock_external_executables['obabel']}"

database:
  main_db: "{tmp_path}/test_database.csv"

logging:
  level: "DEBUG"
  file: "{tmp_path}/test_grim_details.log"

directories:
  repository: "{tmp_path}/repository"
  data: "{tmp_path}/data"
  logs: "{tmp_path}/logs"
"""
    
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    
    # Create necessary directories
    (tmp_path / "repository").mkdir(exist_ok=True)
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "logs").mkdir(exist_ok=True)
    
    return str(config_file)


@pytest.fixture
def mock_subprocess_for_ci(monkeypatch):
    """Mock subprocess calls for CI environment compatibility."""
    import subprocess
    
    def mock_run(*args, **kwargs):
        """Mock subprocess.run for CI environments."""
        cmd = args[0] if args else kwargs.get('args', [])
        if isinstance(cmd, str):
            cmd = [cmd]
        
        # Mock chemistry software calls
        if any(prog in ' '.join(cmd) for prog in ['crest', 'mopac', 'obabel']):
            return MagicMock(
                returncode=0,
                stdout="Mocked output",
                stderr="",
                args=cmd
            )
        
        # Allow actual system calls for basic commands
        return subprocess.run(*args, **kwargs)
    
    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def setup_test_environment(tmp_path, monkeypatch, ci_environment):
    """Set up test environment for each test (not auto-used to avoid conflicts)."""
    # Set up temporary directories - only when explicitly used
    test_data_dir = tmp_path / "data"
    test_logs_dir = tmp_path / "logs" 
    test_repo_dir = tmp_path / "repository"
    
    test_data_dir.mkdir(exist_ok=True)
    test_logs_dir.mkdir(exist_ok=True)
    test_repo_dir.mkdir(exist_ok=True)
    
    # Set environment variables for testing
    monkeypatch.setenv("GRIMPERIUM_TEST_MODE", "1")
    monkeypatch.setenv("GRIMPERIUM_DATA_DIR", str(test_data_dir))
    monkeypatch.setenv("GRIMPERIUM_LOGS_DIR", str(test_logs_dir))
    monkeypatch.setenv("GRIMPERIUM_REPO_DIR", str(test_repo_dir))
    
    return {
        "data_dir": test_data_dir,
        "logs_dir": test_logs_dir,
        "repo_dir": test_repo_dir
    }


@pytest.fixture(autouse=True)
def setup_ci_mocks(monkeypatch, ci_environment):
    """Automatically set up CI-specific mocks without directory conflicts."""
    # Mock network calls in CI
    if ci_environment["is_ci"]:
        # Mock PubChem API calls
        try:
            import pubchempy as pcp
            def mock_get_compounds(*args, **kwargs):
                """Mock PubChem API calls for CI."""
                mock_compound = MagicMock()
                mock_compound.isomeric_smiles = "CCO"  # Ethanol SMILES
                mock_compound.molecular_formula = "C2H6O"
                mock_compound.molecular_weight = 46.07
                return [mock_compound]
            
            monkeypatch.setattr(pcp, "get_compounds", mock_get_compounds)
        except ImportError:
            pass  # pubchempy not available, skip mocking


def pytest_report_header(config):
    """Add custom header information to pytest report."""
    ci_info = []
    
    if os.getenv("GITHUB_ACTIONS"):
        ci_info.append(f"GitHub Actions: {os.getenv('GITHUB_WORKFLOW', 'unknown')}")
        ci_info.append(f"Runner OS: {os.getenv('RUNNER_OS', 'unknown')}")
        ci_info.append(f"Python: {os.getenv('pythonLocation', 'system')}")
    
    if os.getenv("CI"):
        ci_info.append("CI Environment: Detected")
    
    return ci_info


def pytest_sessionstart(session):
    """Actions to perform at the start of test session."""
    # Ensure required directories exist
    required_dirs = ["data", "logs", "repository"]
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    """Actions to perform at the end of test session."""
    # Clean up any temporary files if needed
    pass