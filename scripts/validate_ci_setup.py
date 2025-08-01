#!/usr/bin/env python3
"""
CI Setup Validation Script for Grimperium v2

This script validates that the testing and coverage configuration is properly
integrated with the GitHub Actions workflow. It performs comprehensive checks
to ensure the CI pipeline will work correctly.

Usage:
    python scripts/validate_ci_setup.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any


class CIValidator:
    """Validates CI setup configuration and compatibility."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def check_required_files(self) -> bool:
        """Check that all required CI configuration files exist."""
        print("✓ Checking required CI configuration files...")
        self.checks_total += 6
        
        required_files = [
            (".github/workflows/ci.yml", "GitHub Actions workflow"),
            ("pytest.ini", "Pytest configuration"),
            ("conftest.py", "Pytest global configuration"),
            ("codecov.yml", "Codecov configuration"),
            ("requirements.txt", "Python dependencies"),
        ]
        
        for file_path, description in required_files:
            if (self.project_root / file_path).exists():
                print(f"  ✓ {description}: {file_path}")
                self.checks_passed += 1
            else:
                self.errors.append(f"Missing {description}: {file_path}")
                print(f"  ✗ {description}: {file_path}")
        
        # Check test directory structure
        test_dir = self.project_root / "grimperium" / "tests"
        if test_dir.exists() and test_dir.is_dir():
            test_files = list(test_dir.glob("test_*.py"))
            if test_files:
                print(f"  ✓ Test files found: {len(test_files)} test files")
                self.checks_passed += 1
            else:
                self.errors.append("No test files found in grimperium/tests/")
                print("  ✗ No test files found")
        else:
            self.errors.append("Test directory grimperium/tests/ not found")
            print("  ✗ Test directory not found")
        
        return len(self.errors) == 0
    
    def check_pytest_configuration(self) -> bool:
        """Validate pytest configuration."""
        print("\n✓ Validating pytest configuration...")
        self.checks_total += 4
        
        # Check pytest installation
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"  ✓ Pytest installed: {result.stdout.strip()}")
            self.checks_passed += 1
        except subprocess.CalledProcessError:
            self.errors.append("Pytest not installed or not working")
            print("  ✗ Pytest not available")
        
        # Check pytest-cov installation
        try:
            subprocess.run([sys.executable, "-c", "import pytest_cov"], 
                          capture_output=True, check=True)
            print("  ✓ pytest-cov available")
            self.checks_passed += 1
        except subprocess.CalledProcessError:
            self.errors.append("pytest-cov not installed")
            print("  ✗ pytest-cov not available")
        
        # Check pytest markers
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--markers"], 
                                  capture_output=True, text=True, check=True, 
                                  cwd=self.project_root)
            
            required_markers = ["slow", "integration", "benchmark", "external", "pubchem"]
            markers_found = [marker for marker in required_markers 
                           if f"@pytest.mark.{marker}" in result.stdout]
            
            if len(markers_found) == len(required_markers):
                print(f"  ✓ All custom markers registered: {', '.join(required_markers)}")
                self.checks_passed += 1
            else:
                missing = set(required_markers) - set(markers_found)
                self.warnings.append(f"Some custom markers not registered: {missing}")
                print(f"  ⚠ Missing markers: {missing}")
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Failed to check pytest markers: {e}")
            print(f"  ✗ Failed to check markers: {e}")
        
        # Test collection
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], 
                                  capture_output=True, text=True, check=True,
                                  cwd=self.project_root)
            
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1] if lines else ""
            
            if "tests collected" in last_line:
                test_count = last_line.split()[0]
                print(f"  ✓ Test collection successful: {test_count} tests found")
                self.checks_passed += 1
            else:
                self.errors.append("Test collection failed or no tests found")
                print("  ✗ Test collection failed")
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Test collection failed: {e}")
            print(f"  ✗ Test collection error: {e}")
        
        return True
    
    def check_coverage_configuration(self) -> bool:
        """Validate coverage configuration."""
        print("\n✓ Validating coverage configuration...")
        self.checks_total += 3
        
        # Check codecov.yml
        codecov_file = self.project_root / "codecov.yml"
        if codecov_file.exists():
            try:
                with open(codecov_file) as f:
                    content = f.read()
                    if "target:" in content and "coverage:" in content:
                        print("  ✓ codecov.yml configuration valid")
                        self.checks_passed += 1
                    else:
                        self.warnings.append("codecov.yml missing target or coverage settings")
                        print("  ⚠ codecov.yml incomplete configuration")
            except Exception as e:
                self.errors.append(f"Failed to read codecov.yml: {e}")
                print(f"  ✗ codecov.yml read error: {e}")
        else:
            self.errors.append("codecov.yml not found")
            print("  ✗ codecov.yml missing")
        
        # Test coverage generation
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "grimperium/tests/test_base_service.py::TestBaseService::test_init_with_service_name",
                "--cov=grimperium", "--cov-report=xml", "--cov-report=term", "-v"
            ], capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.returncode == 0 and "coverage.xml" in str(subprocess.run(
                ["ls", "-la"], capture_output=True, text=True, cwd=self.project_root
            ).stdout):
                print("  ✓ XML coverage report generation works")
                self.checks_passed += 1
            else:
                self.warnings.append("Coverage report generation may have issues")
                print("  ⚠ Coverage generation test failed")
        except subprocess.TimeoutExpired:
            self.warnings.append("Coverage test timed out")
            print("  ⚠ Coverage test timed out")
        except Exception as e:
            self.warnings.append(f"Coverage test error: {e}")
            print(f"  ⚠ Coverage test error: {e}")
        
        # Check for coverage.xml after test
        coverage_file = self.project_root / "coverage.xml"
        if coverage_file.exists():
            print("  ✓ coverage.xml file generated successfully")
            self.checks_passed += 1
        else:
            self.warnings.append("coverage.xml file not generated")
            print("  ⚠ coverage.xml not found")
        
        return True
    
    def check_github_actions_workflow(self) -> bool:
        """Validate GitHub Actions workflow configuration."""
        print("\n✓ Validating GitHub Actions workflow...")
        self.checks_total += 4
        
        workflow_file = self.project_root / ".github" / "workflows" / "ci.yml"
        if not workflow_file.exists():
            self.errors.append("GitHub Actions workflow file not found")
            print("  ✗ ci.yml workflow file missing")
            return False
        
        try:
            with open(workflow_file) as f:
                workflow_content = f.read()
            
            # Check required workflow components
            required_components = [
                "pytest", "coverage", "codecov", "matrix"
            ]
            
            for component in required_components:
                if component in workflow_content.lower():
                    print(f"  ✓ Workflow includes {component}")
                    self.checks_passed += 1
                else:
                    self.warnings.append(f"Workflow may be missing {component}")
                    print(f"  ⚠ Workflow missing {component}")
        
        except Exception as e:
            self.errors.append(f"Failed to read workflow file: {e}")
            print(f"  ✗ Workflow file read error: {e}")
        
        return True
    
    def check_external_dependencies_mocking(self) -> bool:
        """Check that external dependencies are properly mocked."""
        print("\n✓ Checking external dependency mocking...")
        self.checks_total += 3
        
        # Check conftest.py for CI mocks
        conftest_file = self.project_root / "conftest.py"
        if conftest_file.exists():
            try:
                with open(conftest_file) as f:
                    content = f.read()
                
                if "ci_environment" in content and "mock" in content.lower():
                    print("  ✓ CI environment mocking configured")
                    self.checks_passed += 1
                else:
                    self.warnings.append("CI mocking may not be configured")
                    print("  ⚠ CI mocking configuration unclear")
            except Exception as e:
                self.warnings.append(f"Failed to check conftest.py: {e}")
                print(f"  ⚠ conftest.py check error: {e}")
        
        # Check test files for mock usage
        test_files = list((self.project_root / "grimperium" / "tests").glob("test_*.py"))
        mock_usage_count = 0
        
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                    if "mock" in content.lower() or "patch" in content:
                        mock_usage_count += 1
            except Exception:
                pass
        
        if mock_usage_count > 0:
            print(f"  ✓ Mocking used in {mock_usage_count} test files")
            self.checks_passed += 1
        else:
            self.warnings.append("No mocking found in test files")
            print("  ⚠ No mocking detected")
        
        # Check for external program mocking
        external_programs = ["crest", "mopac", "obabel"]
        mocks_found = []
        
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                    for program in external_programs:
                        if program in content.lower():
                            mocks_found.append(program)
            except Exception:
                pass
        
        if mocks_found:
            print(f"  ✓ External programs mocked: {set(mocks_found)}")
            self.checks_passed += 1
        else:
            self.warnings.append("External programs may not be mocked")
            print("  ⚠ External program mocking unclear")
        
        return True
    
    def run_quick_test_validation(self) -> bool:
        """Run a quick test to validate the setup works."""
        print("\n✓ Running quick test validation...")
        self.checks_total += 2
        
        # Set CI environment and run a small subset of tests
        env = os.environ.copy()
        env["CI"] = "true"
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "grimperium/tests/test_base_service.py::TestBaseService::test_init_with_service_name",
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root, 
            env=env, timeout=30)
            
            if result.returncode == 0:
                print("  ✓ Quick CI test passed")
                self.checks_passed += 1
            else:
                self.errors.append(f"Quick CI test failed: {result.stderr}")
                print(f"  ✗ Quick test failed")
        
        except subprocess.TimeoutExpired:
            self.warnings.append("Quick test timed out")
            print("  ⚠ Quick test timed out")
        except Exception as e:
            self.warnings.append(f"Quick test error: {e}")
            print(f"  ⚠ Quick test error: {e}")
        
        # Test with coverage
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "grimperium/tests/test_base_service.py::TestBaseService::test_init_with_service_name",
                "--cov=grimperium", "--cov-report=term", "-v"
            ], capture_output=True, text=True, cwd=self.project_root, 
            env=env, timeout=30)
            
            if result.returncode == 0 and "coverage" in result.stdout.lower():
                print("  ✓ Quick coverage test passed")
                self.checks_passed += 1
            else:
                self.warnings.append("Quick coverage test may have issues")
                print("  ⚠ Quick coverage test unclear")
        
        except Exception as e:
            self.warnings.append(f"Quick coverage test error: {e}")
            print(f"  ⚠ Quick coverage test error: {e}")
        
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        success_rate = (self.checks_passed / self.checks_total * 100) if self.checks_total > 0 else 0
        
        report = {
            "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            "checks_total": self.checks_total,
            "checks_passed": self.checks_passed,
            "success_rate": f"{success_rate:.1f}%",
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "PASS" if len(self.errors) == 0 else "FAIL"
        }
        
        return report
    
    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        print("🧪 Grimperium v2 CI Setup Validation")
        print("=" * 50)
        
        checks = [
            self.check_required_files,
            self.check_pytest_configuration,
            self.check_coverage_configuration,
            self.check_github_actions_workflow,
            self.check_external_dependencies_mocking,
            self.run_quick_test_validation,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Check failed with exception: {e}")
                print(f"  ✗ Check failed: {e}")
        
        # Generate and display report
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("📊 VALIDATION REPORT")
        print("=" * 50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Checks: {report['checks_total']}")
        print(f"Checks Passed: {report['checks_passed']}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"Status: {report['status']}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 All checks passed! CI setup is ready.")
        elif not self.errors:
            print("\n✅ Setup is functional with minor warnings.")
        else:
            print("\n❌ Setup has critical issues that need to be resolved.")
        
        return len(self.errors) == 0


def main():
    """Main validation entry point."""
    validator = CIValidator()
    success = validator.run_all_checks()
    
    # Write report to file
    report = validator.generate_report()
    report_file = validator.project_root / "ci_validation_report.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Failed to save report: {e}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()