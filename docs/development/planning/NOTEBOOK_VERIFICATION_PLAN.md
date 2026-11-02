# Notebook Verification Plan

**Branch**: `feature/notebook-verification`
**Issues**: #127-137 (Phases 1-4)
**Goal**: Ensure all example notebooks execute correctly with v0.9.1

## Overview

After releasing v0.9.0 and v0.9.1, we need to verify that all example notebooks work correctly with the new features (native multi-frequency, incidence mode, importation modeling, scenario analysis).

## Related Issues

### Phase 1: Core Verification (#127-129)
- [ ] #127: Verify AnnualFrequencyHandler works correctly
- [ ] #128: Verify complete measles data workflow
- [ ] #129: Create verification results documentation

### Phase 2: Notebook Updates (#130-132)
- [ ] #130: Create new notebook demonstrating native annual support
- [ ] #131: Remove outdated version references from notebook 07
- [ ] #132: Audit all notebooks for outdated references

### Phase 3: Testing (#133-135)
- [ ] #133: Execute full notebook test suite
- [ ] #134: Manually verify all notebooks in Jupyter
- [ ] #135: Test measles data download scripts

### Phase 4: Release Decision (#136-137)
- [ ] #136: Decide if release is needed (v0.9.1 vs v0.10.0)
- [ ] #137: Prepare release (if needed)

## Current Notebook Inventory

### examples/ directory

**Existing Notebooks**:
1. `global_forecasting.ipynb` - COVID-19 global analysis
2. `parallel_simulation_demo.ipynb` - Parallel simulation demonstrations
3. `validation_usa_measles.ipynb` - USA measles validation (NEW in v0.9.1)
4. `scenario_analysis_measles.ipynb` - Scenario comparison (NEW in v0.9.1)

**Notebook Subdirectory** (examples/notebooks/):
5. `06_annual_measles_workaround.ipynb` - Pre-v0.9.0 annual workaround
6. `07_incidence_mode_measles.ipynb` - Incidence mode demonstration

**Scripts**:
- `examples/data/fetch_measles_data.py` - OWID data fetching
- `examples/verify_measles_integration.py` - Importation verification
- `examples/verify_scenarios_headless.py` - Scenario analysis verification

## Verification Tasks

### Task 1: AnnualFrequencyHandler Verification (#127)

**Objective**: Verify that annual data processing works correctly without reindexing

**Steps**:
1. Create test script with annual measles data
2. Verify FrequencyHandler correctly detects 'YE' frequency
3. Verify recovery_lag calculation for annual data
4. Verify max_lag defaults to 3 for annual data
5. Confirm no artificial reindexing occurs
6. Document results

**Test Data**: Mexico measles 2010-2024 (15 annual observations)

**Expected Results**:
- Frequency detected as 'YE'
- recovery_lag = 0 (rounded from 14/365)
- max_lag defaults to 3
- Data stays at 15 rows (no expansion to ~5,475 daily rows)

### Task 2: Complete Measles Workflow (#128)

**Objective**: End-to-end workflow test with measles data

**Steps**:
1. Load annual measles data (incidence mode)
2. Create DataContainer with frequency='YE', mode='incidence'
3. Create and fit Model
4. Generate forecasts
5. Run simulations
6. Verify results are in annual frequency
7. Test importation modeling
8. Test scenario analysis

**Test Scenarios**:
- Baseline: No intervention
- Scenario 1: Enhanced vaccination
- Scenario 2: Importation reduction
- Scenario 3: Combined intervention

### Task 3: Create Verification Documentation (#129)

**Objective**: Document all verification results

**Structure**:
```markdown
# Notebook Verification Results

## Summary
- Total notebooks: X
- Passing: Y
- Failing: Z
- Needs update: W

## Detailed Results
### Notebook 1: global_forecasting.ipynb
- Status: ✅ PASS
- Execution time: XX seconds
- Notes: None

[... for each notebook ...]

## Issues Found
1. Issue description
2. Issue description

## Recommendations
1. Update notebook X
2. Fix issue Y
```

### Task 4: Create Native Annual Notebook (#130)

**Objective**: Demonstrate native annual frequency support (v0.9.0+ feature)

**Outline**:
```python
# 1. Introduction
- Explain annual data challenges
- v0.8.0 workaround vs v0.9.0 native support

# 2. Load Annual Data
- Mexico measles 2010-2024
- Show native frequency detection

# 3. Native Processing
- DataContainer with frequency='YE', mode='incidence'
- Show no reindexing occurs

# 4. Modeling
- Model creation and fitting
- Frequency-aware max_lag selection

# 5. Forecasting
- Generate 5-year forecasts
- Results stay in annual frequency

# 6. Importation Modeling (v0.9.1)
- Add importation_rate
- Model eliminated disease dynamics

# 7. Scenario Analysis (v0.9.1)
- Compare intervention strategies
- Visualize results

# 8. Comparison with v0.8.0
- Show before/after workflow
- Highlight improvements
```

### Task 5: Update Notebook 07 (#131)

**Objective**: Remove outdated version references

**Changes Needed**:
1. Update version references (0.8.0 → 0.9.1)
2. Add note about v0.9.0 native frequency support
3. Update code examples if needed
4. Test execution

### Task 6: Audit All Notebooks (#132)

**Objective**: Systematic review of all notebooks

**Checklist for Each Notebook**:
- [ ] Version references are current
- [ ] Code executes without errors
- [ ] Outputs are correct
- [ ] Uses current API (no deprecated methods)
- [ ] Documentation is accurate
- [ ] Examples are relevant
- [ ] Cell execution order is correct
- [ ] Requirements are documented

### Task 7: Execute Full Test Suite (#133)

**Objective**: Automated notebook execution testing

**Approach**:
```bash
# Install nbconvert and papermill
pip install nbconvert papermill

# Execute each notebook
for notebook in examples/*.ipynb examples/notebooks/*.ipynb; do
    echo "Testing $notebook..."
    papermill "$notebook" "/tmp/$(basename $notebook)" \
        --log-output \
        --progress-bar
done
```

**Report**: Document execution time, errors, warnings

### Task 8: Manual Verification (#134)

**Objective**: Human review in Jupyter environment

**Steps**:
1. Open each notebook in Jupyter
2. Execute cells in order
3. Verify outputs are correct
4. Check visualizations render properly
5. Test interactive elements (if any)
6. Note any issues or improvements

### Task 9: Test Data Download Scripts (#135)

**Objective**: Verify data fetching works

**Script**: `examples/data/fetch_measles_data.py`

**Tests**:
1. Script executes without errors
2. Downloads correct data format
3. Saves to expected location
4. Data is valid (correct columns, types)
5. Documentation is clear

## Success Criteria

### Minimum Requirements (Must Have)
- [ ] All notebooks execute without errors
- [ ] No outdated version references
- [ ] Core workflows (COVID-19, measles) work correctly
- [ ] Data download scripts functional

### Nice to Have
- [ ] New native annual notebook created
- [ ] All notebooks have execution time < 5 minutes
- [ ] Comprehensive verification documentation
- [ ] Automated notebook testing integrated

## Timeline

**Estimated Effort**: 1-2 days

- **Phase 1** (4 hours): Core verification (#127-129)
- **Phase 2** (4 hours): Notebook updates (#130-132)
- **Phase 3** (3 hours): Testing (#133-135)
- **Phase 4** (1 hour): Decision and documentation (#136-137)

## Deliverables

1. **Verification Results Document** (#129)
   - File: `docs/development/NOTEBOOK_VERIFICATION_RESULTS.md`
   - Content: Detailed test results for all notebooks

2. **New Native Annual Notebook** (#130)
   - File: `examples/notebooks/08_native_annual_frequency.ipynb`
   - Content: Complete demonstration of native annual support

3. **Updated Notebooks**
   - All existing notebooks updated with current versions
   - No deprecated API usage
   - Clean execution

4. **Test Automation**
   - Script: `scripts/test_notebooks.sh`
   - Automated notebook execution and reporting

5. **Issue Updates**
   - Close issues #127-137 with verification results
   - Create follow-up issues if needed

## Notes

- This work is on branch `feature/notebook-verification`
- After completion, merge to main (or create PR)
- Consider whether findings require v0.9.2 patch release
- If significant changes, might wait for v0.10.0

## Next Steps After Completion

1. Review results with team
2. Decide on release strategy (#136-137)
3. If no release needed, merge to main
4. If release needed, follow release process
5. Move to v0.10.0 planning (option 1)

---

**Status**: Planning
**Last Updated**: December 19, 2025
**Branch**: feature/notebook-verification
