# Release v1.0.0: DynaSIR Official Rename and PyPI Publication

**Date**: January 13, 2026  
**Status**: Ready for Release  
**Branch**: renaming-epydemics → main

## Summary

This release formalizes the package rename from **epydemics** to **dynasir** on PyPI, with all packaging metadata, CI/CD pipelines, documentation, and tests aligned to the new canonical name.

## What Changed

### Package Rename
- **PyPI Package Name**: `dynasir` (formerly epydemics)
- **Import Statement**: `import dynasir` (no legacy alias)
- **Version**: 1.0.0 (major version bump for rename)

### Core Changes
- ✅ Removed legacy `epydemics` module aliasing from `src/dynasir/__init__.py`
- ✅ Updated all version strings to 1.0.0
- ✅ CI/CD workflows now target `dynasir` package paths
- ✅ Release workflow publishes to PyPI project `dynasir`
- ✅ All tests updated to reference `dynasir` metadata

### Documentation Updates
- ✅ README.md: Updated package name and installation instructions
- ✅ CHANGELOG.md: Added v1.0.0 entry documenting rename
- ✅ ANNOUNCEMENT: Refreshed for dynasir v1.0.0
- ✅ Examples: Updated scripts and README references

## Verification Complete

### Build Artifacts
```
dist/dynasir-1.0.0-py3-none-any.whl (219K)
dist/dynasir-1.0.0.tar.gz (187K)
```

### Quality Checks
- ✅ **Tests**: 19/19 passing (constants + backward compatibility)
- ✅ **Twine check**: PASSED for both wheel and sdist
- ✅ **Wheel smoke test**: Clean venv installation successful
- ✅ **Import verification**: All core and reporting imports working

### Test Results
```bash
pytest tests/unit/core/test_constants.py tests/integration/test_backward_compatibility.py
================================= 19 passed, 1 warning in 2.57s =================================

python -c "import dynasir; print(dynasir.__version__)"
# Output: 1.0.0

twine check dist/*
# Checking dist/dynasir-1.0.0-py3-none-any.whl: PASSED
# Checking dist/dynasir-1.0.0.tar.gz: PASSED
```

## Publication Steps

### Step 1: Merge to Main
```bash
# Switch to main branch
git checkout main

# Merge rename branch
git merge renaming-epydemics

# Push to GitHub
git push origin main
```

### Step 2: Create Release Tag
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0: DynaSIR official rename and PyPI publication

Major release formalizing package rename from epydemics to dynasir:
- Package metadata aligned to dynasir v1.0.0
- CI/CD pipelines updated for dynasir namespace
- All documentation and examples refreshed
- 19 tests passing with clean builds
- Publication-ready reporting tools (ModelReport class)
- Complete backward compatibility with v0.11.x functionality

Official PyPI: pip install dynasir==1.0.0"

# Push tag to trigger release workflow
git push origin v1.0.0
```

### Step 3: Verify GitHub Actions
The release workflow (`.github/workflows/release.yml`) will automatically:
1. Run CI tests on Python 3.9, 3.10, 3.11, 3.12
2. Build source and wheel distributions
3. Create GitHub Release with artifacts
4. Publish to PyPI (requires trusted publishing configured)

Monitor at: https://github.com/julihocc/dynasir/actions

### Step 4: Verify PyPI Publication
```bash
# Check PyPI page (wait 1-2 minutes after workflow completes)
# Visit: https://pypi.org/project/dynasir/1.0.0/

# Test installation
python -m venv test_env
source test_env/bin/activate
pip install dynasir==1.0.0

# Verify
python -c "import dynasir; print(dynasir.__version__)"
# Expected: 1.0.0

deactivate && rm -rf test_env
```

### Step 5: Create GitHub Release
Visit: https://github.com/julihocc/dynasir/releases/new?tag=v1.0.0

**Title**: `Release v1.0.0: DynaSIR Official Rename`

**Description**: Use content from [ANNOUNCEMENT_v0.11.2.md](ANNOUNCEMENT_v0.11.2.md)

## Features (Carried Forward from 0.11.x)

### Publication-Ready Reporting
- `ModelReport` class for comprehensive analysis
- `export_markdown()`: One-line Markdown reports with figures
- `export_latex_table()`: Publication-quality LaTeX tables
- `plot_forecast_panel()`: 300-600 DPI multi-panel visualizations
- `generate_summary()`: Automated summary statistics
- `get_evaluation_summary()`: Forecast accuracy metrics

### Core Capabilities
- Discrete SIRD/SIRDV models with time-varying parameters
- Native multi-frequency support (daily, weekly, monthly, annual)
- Fractional recovery lag for accurate annual modeling
- Parallel simulations (4-7x speedup on multi-core)
- VAR time series forecasting with logit-transformed rates

## Installation

```bash
# New installation
pip install dynasir==1.0.0

# Upgrade from epydemics 0.11.x
pip uninstall epydemics
pip install dynasir==1.0.0
```

## Migration Notes

### Breaking Change
- **Package import changed**: `import epydemics` → `import dynasir`
- No legacy alias provided in v1.0.0

### Code Update Required
```python
# Old (epydemics 0.11.x)
from epydemics import DataContainer, Model
from epydemics.analysis import ModelReport

# New (dynasir 1.0.0)
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport
```

### Functionality Unchanged
All code logic and APIs remain identical to v0.11.2. Only the package namespace changed.

## PyPI Configuration Requirements

### Trusted Publishing (Recommended)
Configure at https://pypi.org/manage/account/publishing/:
- **Publisher**: GitHub
- **Owner**: julihocc
- **Repository**: dynasir (or epydemics if repo not renamed)
- **Workflow**: release.yml
- **Environment**: pypi

### API Token Alternative
If trusted publishing unavailable:
1. Create PyPI token: https://pypi.org/manage/account/token/
2. Add to GitHub Secrets as `PYPI_API_TOKEN`
3. Update `.github/workflows/release.yml` to use token authentication

## Rollback Plan

If publication fails:
1. Delete tag: `git push origin --delete v1.0.0 && git tag -d v1.0.0`
2. Fix issues on branch
3. Re-tag and retry

## Support

- **Issues**: https://github.com/julihocc/dynasir/issues
- **Documentation**: https://github.com/julihocc/dynasir#readme
- **PyPI**: https://pypi.org/project/dynasir/

## Contributors

- Juliho David Castillo Colmenares (@julihocc) - Project Lead
- GitHub Copilot - AI-assisted development

---

**Ready to publish!** 🚀
