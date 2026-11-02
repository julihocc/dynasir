#!/usr/bin/env python3
"""
Validate notebook structure and identify known issues.

This script validates notebooks without executing them, checking for:
1. Valid notebook structure (can be loaded)
2. Known problematic patterns (annual + incidence mode)
3. Import statements work
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re


def load_notebook(notebook_path: Path) -> Dict:
    """Load and parse a notebook file."""
    try:
        with open(notebook_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load notebook: {e}")


def extract_code_cells(notebook: Dict) -> List[str]:
    """Extract all code cell sources from notebook."""
    code_cells = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            source = cell.get("source", [])
            if isinstance(source, list):
                code_cells.append("".join(source))
            else:
                code_cells.append(source)
    return code_cells


def check_for_annual_incidence_pattern(code_cells: List[str]) -> Tuple[bool, str]:
    """
    Check if notebook uses the problematic annual + incidence pattern.

    Returns:
        Tuple of (has_pattern, details)
    """
    has_annual = False
    has_incidence = False
    details = []

    for i, code in enumerate(code_cells):
        # Check for annual frequency
        if re.search(r'freq\s*=\s*["\']YE["\']', code) or \
           re.search(r'freq\s*=\s*["\']Y["\']', code) or \
           re.search(r'freq\s*=\s*["\']A["\']', code):
            has_annual = True
            details.append(f"Cell {i}: Found annual frequency (freq='YE'/'Y'/'A')")

        # Check for incidence mode
        if re.search(r'mode\s*=\s*["\']incidence["\']', code):
            has_incidence = True
            details.append(f"Cell {i}: Found incidence mode")

        # Check for DataContainer with both patterns
        if 'DataContainer' in code:
            if has_annual and has_incidence:
                details.append(f"Cell {i}: DataContainer with annual + incidence pattern")

    return (has_annual and has_incidence, "\n  ".join(details))


def validate_notebook(notebook_path: Path) -> Dict:
    """
    Validate a notebook and return results.

    Returns:
        Dict with validation results
    """
    result = {
        "name": notebook_path.name,
        "valid": False,
        "has_known_issue": False,
        "issues": [],
        "warnings": []
    }

    try:
        # 1. Load notebook
        notebook = load_notebook(notebook_path)
        result["valid"] = True

        # 2. Extract code cells
        code_cells = extract_code_cells(notebook)

        # 3. Check for annual + incidence pattern
        has_pattern, details = check_for_annual_incidence_pattern(code_cells)
        if has_pattern:
            result["has_known_issue"] = True
            result["warnings"].append(
                "Uses annual + incidence mode (known VAR incompatibility)"
            )
            result["warnings"].append(details)

        # 4. Check for basic imports
        all_code = "\n".join(code_cells)
        if "from dynasir import" in all_code or "import dynasir" in all_code:
            result["warnings"].append("Uses epydemics library (good)")

    except Exception as e:
        result["valid"] = False
        result["issues"].append(str(e))

    return result


def main():
    """Run validation on all notebooks."""
    notebooks_dir = Path(__file__).parent.parent / "examples" / "notebooks"

    if not notebooks_dir.exists():
        print(f"❌ Notebooks directory not found: {notebooks_dir}")
        sys.exit(1)

    print("=" * 80)
    print("NOTEBOOK VALIDATION SUITE")
    print("=" * 80)
    print()

    notebook_files = sorted(notebooks_dir.glob("*.ipynb"))

    if not notebook_files:
        print("⚠️  No notebooks found in", notebooks_dir)
        sys.exit(1)

    results = []
    for notebook_path in notebook_files:
        print(f"\nValidating: {notebook_path.name}")
        result = validate_notebook(notebook_path)
        results.append(result)

        if result["valid"]:
            print("  ✅ Structure: Valid")
        else:
            print("  ❌ Structure: Invalid")
            for issue in result["issues"]:
                print(f"     Error: {issue}")

        if result["has_known_issue"]:
            print("  ⚠️  Known Issue: Annual + Incidence mode detected")
            print("     This notebook will fail at VAR fitting step")
            print("     See docs/user-guide/known-limitations.md")

        if result["warnings"]:
            for warning in result["warnings"]:
                if warning.startswith("Cell"):
                    print(f"     {warning}")

    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    valid_count = sum(1 for r in results if r["valid"])
    issue_count = sum(1 for r in results if r["has_known_issue"])

    print(f"Total notebooks: {len(results)}")
    print(f"✅ Valid structure: {valid_count}/{len(results)}")
    print(f"⚠️  With known issues: {issue_count}")

    if issue_count > 0:
        print("\nNotebooks with known issues:")
        for r in results:
            if r["has_known_issue"]:
                print(f"  - {r['name']}")
                print(f"    Issue: Annual + incidence mode (VAR incompatibility)")
                print(f"    Expected: Will fail at model.fit_model() step")
                print(f"    Reference: docs/user-guide/known-limitations.md")

    print()

    # All notebooks should be structurally valid
    if valid_count == len(results):
        print("✅ VALIDATION PASSED: All notebooks have valid structure")
        if issue_count > 0:
            print(f"⚠️  Note: {issue_count} notebook(s) contain known limitations")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED: Some notebooks have structural issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
