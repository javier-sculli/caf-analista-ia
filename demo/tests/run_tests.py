#!/usr/bin/env python3
"""
Test Runner for CAF Analytics Demo
Runs all tests and generates a detailed report
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80 + "\n")


def run_pytest(args=""):
    """Run pytest with given arguments"""
    cmd = f"python3 -m pytest {args}"
    print(f"Running: {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main test runner"""
    print_header("CAF ANALYTICS DEMO - TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not installed!")
        print("\nInstall with: pip install pytest")
        return 1

    # Run different test suites
    test_suites = [
        {
            'name': 'Example Queries',
            'path': 'tests/test_example_queries.py',
            'args': '-v -s'
        },
        {
            'name': 'Visualizations',
            'path': 'tests/test_visualizations.py',
            'args': '-v -s'
        }
    ]

    results = {}

    for suite in test_suites:
        print_header(f"TEST SUITE: {suite['name']}")
        returncode = run_pytest(f"{suite['path']} {suite['args']}")
        results[suite['name']] = returncode == 0

    # Summary
    print_header("FINAL SUMMARY")
    all_passed = True
    for suite_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {suite_name}")
        if not passed:
            all_passed = False

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
