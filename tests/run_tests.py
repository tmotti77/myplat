#!/usr/bin/env python3
"""
Test runner script for Hybrid RAG AI Platform
Provides convenient test execution with different configurations
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner with multiple configuration options."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        
    def run_command(self, cmd: List[str], env: Optional[dict] = None) -> int:
        """Run a command and return the exit code."""
        print(f"Running: {' '.join(cmd)}")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env={**os.environ, **(env or {})},
                check=False
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print("-" * 80)
            print(f"Command completed in {duration:.2f} seconds with exit code {result.returncode}")
            
            return result.returncode
            
        except KeyboardInterrupt:
            print("\nTest execution interrupted by user")
            return 130
        except Exception as e:
            print(f"Error running command: {e}")
            return 1
    
    def run_unit_tests(self, args: argparse.Namespace) -> int:
        """Run unit tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short"
        ]
        
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        if args.parallel:
            cmd.extend(["-n", "auto"])
        
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        env = {"USE_FAST_TESTS": "true"} if args.fast else {}
        
        return self.run_command(cmd, env)
    
    def run_integration_tests(self, args: argparse.Namespace) -> int:
        """Run integration tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short"
        ]
        
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        # Integration tests need real database
        env = {"USE_FAST_TESTS": "false"}
        
        return self.run_command(cmd, env)
    
    def run_e2e_tests(self, args: argparse.Namespace) -> int:
        """Run end-to-end tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--tb=short",
            "--timeout=300"  # 5 minute timeout for E2E tests
        ]
        
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        # E2E tests need full environment
        env = {
            "USE_FAST_TESTS": "false",
            "E2E_TESTING": "true"
        }
        
        return self.run_command(cmd, env)
    
    def run_all_tests(self, args: argparse.Namespace) -> int:
        """Run all test suites."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short"
        ]
        
        if args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])
        
        if args.parallel and not args.e2e:
            cmd.extend(["-n", "auto"])
        
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        if args.fast:
            cmd.extend(["-m", "not slow and not e2e"])
        
        env = {"USE_FAST_TESTS": "true" if args.fast else "false"}
        
        return self.run_command(cmd, env)
    
    def run_performance_tests(self, args: argparse.Namespace) -> int:
        """Run performance and load tests."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "performance",
            "-v",
            "--tb=short",
            "--benchmark-only"
        ]
        
        return self.run_command(cmd)
    
    def run_security_tests(self, args: argparse.Namespace) -> int:
        """Run security tests."""
        print("Running security tests...")
        
        # Run bandit for security analysis
        bandit_cmd = [
            "bandit", "-r", "src/", 
            "-f", "json", 
            "-o", "security-report.json"
        ]
        
        bandit_result = self.run_command(bandit_cmd)
        
        # Run safety for dependency vulnerabilities
        safety_cmd = ["safety", "check", "--json"]
        safety_result = self.run_command(safety_cmd)
        
        # Run security-focused pytest markers
        pytest_cmd = [
            "python", "-m", "pytest",
            "-m", "security",
            "-v"
        ]
        
        pytest_result = self.run_command(pytest_cmd)
        
        return max(bandit_result, safety_result, pytest_result)
    
    def lint_code(self, args: argparse.Namespace) -> int:
        """Run code linting and formatting checks."""
        print("Running code quality checks...")
        
        commands = [
            # Black formatting check
            ["black", "--check", "--diff", "src/", "tests/"],
            # isort import sorting check
            ["isort", "--check-only", "--diff", "src/", "tests/"],
            # flake8 linting
            ["flake8", "src/", "tests/"],
            # mypy type checking
            ["mypy", "src/"]
        ]
        
        exit_codes = []
        
        for cmd in commands:
            result = self.run_command(cmd)
            exit_codes.append(result)
        
        return max(exit_codes)
    
    def setup_test_environment(self, args: argparse.Namespace) -> int:
        """Set up test environment."""
        print("Setting up test environment...")
        
        # Install test requirements
        install_cmd = [
            "pip", "install", "-r", "tests/test_requirements.txt"
        ]
        
        install_result = self.run_command(install_cmd)
        
        if install_result != 0:
            return install_result
        
        # Set up test database (if using Docker)
        if args.docker:
            docker_cmd = [
                "docker-compose", "-f", "docker-compose.test.yml", "up", "-d",
                "postgres", "redis", "qdrant"
            ]
            
            docker_result = self.run_command(docker_cmd)
            
            if docker_result != 0:
                return docker_result
            
            print("Waiting for services to be ready...")
            time.sleep(10)
        
        print("Test environment setup complete!")
        return 0
    
    def cleanup_test_environment(self, args: argparse.Namespace) -> int:
        """Clean up test environment."""
        print("Cleaning up test environment...")
        
        if args.docker:
            docker_cmd = [
                "docker-compose", "-f", "docker-compose.test.yml", "down", "-v"
            ]
            
            return self.run_command(docker_cmd)
        
        return 0
    
    def generate_test_report(self, args: argparse.Namespace) -> int:
        """Generate comprehensive test report."""
        print("Generating test report...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--html=test-report.html",
            "--self-contained-html",
            "--json-report",
            "--json-report-file=test-report.json",
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "-v"
        ]
        
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        return self.run_command(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for Hybrid RAG AI Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py unit --fast --coverage
  python tests/run_tests.py integration --markers="database and not slow"
  python tests/run_tests.py e2e --docker
  python tests/run_tests.py all --parallel --coverage
  python tests/run_tests.py security
  python tests/run_tests.py lint
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "e2e", "all", 
            "performance", "security", "lint",
            "setup", "cleanup", "report"
        ],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run fast tests only (skip slow tests)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--markers",
        type=str,
        help="Pytest markers to filter tests (e.g., 'unit and not slow')"
    )
    
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Use Docker for test environment"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Set up environment variables
    os.environ["PYTHONPATH"] = str(runner.project_root)
    
    if args.verbose:
        os.environ["PYTEST_VERBOSE"] = "1"
    
    # Route to appropriate test runner
    if args.test_type == "unit":
        exit_code = runner.run_unit_tests(args)
    elif args.test_type == "integration":
        exit_code = runner.run_integration_tests(args)
    elif args.test_type == "e2e":
        exit_code = runner.run_e2e_tests(args)
    elif args.test_type == "all":
        exit_code = runner.run_all_tests(args)
    elif args.test_type == "performance":
        exit_code = runner.run_performance_tests(args)
    elif args.test_type == "security":
        exit_code = runner.run_security_tests(args)
    elif args.test_type == "lint":
        exit_code = runner.lint_code(args)
    elif args.test_type == "setup":
        exit_code = runner.setup_test_environment(args)
    elif args.test_type == "cleanup":
        exit_code = runner.cleanup_test_environment(args)
    elif args.test_type == "report":
        exit_code = runner.generate_test_report(args)
    else:
        print(f"Unknown test type: {args.test_type}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()