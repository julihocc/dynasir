# Summary: epydemics → dynasir Package Rename (v1.0.0)

## Package Identity Changes

**Old Name**: epydemics  
**New Name**: dynasir (DynaSIR)  
**Version**: 1.0.0 (first release under new name)  
**Release Date**: January 13-14, 2026

## Installation & Import Changes

**OLD (epydemics)**:
```python
pip install epydemics

import epydemics
from epydemics import DataContainer, Model
from epydemics.analysis import ModelReport
```

**NEW (dynasir)**:
```python
pip install dynasir

import dynasir
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport
```

## Repository Changes

- **Repository**: Renamed from `julihocc/epydemics` → `julihocc/dynasir`
- **GitHub URL**: https://github.com/julihocc/dynasir
- **PyPI URL**: https://pypi.org/project/dynasir/
- **All issue/PR links**: Update from `/epydemics/` to `/dynasir/` in URLs

## What Changed

1. **Package name**: `epydemics` → `dynasir` everywhere
2. **Import namespace**: All imports now use `dynasir` instead of `epydemics`
3. **No backward compatibility aliases**: Version 1.0.0 removes all legacy `epydemics` references
4. **Repository branding**: GitHub repo renamed to match package name
5. **PyPI project**: Published as `dynasir` (previous versions under `epydemics` deprecated)

## What Did NOT Change

- **Functionality**: All APIs, classes, methods, and features remain identical
- **Python support**: Still 3.9, 3.10, 3.11, 3.12
- **Core architecture**: SIRD/SIRDV models with VAR forecasting unchanged
- **Module structure**: `dynasir.core`, `dynasir.data`, `dynasir.models`, `dynasir.analysis` (same layout as before)
- **Dependencies**: No changes to required packages
- **License**: Same license as epydemics

## Key Version Information

- **Last epydemics version**: 0.11.2
- **First dynasir version**: 1.0.0
- **Breaking change**: Users must update imports when upgrading from epydemics to dynasir

## Citations & References

When updating papers/reports:
- Replace all instances of "epydemics" with "dynasir" or "DynaSIR"
- Update package name in code examples
- Update installation instructions
- Use "dynasir v1.0.0" for version references going forward
- Update GitHub/PyPI URLs to new repo name
- Note: "Formerly known as epydemics" may be appropriate for historical context

## Technical Details

### Code Examples Update Guide

**Before (epydemics)**:
```python
from epydemics import DataContainer, Model
from epydemics.analysis import ModelReport
from epydemics.core.constants import RATIOS, COMPARTMENTS

# Create model
data = pd.DataFrame({'I': [...], 'D': [...], 'N': [...]})
container = DataContainer(data, mode='incidence', frequency='YE')
model = Model(container)
```

**After (dynasir)**:
```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport
from dynasir.core.constants import RATIOS, COMPARTMENTS

# Create model (same API)
data = pd.DataFrame({'I': [...], 'D': [...], 'N': [...]})
container = DataContainer(data, mode='incidence', frequency='YE')
model = Model(container)
```

### Bibliography/Citation Updates

**Old citation format**:
```
Author, A. (2024). Title. epydemics v0.11.2. 
Available at: https://github.com/julihocc/epydemics
```

**New citation format**:
```
Author, A. (2026). Title. dynasir v1.0.0. 
Available at: https://github.com/julihocc/dynasir
DOI: https://doi.org/10.5281/zenodo.14564142
```

### Documentation Reference Updates

All documentation references should be updated:
- Package name: epydemics → dynasir
- Import statements: update namespace
- GitHub links: /epydemics/ → /dynasir/
- PyPI links: /project/epydemics/ → /project/dynasir/
- Version numbers: 0.x.x → 1.0.0

## Migration Notes for Report/Paper Authors

1. **Find & Replace**: Search for "epydemics" and replace with "dynasir" (case-sensitive)
2. **Code Blocks**: Update all Python import statements
3. **URLs**: Update GitHub and PyPI links
4. **Version References**: Update to v1.0.0
5. **Installation Commands**: Change `pip install epydemics` to `pip install dynasir`
6. **Historical Context**: Consider adding "(formerly epydemics)" on first mention
7. **Bibliography**: Update package name and URLs in citations
8. **Figures/Diagrams**: If package name appears in diagrams, update branding

## Status: Complete

- ✅ Package renamed and published to PyPI as dynasir 1.0.0
- ✅ Repository renamed to julihocc/dynasir
- ✅ All code references updated
- ✅ GitHub issue links updated
- ✅ PyPI trusted publishing configured
- ✅ Installation and imports verified working
