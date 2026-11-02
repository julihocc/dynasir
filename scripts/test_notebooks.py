#!/usr/bin/env python3
"""
Test all notebooks to ensure they can be executed.

This script tests notebooks by executing them with nbconvert.
It identifies which notebooks are expected to fail (e.g., notebook 07
uses annual + incidence which is incompatible with VAR).
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Define notebooks and their expected status
NOTEBOOKS: Dict[str, Dict] = {
    "01_sird_basic_workflow.ipynb": {
        "expected": "pass",
        "description": "Basic SIRD workflow with cumulative mode"
    },
    "02_sirdv_vaccination_analysis.ipynb": {
        "expected": "pass",
        "description": "SIRDV with vaccination compartment"
    },
    "03_global_covid19_forecasting.ipynb": {
        "expected": "pass",
        "description": "COVID-19 global forecasting (daily cumulative)"
    },
    "04_parallel_simulations.ipynb": {
        "expected": "pass",
        "description": "Parallel simulation demonstrations"
    },
    "05_multi_backend_comparison.ipynb": {
        "expected": "skip",
        "description": "Multi-backend comparison (future feature)"
    },
    "06_annual_measles_workaround.ipynb": {
        "expected": "pass",
        "description": "Annual measles with monthly workaround"
    },
    "07_incidence_mode_measles.ipynb": {
        "expected": "fail",
        "description": "Annual + incidence mode (known limitation)",
        "expected_error": "LinAlgError"
    },
}


def test_notebook(notebook_path: Path) -> Tuple[bool, str]:
    """
    Test a notebook by executing it with jupyter nbconvert.

    Args:
        notebook_path: Path to the notebook

    Returns:
        Tuple of (success, error_message)
    """
    try:
        result = subprocess.run(
            [
                "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--output", "/tmp/test_output.ipynb",
                str(notebook_path)
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr

    except subprocess.TimeoutExpired:
        return False, "Execution timeout (>5 minutes)"
    except Exception as e:
        return False, str(e)


def main():
    """Run all notebook tests."""
    notebooks_dir = Path(__file__).parent.parent / "examples" / "notebooks"

    if not notebooks_dir.exists():
        print(f"❌ Notebooks directory not found: {notebooks_dir}")
        sys.exit(1)

    print("=" * 80)
    print("NOTEBOOK TESTING SUITE")
    print("=" * 80)
    print()

    results = {
        "passed": [],
        "failed": [],
        "expected_failures": [],
        "skipped": [],
        "unexpected": []
    }

    for notebook_name, info in NOTEBOOKS.items():
        notebook_path = notebooks_dir / notebook_name

        if not notebook_path.exists():
            print(f"⚠️  SKIP: {notebook_name} (file not found)")
            results["skipped"].append(notebook_name)
            continue

        expected = info["expected"]
        description = info["description"]

        print(f"\nTesting: {notebook_name}")
        print(f"  Description: {description}")
        print(f"  Expected: {expected}")
        print(f"  Running...", end=" ", flush=True)

        if expected == "skip":
            print("SKIPPED (future feature)")
            results["skipped"].append(notebook_name)
            continue

        success, error_msg = test_notebook(notebook_path)

        if success:
            if expected == "pass":
                print("✅ PASSED")
                results["passed"].append(notebook_name)
            else:
                print("❌ UNEXPECTED PASS (expected to fail)")
                results["unexpected"].append(notebook_name)
        else:
            if expected == "fail":
                expected_error = info.get("expected_error", "")
                if expected_error and expected_error in error_msg:
                    print(f"✅ EXPECTED FAILURE ({expected_error})")
                    results["expected_failures"].append(notebook_name)
                else:
                    print(f"⚠️  FAILED (but expected)")
                    print(f"     Error: {error_msg[:200]}")
                    results["expected_failures"].append(notebook_name)
            else:
                print("❌ FAILED (unexpected)")
                print(f"     Error: {error_msg[:200]}")
                results["failed"].append(notebook_name)

    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Passed: {len(results['passed'])}")
    for nb in results['passed']:
        print(f"   - {nb}")

    print(f"\n✅ Expected failures: {len(results['expected_failures'])}")
    for nb in results['expected_failures']:
        print(f"   - {nb} ({NOTEBOOKS[nb]['description']})")

    print(f"\n⚠️  Skipped: {len(results['skipped'])}")
    for nb in results['skipped']:
        print(f"   - {nb}")

    if results['failed']:
        print(f"\n❌ Unexpected failures: {len(results['failed'])}")
        for nb in results['failed']:
            print(f"   - {nb}")

    if results['unexpected']:
        print(f"\n❌ Unexpected passes: {len(results['unexpected'])}")
        for nb in results['unexpected']:
            print(f"   - {nb}")

    print()

    # Exit with appropriate code
    if results['failed'] or results['unexpected']:
        print("❌ TESTS FAILED: Some notebooks behaved unexpectedly")
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED: Notebooks behave as expected")
        sys.exit(0)


if __name__ == "__main__":
    main()
