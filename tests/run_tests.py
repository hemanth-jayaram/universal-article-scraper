#!/usr/bin/env python3
"""
Simple test runner for the Homepage Article Scraper tests.

Usage:
    python tests/run_tests.py
    python tests/run_tests.py --verbose
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
except ImportError:
    print("❌ pytest not installed. Install with: pip install pytest")
    sys.exit(1)


def main():
    """Run the test suite."""
    parser = argparse.ArgumentParser(description="Run Homepage Article Scraper tests")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage')
    args = parser.parse_args()
    
    test_dir = Path(__file__).parent
    
    # Build pytest arguments
    pytest_args = [str(test_dir)]
    
    if args.verbose:
        pytest_args.append('-v')
    
    if args.coverage:
        pytest_args.extend(['--cov=scraper', '--cov-report=term-missing'])
    
    # Add some default options for better output
    pytest_args.extend([
        '--tb=short',  # Shorter traceback format
        '--strict-markers',  # Be strict about markers
        '-ra'  # Show short summary of all results except passed
    ])
    
    print("🧪 Running Homepage Article Scraper tests...")
    print(f"📁 Test directory: {test_dir}")
    print(f"🔧 Arguments: {' '.join(pytest_args)}")
    print("")
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("")
        print("✅ All tests passed!")
    else:
        print("")
        print("❌ Some tests failed.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
