# PyPI Publication Guide for dynasir v0.7.0

## ✅ Pre-Publication Checklist (COMPLETED)

- [x] Version bumped to 0.7.0 in `pyproject.toml` and `src/dynasir/__init__.py`
- [x] CHANGELOG.md updated with v0.7.0 release notes
- [x] All 192 tests passing (100% pass rate)
- [x] Code coverage at 67%
- [x] All 4 example notebooks validated and working
- [x] Pull Request #81 created and merged to main
- [x] GitHub Release v0.7.0 created: https://github.com/julihocc/dynasir/releases/tag/v0.7.0
- [x] Distribution packages built:
  - `dist/dynasir-0.7.0-py3-none-any.whl` (42K)
  - `dist/dynasir-0.7.0.tar.gz` (46K)

## 📦 Current Build Status

Build completed successfully with the following artifacts:
```bash
$ ls -lh dist/
total 92K
-rw-rw-rw- 1 codespace codespace 42K Nov 28 05:18 dynasir-0.7.0-py3-none-any.whl
-rw-rw-rw- 1 codespace codespace 46K Nov 28 05:18 dynasir-0.7.0.tar.gz
```

## 🔑 PyPI API Token Setup

### Step 1: Create PyPI API Token

1. Visit https://pypi.org/manage/account/token/
2. Log in with your PyPI account (username: `julihocc` or associated email)
3. Click "Add API token"
4. **Token name**: `dynasir-v0.7.0-release`
5. **Scope**: `Project: dynasir` (if project exists) or `Entire account`
6. Click "Create token"
7. **COPY THE TOKEN IMMEDIATELY** - it will only be shown once
   - Format: `pypi-AgEIcHlwaS5vcmc...` (starts with `pypi-`)

### Step 2: Store Token Securely

Option A - Environment Variable (Recommended for CI/CD):
```bash
export UV_PUBLISH_TOKEN="pypi-AgEIcHlwaS5vcmc..."
```

Option B - `.env` File (Local Development):
```bash
# Create .env file in project root (already in .gitignore)
echo 'UV_PUBLISH_TOKEN="pypi-AgEIcHlwaS5vcmc..."' >> .env
```

Option C - GitHub Secrets (For GitHub Actions):
- Go to repository Settings → Secrets and variables → Actions
- Add `PYPI_API_TOKEN` with your token value

## 🚀 Publication Methods

### Method 1: Using `uv publish` (Recommended)

**With token environment variable set:**
```bash
cd /workspaces/dynasir
uv publish
```

**With explicit token:**
```bash
uv publish --token "pypi-AgEIcHlwaS5vcmc..."
```

**Dry run (test without uploading):**
```bash
uv publish --dry-run
```

### Method 2: Using `twine` (Alternative)

If `uv publish` has issues:

```bash
# Install twine
pip install twine

# Upload to PyPI
twine upload dist/dynasir-0.7.0* --username __token__ --password "pypi-AgEIcHlwaS5vcmc..."
```

### Method 3: Test PyPI First (Safest)

Recommended for first-time publication:

```bash
# Create Test PyPI token at https://test.pypi.org/manage/account/token/

# Upload to Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token "pypi-AgEIcHRlc3QucHlwaS5vcmc..."

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dynasir==0.7.0

# Verify it works
python -c "from dynasir import DataContainer, Model; print('Success!')"
```

## 📋 Step-by-Step Publication Workflow

### Complete Command Sequence

```bash
# 1. Ensure you're on main branch with latest code
cd /workspaces/dynasir
git checkout main
git pull origin main

# 2. Verify version is correct
grep "version = " pyproject.toml
grep "__version__" src/dynasir/__init__.py

# 3. Run final tests (already passed)
pytest --cov=src/dynasir -v

# 4. Clean old builds (if any)
rm -rf dist/ build/ src/dynasir.egg-info/

# 5. Build fresh distributions
uv build

# 6. Verify package contents
tar -tzf dist/dynasir-0.7.0.tar.gz | head -20
unzip -l dist/dynasir-0.7.0-py3-none-any.whl | head -20

# 7. Set PyPI token (ONE of these methods)
export UV_PUBLISH_TOKEN="pypi-AgEIcHlwaS5vcmc..."  # Terminal
# OR add to .env file
# OR use --token flag in publish command

# 8. OPTIONAL: Test on Test PyPI first
uv publish --publish-url https://test.pypi.org/legacy/ --token "YOUR_TEST_PYPI_TOKEN"

# 9. Publish to production PyPI
uv publish

# 10. Verify publication
# Wait 1-2 minutes for PyPI to index, then:
pip install --upgrade dynasir==0.7.0
python -c "import dynasir; print(dynasir.__version__)"  # Should print: 0.7.0
```

## 🔍 Post-Publication Verification

### 1. Check PyPI Page

Visit https://pypi.org/project/dynasir/0.7.0/ and verify:
- Version shows as 0.7.0
- Release date is correct (Nov 28, 2025)
- README.md renders correctly
- Dependencies listed correctly
- Download statistics start accumulating

### 2. Test Fresh Installation

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install dynasir==0.7.0

# Run quick validation
python -c "
from dynasir import DataContainer, Model, process_data_from_owid
print('Import successful!')
print('Version:', dynasir.__version__)
"

# Deactivate and cleanup
deactivate
rm -rf test_env
```

### 3. Test SIRDV Feature

```bash
python << 'EOF'
from dynasir import process_data_from_owid, DataContainer, Model

# Test SIRD mode
raw = process_data_from_owid(iso_code="OWID_WRL")
container = DataContainer(raw, window=7)
print(f"SIRD mode - Columns: {list(container.data.columns)}")

# Test SIRDV mode
raw_vacc = process_data_from_owid(iso_code="ISR", include_vaccination=True)
container_vacc = DataContainer(raw_vacc, window=7)
print(f"SIRDV mode - Columns: {list(container_vacc.data.columns)}")
print("SIRDV feature working!")
EOF
```

## 🛑 Common Issues & Solutions

### Issue 1: "Invalid API token"
**Cause**: Token copied incorrectly or expired  
**Solution**: Regenerate token from PyPI, ensure it starts with `pypi-`

### Issue 2: "Package already exists"
**Cause**: v0.7.0 already uploaded (can't replace)  
**Solution**: 
- If testing, use Test PyPI
- If production error, version must be incremented (0.7.1)

### Issue 3: "403 Forbidden"
**Cause**: Token lacks permissions for project  
**Solution**: Use "Entire account" scope or add project-specific permission

### Issue 4: README not rendering
**Cause**: Markdown syntax issues  
**Solution**: Check README.md locally with `python -m readme_renderer README.md`

### Issue 5: Missing dependencies
**Cause**: pyproject.toml dependencies incomplete  
**Solution**: Verify all imports work in fresh venv before publishing

## 📊 Expected PyPI Metrics

After successful publication:

- **Download stats**: Visible after ~1 hour on PyPI stats page
- **PyPI badge**: `![PyPI version](https://badge.fury.io/py/dynasir.svg)`
- **Package size**: ~42KB wheel, ~46KB source
- **Supported Python**: 3.9+ (as per pyproject.toml)
- **License**: MIT
- **Homepage**: GitHub repository URL

## 🔄 CI/CD Automation (Future Enhancement)

For automated releases via GitHub Actions, create `.github/workflows/publish-pypi.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build
      - run: uv publish --token ${{ secrets.PYPI_API_TOKEN }}
```

## 📝 Release Announcement Template

After publication, announce on:

### GitHub Discussion/Announcement
```markdown
🎉 dynasir v0.7.0 released!

Major feature: SIRDV model with vaccination support

Install: `pip install --upgrade dynasir`
Release notes: https://github.com/julihocc/dynasir/releases/tag/v0.7.0
PyPI: https://pypi.org/project/dynasir/0.7.0/

New in this release:
- V compartment for vaccination tracking
- 81 simulation scenarios (3⁴ confidence levels)
- Automatic SIRD/SIRDV detection
- 100% backward compatible

Check out the new tutorial: examples/notebooks/02_sirdv_vaccination_analysis.ipynb
```

### Social Media (if applicable)
```
Released dynasir v0.7.0 with SIRDV model support for epidemic forecasting with vaccination campaigns. 192 tests passing, 4 example notebooks included. #Python #DataScience #Epidemiology
https://github.com/julihocc/dynasir
```

## 🎯 Next Steps After Publication

1. **Monitor**: Watch for issues/questions on GitHub
2. **Badge**: Add PyPI version badge to README.md
3. **Documentation**: Consider setting up ReadTheDocs
4. **Examples**: Share notebooks on platforms like Kaggle
5. **Citation**: Add CITATION.cff for academic users
6. **Community**: Respond to first users and gather feedback

## 📞 Support

If publication issues arise:
- PyPI support: https://pypi.org/help/
- GitHub issues: https://github.com/julihocc/dynasir/issues
- Documentation: This guide

---

**Status**: Ready for publication to PyPI  
**Version**: 0.7.0  
**Date**: November 28, 2025  
**Maintainer**: @julihocc
