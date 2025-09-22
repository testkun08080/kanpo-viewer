#!/usr/bin/env python3
"""
Pre-deployment test runner for Kanpo PDF API

Usage:
    python api/tests/run_tests.py              # Run all tests
    python api/tests/run_tests.py --unit       # Run unit tests only
    python api/tests/run_tests.py --integration # Run integration tests only
    python api/tests/run_tests.py --deployment # Run deployment readiness tests only
    python api/tests/run_tests.py --quick      # Run quick tests only (no integration)
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()

    duration = end_time - start_time

    if result.returncode == 0:
        print(f"✅ {description} - Passed ({duration:.2f}s)")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
    else:
        print(f"❌ {description} - Failed ({duration:.2f}s)")
        if result.stderr.strip():
            print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")

    return result.returncode == 0

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    try:
        import pytest
        import fastapi
        import pydantic
        print("✅ All required dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies with: uv sync")
        return False

def run_tests(test_type="all"):
    """Run the specified test suite"""

    if not check_dependencies():
        return False

    base_cmd = ["python", "-m", "pytest", "-v"]

    # Change to the correct directory
    os.chdir(Path(__file__).parent.parent)

    test_configs = {
        "unit": {
            "path": "tests/unit/",
            "description": "Unit Tests",
            "markers": []
        },
        "integration": {
            "path": "tests/integration/",
            "description": "Integration Tests",
            "markers": ["-m", "integration"]
        },
        "deployment": {
            "path": "tests/test_deployment_readiness.py",
            "description": "Deployment Readiness Tests",
            "markers": []
        },
        "quick": {
            "path": "tests/",
            "description": "Quick Tests (No Integration)",
            "markers": ["-m", "not integration"]
        },
        "all": {
            "path": "tests/",
            "description": "All Tests",
            "markers": []
        }
    }

    if test_type not in test_configs:
        print(f"❌ Unknown test type: {test_type}")
        return False

    config = test_configs[test_type]
    cmd = base_cmd + config["markers"] + [config["path"]]

    print(f"\n🧪 Running {config['description']}")
    print("=" * 50)

    return run_command(cmd, config["description"])

def run_linting():
    """Run code linting and formatting checks"""
    print("\n🔍 Running Code Quality Checks")
    print("=" * 50)

    # Check if files exist
    app_dir = Path(__file__).parent.parent / "app"
    if not app_dir.exists():
        print("❌ App directory not found")
        return False

    # Simple syntax check
    python_files = list(app_dir.rglob("*.py"))
    syntax_errors = []

    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
        except SyntaxError as e:
            syntax_errors.append(f"{py_file}: {e}")

    if syntax_errors:
        print("❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"  {error}")
        return False
    else:
        print("✅ No syntax errors found")
        return True

def validate_api_structure():
    """Validate API structure and imports"""
    print("\n🏗️ Validating API Structure")
    print("=" * 50)

    try:
        from app.main import app
        from app.services.simple_pdf_service import SimplePdfDownloadService
        from app.schemas.pdf import PdfDownloadRequest

        print("✅ All main modules import successfully")

        # Check if routes are registered
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"🔍 Found routes: {route_paths}")

        expected_routes = ["/", "/pdf/download", "/pdf/health"]

        missing_routes = []
        for expected in expected_routes:
            if not any(expected in path for path in route_paths):
                missing_routes.append(expected)

        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        else:
            print("✅ All expected routes found")
            return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def run_manual_api_test():
    """Run manual API test (equivalent to the old test_pdf_api.py)"""
    print("\n🧪 Manual API Test (Live Server)")
    print("=" * 50)

    try:
        import requests

        api_base_url = "http://localhost:8000/api/pdf"
        test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

        # Test health endpoint
        print("🏥 Testing health endpoint...")
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint OK")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect - API server not running")
            print("💡 Start with: uv run uvicorn api.app.main:app --reload --port 8000")
            return False

        # Test download endpoint
        print("📥 Testing download endpoint...")
        test_request = {
            "url": test_url,
            "filename": "manual_test.pdf"
        }

        response = requests.post(
            f"{api_base_url}/download",
            json=test_request,
            timeout=30
        )

        if response.status_code == 200 and 'pdf' in response.headers.get('content-type', '').lower():
            print(f"✅ Download test OK ({len(response.content)} bytes)")
            return True
        else:
            print(f"❌ Download test failed: {response.status_code}")
            return False

    except ImportError:
        print("❌ requests module not available for manual test")
        return False
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        return False

def generate_test_report():
    """Generate a simple test report"""
    print("\n📊 Test Summary")
    print("=" * 50)

    # Run a quick test count
    try:
        result = subprocess.run([
            "python", "-m", "pytest", "--collect-only", "-q", "tests/"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            test_count = len([line for line in lines if '::test_' in line])
            print(f"📈 Total tests discovered: {test_count}")
        else:
            print("❓ Could not count tests")
    except Exception:
        print("❓ Could not generate test report")

def main():
    parser = argparse.ArgumentParser(description="Pre-deployment test runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--deployment", action="store_true", help="Run deployment readiness tests only")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (no integration)")
    parser.add_argument("--lint", action="store_true", help="Run linting checks only")
    parser.add_argument("--validate", action="store_true", help="Validate API structure only")
    parser.add_argument("--manual", action="store_true", help="Run manual API test (live server required)")

    args = parser.parse_args()

    print("🚀 Kanpo PDF API - Pre-deployment Test Suite")
    print("=" * 60)

    all_passed = True

    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.deployment:
        test_type = "deployment"
    elif args.quick:
        test_type = "quick"
    else:
        test_type = "all"

    # Run validation
    if not args.lint and not args.validate:
        if not validate_api_structure():
            all_passed = False

    # Run linting
    if args.lint or not any([args.unit, args.integration, args.deployment, args.quick, args.validate]):
        if not run_linting():
            all_passed = False

    # Run tests
    if not args.lint and not args.validate:
        if not run_tests(test_type):
            all_passed = False

    # Run structure validation
    if args.validate:
        if not validate_api_structure():
            all_passed = False

    # Run manual API test
    if args.manual:
        if not run_manual_api_test():
            all_passed = False

    # Generate report
    if not args.lint and not args.validate and not args.manual:
        generate_test_report()

    # Final result
    print("\n🎯 Final Result")
    print("=" * 50)

    if all_passed:
        print("✅ All checks passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()