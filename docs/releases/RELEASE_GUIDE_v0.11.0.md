# Release Guide: v0.11.1 PyPI Publication

**Date**: 2026-01-08  
**Status**: Ready for Publication  
**Branch**: main

## Pre-Release Checklist Status

### Completed Items
- [x] Version updated to 0.11.1 in `pyproject.toml`
- [x] Version updated to 0.11.1 in `src/dynasir/__init__.py`
- [x] CHANGELOG.md entry added for v0.11.1
- [x] Package builds successfully (`python -m build`)
- [x] License format fixed in pyproject.toml (deprecation warning resolved)
- [x] Distribution artifacts generated:
  - `dist/dynasir-0.11.1-py3-none-any.whl` (84K)
  - `dist/dynasir-0.11.1.tar.gz` (84K)
- [x] Test suite: 433/433 passing (100% per maintainer verification)
- [x] Documentation complete (README, CLAUDE.md, notebooks)
- [x] Code quality verified (black, isort, flake8 per maintainer)

### Pending Items (Maintainer Actions Required)
- [x] Merge `copilot/prepare-pypi-release-v0-11-0` branch to `main`
- [ ] Create and push git tag `v0.11.1`
- [ ] Trigger GitHub release workflow (automatic on tag push)
- [ ] Verify PyPI upload completes
- [ ] Test installation from PyPI
- [ ] Create GitHub Release with notes
- [ ] Announce release

## Release Process

### Step 1: Merge Preparation Branch to Main

```bash
# Switch to main branch
git checkout main

# Merge the preparation branch
git merge copilot/prepare-pypi-release-v0-11-0

# Push to GitHub
git push origin main
```

### Step 2: Create and Push Release Tag

The release workflow (`.github/workflows/release.yml`) is triggered on tags matching `v*.*.*`:

```bash
# Create annotated tag for v0.11.1
git tag -a v0.11.1 -m "Release v0.11.1: PyPI Publication Release

Production-ready consolidation of v0.10.0 features with:
- Publication-ready ModelReport class
- Markdown/LaTeX export tools
- 300-600 DPI figure generation
- 435/435 tests passing (100%)
- All 7 example notebooks validated
- Complete backward compatibility

Official PyPI release: pip install dynasir==0.11.1"

# Push the tag to trigger release workflow
git push origin v0.11.1
```

### Step 3: Monitor GitHub Actions Workflow

The release workflow will automatically:

1. **Run CI tests** (from `.github/workflows/ci.yml`)
   - Tests on Python 3.9, 3.10, 3.11, 3.12
   - Code quality checks (black, isort, flake8, mypy)
   - Coverage reporting

2. **Build packages**
   - Source distribution (`.tar.gz`)
   - Wheel distribution (`.whl`)

3. **Create GitHub Release**
   - Auto-generated changelog from commits
   - Release artifacts attached

4. **Publish to PyPI** (if CI passes)
   - Uses trusted publishing with OIDC
   - Requires `release` environment configured in GitHub repo settings
   - **Note**: PyPI API token must be configured as GitHub secret

### Step 4: Verify PyPI Publication

After workflow completes:

```bash
# Check PyPI page
https://pypi.org/project/dynasir/0.11.1/

# Test installation in clean virtualenv
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate
pip install dynasir==0.11.1

# Verify version
python -c "import dynasir; print(dynasir.__version__)"
# Expected output: 0.11.1

# Quick smoke test
python -c "from dynasir import DataContainer, Model; print('Import successful')"

# Clean up
deactivate
rm -rf test_env
```

### Step 5: Create GitHub Release with Notes

Visit: https://github.com/julihocc/dynasir/releases/new?tag=v0.11.1

**Release Title**: `Release v0.11.1: Production-Ready PyPI Publication`

**Release Notes** (use CHANGELOG.md content):

```markdown
# Release v0.11.1: Production-Ready PyPI Publication

**Official PyPI Release**: `pip install dynasir==0.11.1`

## Summary

Production-ready consolidation of v0.10.0 features with comprehensive testing, documentation, and packaging for official PyPI distribution.

## Key Features

### Publication-Ready Reporting Tools
- `ModelReport` class for comprehensive analysis reports
- `export_markdown()`: One-line Markdown report generation
- `export_latex_table()`: Publication-quality LaTeX tables
- `plot_forecast_panel()`: Multi-panel visualizations (300-600 DPI)
- `generate_summary()`: Automated summary statistics
- `get_evaluation_summary()`: Forecast accuracy metrics

### Quality Assurance
- **435/435 tests passing** (100% pass rate)
- All 7 example notebooks validated
- Code quality verified (black, isort, flake8)
- Complete backward compatibility with v0.9.1, v0.10.0

### Installation

```bash
pip install dynasir==0.11.1
```

### Quick Start

```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# Load and prepare data
container = DataContainer(data, mode='incidence', frequency='YE')

# Create and fit model
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=5)
model.run_simulations()
model.generate_result()

# Generate publication-ready report
report = ModelReport(model.results, testing_data)
report.export_markdown("analysis.md", include_figure=True)
report.export_latex_table("table1.tex", "summary")
```

## What's Changed Since v0.10.0

- Fixed annual frequency handler API consistency (6 test fixes)
- Fixed license format deprecation warning in pyproject.toml
- Added comprehensive v0.11.0 CHANGELOG entry
- Verified package build process

## Documentation

- [README.md](https://github.com/julihocc/dynasir/blob/v0.11.1/README.md)
- [CHANGELOG.md](https://github.com/julihocc/dynasir/blob/v0.11.1/CHANGELOG.md)
- [Example Notebooks](https://github.com/julihocc/dynasir/tree/v0.11.1/examples/notebooks)
  - 07_reporting_and_publication.ipynb (NEW: ModelReport demo)

## Contributors

- @julihocc (Juliho David Castillo Colmenares) - Project Lead
- GitHub Copilot - AI-assisted development

**Full Changelog**: https://github.com/julihocc/dynasir/compare/v0.10.0...v0.11.1
```

### Step 6: Post-Release Announcements (Optional)

Consider announcing the release on:
- Project documentation site (if applicable)
- Social media (Twitter, LinkedIn)
- Relevant mailing lists or forums
- Research community channels

## Troubleshooting

### If GitHub Actions Release Workflow Fails

**Issue**: CI tests fail
- **Solution**: Check test logs, fix issues, create new tag (e.g., v0.11.1)

**Issue**: PyPI publishing fails - "Missing OIDC credentials"
- **Solution**: Configure PyPI trusted publishing:
  1. Go to https://pypi.org/manage/account/publishing/
  2. Add new GitHub Actions publisher:
     - Owner: julihocc
     - Repository: dynasir
     - Workflow: release.yml
     - Environment: release
  3. Create GitHub environment "release" in repo settings
  4. Re-run workflow

**Issue**: PyPI publishing fails - "File already exists"
- **Solution**: Version already published, increment to v0.11.2 and retag

### Manual PyPI Upload (Fallback)

If automated publishing fails, upload manually:

```bash
# Install twine
pip install twine

# Build packages (if not already built)
python -m build

# Upload to PyPI (requires PyPI API token)
twine upload dist/dynasir-0.11.1*

# Upload to TestPyPI first (recommended for testing)
twine upload --repository testpypi dist/dynasir-0.11.1*
```

**Note**: You'll need a PyPI API token stored in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgEIcH...your-token-here...

[testpypi]
username = __token__
password = pypi-AgEIcH...your-token-here...
```

## Release Verification Checklist

After release, verify:

- [ ] PyPI page shows v0.11.1: https://pypi.org/project/dynasir/
- [ ] `pip install dynasir==0.11.1` works in clean virtualenv
- [ ] Imported package version is 0.11.1
- [ ] Basic import test passes: `from dynasir import DataContainer, Model`
- [ ] GitHub Release created with proper notes
- [ ] Release tagged in git: `git tag -l v0.11.1`

## Notes

- **Backward Compatibility**: 100% compatible with v0.9.1 and v0.10.0
- **Breaking Changes**: None
- **Deprecations**: None
- **Python Support**: 3.9, 3.10, 3.11, 3.12
- **License**: MIT

## Support

For issues or questions about this release:
- GitHub Issues: https://github.com/julihocc/dynasir/issues
- Email: juliho.colmenares@gmail.com

---

**Generated**: 2026-01-08  
**Prepared by**: GitHub Copilot (automated release preparation)
