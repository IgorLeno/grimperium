"""
Startup environment validation utilities for Grimperium.

This module provides comprehensive validation of the execution environment
to prevent runtime errors and provide clear, actionable feedback to users
about configuration issues.
"""

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .subprocess_utils import execute_command, validate_executable_version
from ..constants import REQUIRED_EXECUTABLES, EXECUTABLE_VALIDATION_TIMEOUT


class ValidationResult:
    """Container for validation results with detailed feedback."""
    
    def __init__(self, success: bool, message: str, suggestions: Optional[List[str]] = None):
        self.success = success
        self.message = message
        self.suggestions = suggestions or []


class StartupValidator:
    """
    Comprehensive startup environment validator.
    
    This class provides systematic validation of the execution environment
    including virtual environments, external tools, and configuration.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the startup validator.
        
        Args:
            console: Rich console for formatted output (creates one if None)
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        
    def validate_environment(self, config: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """
        Perform comprehensive environment validation.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (overall_success, list_of_validation_results)
        """
        results = []
        overall_success = True
        
        # 1. Virtual Environment Check
        venv_result = self._validate_virtual_environment()
        results.append(venv_result)
        if not venv_result.success:
            overall_success = False
            
        # 2. Python Dependencies Check
        deps_result = self._validate_python_dependencies()
        results.append(deps_result)
        if not deps_result.success:
            overall_success = False
            
        # 3. External Tools Check
        tools_result = self._validate_external_tools(config)
        results.append(tools_result)
        if not tools_result.success:
            overall_success = False
            
        # 4. Directory Permissions Check
        dirs_result = self._validate_directory_permissions(config)
        results.append(dirs_result)
        if not dirs_result.success:
            overall_success = False
            
        return overall_success, results
    
    def _validate_virtual_environment(self) -> ValidationResult:
        """
        Validate that Python is running in a virtual environment.
        
        Returns:
            ValidationResult with virtual environment status
        """
        try:
            # Check for conda environment
            conda_env = os.environ.get('CONDA_DEFAULT_ENV')
            if conda_env:
                return ValidationResult(
                    success=True,
                    message=f"✅ Running in Conda environment: {conda_env}"
                )
            
            # Check for other virtual environments
            venv_indicators = [
                ('VIRTUAL_ENV', 'Virtual Environment'),
                ('PIPENV_ACTIVE', 'Pipenv Environment'),
                ('POETRY_ACTIVE', 'Poetry Environment')
            ]
            
            for env_var, env_type in venv_indicators:
                if os.environ.get(env_var):
                    env_path = os.environ.get(env_var, 'active')
                    return ValidationResult(
                        success=True,
                        message=f"✅ Running in {env_type}: {env_path}"
                    )
            
            # Check if we're in a venv by looking at sys.prefix
            if sys.prefix != sys.base_prefix:
                return ValidationResult(
                    success=True,
                    message=f"✅ Running in virtual environment: {sys.prefix}"
                )
            
            # No virtual environment detected
            return ValidationResult(
                success=False,
                message="❌ No virtual environment detected",
                suggestions=[
                    "Activate your Conda environment: conda activate grimperium",
                    "Or create a new environment: conda create -n grimperium python=3.9",
                    "Alternative: Use Python venv: python -m venv grimperium && source grimperium/bin/activate",
                    "Ensure all dependencies are installed in the virtual environment"
                ]
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"❌ Error checking virtual environment: {e}",
                suggestions=["Please check your Python environment configuration"]
            )
    
    def _validate_python_dependencies(self) -> ValidationResult:
        """
        Validate that required Python packages are installed.
        
        Returns:
            ValidationResult with dependency status
        """
        required_packages = [
            'pandas', 'typer', 'rich', 'pydantic', 'pyyaml', 'requests',
            'questionary', 'pubchempy', 'filelock'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            return ValidationResult(
                success=True,
                message=f"✅ All {len(required_packages)} Python dependencies are installed"
            )
        
        return ValidationResult(
            success=False,
            message=f"❌ Missing {len(missing_packages)} Python packages: {', '.join(missing_packages)}",
            suggestions=[
                "Install missing packages: pip install " + " ".join(missing_packages),
                "Or install all requirements: pip install -r requirements.txt",
                "Ensure you're in the correct virtual environment"
            ]
        )
    
    def _validate_external_tools(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate that external computational chemistry tools are available.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ValidationResult with external tools status
        """
        executables = config.get('executables', {})
        
        if not executables:
            return ValidationResult(
                success=False,
                message="❌ No executables configuration found",
                suggestions=["Check your config.yaml file for executables section"]
            )
        
        missing_tools = []
        tool_details = []
        
        for tool_name in REQUIRED_EXECUTABLES:
            if tool_name not in executables:
                missing_tools.append(f"{tool_name} (not configured)")
                continue
                
            tool_path = executables[tool_name]
            
            # Check if tool exists in PATH or as absolute path
            if not shutil.which(tool_path) and not Path(tool_path).exists():
                missing_tools.append(f"{tool_name} ({tool_path})")
                continue
            
            # Try to validate tool works
            version_info = self._get_tool_version(tool_name, tool_path)
            if version_info:
                tool_details.append(f"{tool_name}: {version_info}")
            else:
                missing_tools.append(f"{tool_name} (not working)")
        
        if not missing_tools:
            return ValidationResult(
                success=True,
                message=f"✅ All external tools available:\n  " + "\n  ".join(tool_details)
            )
        
        suggestions = [
            "Install missing computational chemistry tools:",
        ]
        
        for tool in missing_tools:
            if 'crest' in tool.lower():
                suggestions.extend([
                    "  • CREST: Download from https://github.com/crest-lab/crest",
                    "    Or install via conda: conda install -c conda-forge crest"
                ])
            elif 'mopac' in tool.lower():
                suggestions.extend([
                    "  • MOPAC: Download from http://openmopac.net/",
                    "    Ensure MOPAC is in your PATH or configure absolute path in config.yaml"
                ])
            elif 'obabel' in tool.lower():
                suggestions.extend([
                    "  • OpenBabel: Install via conda: conda install -c conda-forge openbabel",
                    "    Or via package manager: apt-get install openbabel-gui (Ubuntu)"
                ])
        
        suggestions.append("Update config.yaml with correct executable paths if needed")
        
        return ValidationResult(
            success=False,
            message=f"❌ Missing or non-functional tools: {', '.join(missing_tools)}",
            suggestions=suggestions
        )
    
    def _validate_directory_permissions(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate that required directories can be created and are writable.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ValidationResult with directory permissions status
        """
        try:
            directories_to_check = []
            
            # Repository directory
            repo_path = config.get('repository_base_path', 'repository')
            directories_to_check.append(('Repository', repo_path))
            
            # Database directories
            if 'database' in config:
                for db_name, db_path in config['database'].items():
                    db_dir = Path(db_path).parent
                    directories_to_check.append((f'Database ({db_name})', str(db_dir)))
            
            # Logs directory
            if 'logging' in config and 'log_file' in config['logging']:
                log_dir = Path(config['logging']['log_file']).parent
                directories_to_check.append(('Logs', str(log_dir)))
            
            permission_issues = []
            
            for dir_name, dir_path in directories_to_check:
                try:
                    dir_obj = Path(dir_path)
                    
                    # Try to create directory if it doesn't exist
                    dir_obj.mkdir(parents=True, exist_ok=True)
                    
                    # Test write permissions
                    test_file = dir_obj / '.grimperium_write_test'
                    test_file.write_text('test')
                    test_file.unlink()
                    
                except Exception as e:
                    permission_issues.append(f"{dir_name}: {dir_path} - {str(e)}")
            
            if not permission_issues:
                return ValidationResult(
                    success=True,
                    message=f"✅ All {len(directories_to_check)} required directories are accessible"
                )
            
            return ValidationResult(
                success=False,
                message=f"❌ Directory permission issues:\n  " + "\n  ".join(permission_issues),
                suggestions=[
                    "Check file system permissions for the problematic directories",
                    "Ensure you have write access to the project directory",
                    "Consider running with appropriate user permissions",
                    "Check if directories are on a read-only file system"
                ]
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"❌ Error checking directory permissions: {e}",
                suggestions=["Please check your file system permissions"]
            )
    
    def _get_tool_version(self, tool_name: str, tool_path: str) -> Optional[str]:
        """
        Get version information for a computational chemistry tool.
        
        Args:
            tool_name: Name of the tool (crest, mopac, obabel)
            tool_path: Path to the tool executable
            
        Returns:
            Version string if successful, None otherwise
        """
        try:
            if tool_name == 'crest':
                result = execute_command(
                    [tool_path, '--version'], 
                    timeout=EXECUTABLE_VALIDATION_TIMEOUT
                )
                if result.success:
                    # Extract version from CREST output
                    for line in result.stdout.split('\n'):
                        if 'version' in line.lower() or 'crest' in line.lower():
                            return line.strip()
                    return "Available"
                    
            elif tool_name == 'mopac':
                result = execute_command(
                    [tool_path], 
                    timeout=EXECUTABLE_VALIDATION_TIMEOUT
                )
                # MOPAC returns info even on "error" exit
                output = result.stdout + result.stderr
                for line in output.split('\n'):
                    if 'mopac' in line.lower() and ('version' in line.lower() or 'v' in line.lower()):
                        return line.strip()
                return "Available"
                
            elif tool_name == 'obabel':
                result = execute_command(
                    [tool_path, '--version'], 
                    timeout=EXECUTABLE_VALIDATION_TIMEOUT
                )
                if result.success:
                    for line in result.stdout.split('\n'):
                        if 'open babel' in line.lower():
                            return line.strip()
                    return "Available"
            
            return None
            
        except Exception:
            return None
    
    def display_validation_results(self, results: List[ValidationResult], 
                                  show_suggestions: bool = True) -> None:
        """
        Display validation results in a formatted table.
        
        Args:
            results: List of validation results
            show_suggestions: Whether to show suggestions for failed validations
        """
        # Create main results table
        table = Table(title="🔍 Grimperium Environment Validation Report")
        table.add_column("Check", style="bold", width=25)
        table.add_column("Status", justify="center", width=60)
        
        for result in results:
            table.add_row(
                result.message.split(':')[0].replace('✅', '').replace('❌', '').strip(),
                result.message
            )
        
        self.console.print(table)
        
        # Show suggestions for failed validations
        if show_suggestions:
            failed_results = [r for r in results if not r.success and r.suggestions]
            
            if failed_results:
                self.console.print("\n")
                suggestion_panel = []
                
                for result in failed_results:
                    suggestion_panel.append(f"[red]{result.message}[/red]")
                    for suggestion in result.suggestions:
                        suggestion_panel.append(f"  [yellow]→[/yellow] {suggestion}")
                    suggestion_panel.append("")
                
                self.console.print(Panel(
                    "\n".join(suggestion_panel[:-1]),  # Remove last empty line
                    title="[bold red]🚨 Action Required[/bold red]",
                    border_style="red",
                    padding=(1, 2)
                ))


def validate_startup_environment(config: Dict[str, Any], 
                               console: Optional[Console] = None) -> bool:
    """
    Convenience function to validate startup environment.
    
    Args:
        config: Configuration dictionary
        console: Rich console for output
        
    Returns:
        True if all validations pass, False otherwise
    """
    validator = StartupValidator(console)
    success, results = validator.validate_environment(config)
    
    # Always display results
    validator.display_validation_results(results, show_suggestions=not success)
    
    return success