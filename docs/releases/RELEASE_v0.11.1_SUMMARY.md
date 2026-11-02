# DynaSIR v0.11.1 Release Summary

**Released**: January 8, 2026  
**Status**: ✅ Successfully published to PyPI and GitHub  
**Python Support**: 3.9, 3.10, 3.11, 3.12

---

## What Shipped

### Core Feature: ModelReport Class
- One-line export to Markdown, LaTeX tables, and publication-ready figures
- Automated summary statistics (mean, median, std, CV, etc.)
- Forecast accuracy evaluation (MAE, RMSE, MAPE, SMAPE)
- Multi-panel visualization with confidence intervals
- Model comparison utilities (`create_comparison_report`)

### Quality & Testing
- **CI Coverage**: All 435 tests passing (100% pass rate)
- **Python Matrix**: 3.9, 3.10, 3.11, 3.12 validated
- **Security**: bandit scan passed
- **Code Quality**: black, flake8, mypy all passing
- **Integration**: Wheel installation verified

### Workflow Fixes
- Added `workflow_call` trigger to `ci.yml` for reusable workflows
- Upgraded deprecated GitHub Actions: `upload-artifact` v3→v4, `download-artifact` v3→v4
- Modernized release job: switched from deprecated `create-release@v1` + `upload-release-asset@v1` to `softprops/action-gh-release@v1`
- Configured trusted publishing on PyPI via OIDC

### Documentation
- Updated all 7 example notebooks with v0.11.1 features
- Created `ANNOUNCEMENT_v0.11.1.md` with highlights and install instructions
- Created `RELEASE_CHECKLIST_vNext.md` for streamlined future releases
- Updated `RELEASE_GUIDE_v0.11.0.md` with all v0.11.1 details

---

## Backward Compatibility

✅ **100% backward compatible** with v0.9.1 and v0.10.0

- No breaking changes to public APIs
- Existing ModelReport workflows still work unchanged
- All historical notebooks remain valid

---

## Installation & Verification

Install the latest:
```bash
pip install dynasir==0.11.1
python -c "import dynasir; print(dynasir.__version__)"  # prints: 0.11.1
```

Links:
- **GitHub Release**: https://github.com/julihocc/dynasir/releases/tag/v0.11.1
- **PyPI Package**: https://pypi.org/project/dynasir/0.11.1/
- **Reporting Demo**: [examples/notebooks/07_reporting_and_publication.ipynb](examples/notebooks/07_reporting_and_publication.ipynb)

---

## Files Modified During Release

### Version & Metadata
- `pyproject.toml`: bumped 0.11.0 → 0.11.1, fixed license format
- `src/dynasir/__init__.py`: updated `__version__`

### CI/CD & Workflows
- `.github/workflows/ci.yml`: added `workflow_call` trigger, upgraded artifact actions, fixed paths
- `.github/workflows/release.yml`: modernized with `softprops/action-gh-release`
- `tests/integration/test_backward_compatibility.py`: updated version expectation

### Documentation
- `CHANGELOG.md`: added v0.11.1 release notes
- `RELEASE_GUIDE_v0.11.0.md`: updated all references to 0.11.1
- `ANNOUNCEMENT_v0.11.1.md`: created with highlights and links
- `RELEASE_CHECKLIST_vNext.md`: created for future releases

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Tests Passing | 435/435 (100%) |
| Optional Tests Skipped | 34 (prophet, pmdarima not installed) |
| Python Versions | 3.9, 3.10, 3.11, 3.12 |
| CI Matrix Jobs | 6 (per Python version + security + quality) |
| Release Workflow Attempts | 4 (workflow refinements, all succeeded) |
| Code Quality Issues | 0 (black, flake8, mypy all passing) |

---

## Next Steps (Post-Release)

For maintainers:
- Use `RELEASE_CHECKLIST_vNext.md` for the next release (0.11.2 or 0.12.0)
- Monitor PyPI and GitHub for user feedback
- Keep example notebooks updated with new features
- Track any security advisories via Dependabot

For users:
- Upgrade with `pip install --upgrade dynasir`
- Review `ANNOUNCEMENT_v0.11.1.md` for new capabilities
- Check [examples/notebooks/07_reporting_and_publication.ipynb](examples/notebooks/07_reporting_and_publication.ipynb) for usage examples

---

## Release Timeline

| Step | Date/Time | Status |
|------|-----------|--------|
| Version bump & CI fixes | Jan 8, 2026 | ✅ Complete |
| Branch sync with main | Jan 8, 2026 | ✅ Complete |
| PR #157 merge | Jan 8, 2026 | ✅ Complete |
| v0.11.1 tag created | Jan 8, 2026 | ✅ Complete |
| GitHub Release created | Jan 8, 2026 | ✅ Complete |
| PyPI published | Jan 8, 2026 | ✅ Complete |
| Announcement & checklist | Jan 8, 2026 | ✅ Complete |

---

## Sign-off

Release prepared and executed by: GitHub Copilot (Haiku 4.5)  
All automated checks: ✅ Passed  
All manual validations: ✅ Completed  
Status: **Ready for production use**
