# Refactoring Priorities and Next Steps

**Last Updated:** November 26, 2025
**Current Branch:** fixing-data-problem  
**Project Board:** https://github.com/users/julihocc/projects/3  
**Milestone:** https://github.com/julihocc/dynasir/milestone/2
**Phase:** Post Phase 3 - Maintenance and Improvements

---

## Current Status

### Completed Work
- Phase 1: Foundation Setup COMPLETE
- Phase 2: Core Functionality Extraction COMPLETE
- Phase 3: Advanced Features & Analysis Module COMPLETE
- Notebook API synchronization COMPLETE
- Modern pandas syntax migration COMPLETE

### Recent Fixes (November 2025)
1. Fixed `global_forecasting.ipynb` import errors
   - Changed `compartment_labels` → `COMPARTMENT_LABELS` (uppercase)
2. Fixed notebook API method calls
   - `create_logit_ratios_model()` → `create_model()`
   - `fit_logit_ratios_model()` → `fit_model()`
   - `forecast_logit_ratios()` → `forecast()`
3. Updated documentation
   - TUTORIAL.md updated with correct API
   - CLAUDE.md already had correct API
   - README.md is generic and correct

---

## Priority 1: Critical Documentation and Examples

### 1.1 Verify and Test Example Notebook (Tracking: #63)
**Status:** HIGH PRIORITY
**Rationale:** The notebook is the primary demonstration of the library

**Tasks:**
- [ ] Run `global_forecasting.ipynb` end-to-end to verify all cells execute
- [ ] Check for any remaining deprecated method calls
- [ ] Verify all imports work correctly
- [ ] Ensure all visualizations render properly
- [ ] Test with current OWID data

**Files to Check:**
- `examples/global_forecasting.ipynb`
- `examples/README.md`

### 1.2 Add Method Deprecation Warnings (Tracking: #64)
**Status:** RECOMMENDED
**Rationale:** Help users transition from old API to new API

**Implementation:**
```python
# In src/dynasir/models/sird.py

import warnings

class Model:
    def create_logit_ratios_model(self, *args, **kwargs):
        """DEPRECATED: Use create_model() instead."""
        warnings.warn(
            "create_logit_ratios_model() is deprecated, use create_model() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.create_model(*args, **kwargs)

    def fit_logit_ratios_model(self, *args, **kwargs):
        """DEPRECATED: Use fit_model() instead."""
        warnings.warn(
            "fit_logit_ratios_model() is deprecated, use fit_model() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.fit_model(*args, **kwargs)

    def forecast_logit_ratios(self, *args, **kwargs):
        """DEPRECATED: Use forecast() instead."""
        warnings.warn(
            "forecast_logit_ratios() is deprecated, use forecast() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.forecast(*args, **kwargs)
```

**Benefits:**
- Backward compatibility maintained
- Clear migration path for users
- Follows Python best practices

---

## Priority 2: Enhanced Functionality

### 2.1 Add R₀ Calculation Methods (Tracking: #65)
**Status:** ALREADY IMPLEMENTED (verify in sird.py)
**Rationale:** R₀ is a critical epidemiological metric

**Methods to verify:**
- `Model.calculate_R0()` - Historical R₀ from data
- `Model.forecast_R0()` - Forecasted R₀ across scenarios

**Testing Needed:**
```python
# tests/unit/models/test_r0_calculation.py
def test_calculate_R0_from_data(sample_model):
    """Test R₀ calculation from historical data."""
    R0 = sample_model.calculate_R0()
    assert isinstance(R0, pd.Series)
    assert all(R0 >= 0)

def test_forecast_R0_scenarios(fitted_model):
    """Test R₀ forecasting across scenarios."""
    R0_forecast = fitted_model.forecast_R0()
    assert R0_forecast.shape[1] >= 27  # At least 27 scenarios
```

### 2.2 Enhance Visualization Utilities (Tracking: #66)
**Status:** PARTIALLY IMPLEMENTED
**Rationale:** Notebook has superior formatting not in library

**Verify Existence:**
- `dynasir.analysis.formatting.format_time_axis()`
- `dynasir.analysis.formatting.add_forecast_highlight()`
- `dynasir.analysis.formatting.set_professional_style()`

**If Missing, Add:**
```python
# src/dynasir/analysis/formatting.py

def format_time_axis(ax, data_index, time_range="auto", rotation=45, labelsize=10):
    """Apply consistent time axis formatting."""
    # Implementation from notebook
    pass

def add_forecast_highlight(ax, start, end, color="#FBD38D", alpha=0.12):
    """Add forecast period highlight to plot."""
    # Implementation from notebook
    pass
```

---

## Priority 3: Code Quality and Maintenance

### 3.1 API Consistency Audit (Tracking: #67)
**Status:** NEEDED
**Rationale:** Ensure all method names follow consistent patterns

**Tasks:**
- [ ] List all public methods in Model class
- [ ] Check for any remaining "logit_ratios" in method names
- [ ] Ensure all internal delegation works correctly
- [ ] Verify VARForecasting class methods

### 3.2 Documentation Completeness (Tracking: #68)
**Status:** IN PROGRESS

**Tasks:**
- [x] TUTORIAL.md - Updated
- [x] CLAUDE.md - Verified correct
- [x] README.md - Verified correct
- [ ] Add docstring examples to all major methods
- [ ] Create API reference documentation
- [ ] Add migration guide (old API → new API)

### 3.3 Test Coverage for API Changes (Tracking: #69)
**Status:** NEEDED

**Tasks:**
- [ ] Test old method names still work (with deprecation warnings)
- [ ] Test new method names work correctly
- [ ] Test VARForecasting delegation
- [ ] Test EpidemicSimulation delegation

---

## Priority 4: Performance and Scalability

### 4.1 Parallel Simulation Execution (Tracking: #70)
**Status:** FUTURE ENHANCEMENT
**Rationale:** 27 scenarios run sequentially is slow

**Design:**
```python
# In src/dynasir/models/sird.py

def run_simulations(self, n_jobs=None):
    """Run epidemic simulations with optional parallelization.

    Args:
        n_jobs: Number of parallel jobs (None = CPU count, 1 = sequential)
    """
    # Use ProcessPoolExecutor for parallel execution
    pass
```

### 4.2 Result Caching (Tracking: #71)
**Status:** FUTURE ENHANCEMENT
**Rationale:** Avoid recomputing identical forecasts

---

## Priority 5: Extended Functionality

### 5.1 Alternative Time Series Models (Tracking: #72)
**Status:** FUTURE RESEARCH
**Options:**
- SARIMAX for seasonal patterns
- Prophet for automated forecasting
- LSTM for deep learning approaches

### 5.2 Regional Comparison Utilities (Tracking: #73)
**Status:** FUTURE FEATURE
**Purpose:** Easy multi-region analysis and comparison

---

## Implementation Timeline

### Immediate (This Week)
1. Verify notebook runs end-to-end
2. Add deprecation warnings for old API
3. Run full test suite

### Short-term (Next Month)
1. Complete API consistency audit
2. Add comprehensive docstring examples
3. Create migration guide
4. Increase test coverage to 80%+

### Medium-term (Next Quarter)
1. Implement parallel simulations
2. Add result caching
3. Create additional example notebooks
4. Performance benchmarking

### Long-term (Future)
1. Alternative forecasting models
2. Regional comparison utilities
3. Advanced visualization tools
4. Plugin system for custom models

---

## Success Metrics

- [ ] All example notebooks run without errors
- [ ] No breaking changes for existing users
- [ ] Clear deprecation warnings for old API
- [ ] Test coverage > 80%
- [ ] All public methods have docstring examples
- [ ] Documentation builds successfully
- [ ] PyPI package can be released as v0.6.1

---

## Known Issues to Address

### Issue 1: Import Naming Inconsistency
**Status:** RESOLVED
- Fixed: `compartment_labels` → `COMPARTMENT_LABELS`

### Issue 2: API Method Names
**Status:** RESOLVED
- Fixed: Old method names updated in notebook and tutorial

### Issue 3: Pandas Deprecation Warnings
**Status:** RESOLVED (Phase 3)
- Modern pandas syntax implemented

---

## Maintenance Notes

### API Stability
- Core API (create_model, fit_model, forecast) is now stable
- Old method names should remain with deprecation warnings
- No breaking changes planned for v0.6.x series

### Backward Compatibility Strategy
1. Keep old methods with deprecation warnings
2. Maintain for at least 2 minor versions (0.6.x, 0.7.x)
3. Remove in v0.8.0 with clear migration guide

### Version Planning
- v0.6.1: Current state + deprecation warnings + documentation
- v0.7.0: Enhanced features (parallel, caching, R₀)
- v0.8.0: Breaking changes (remove deprecated methods)
- v1.0.0: Stable release with complete feature set

---

## References

- [ROADMAP.md](ROADMAP.md) - Complete refactoring roadmap
- [CODE_IMPROVEMENTS_ROADMAP.md](CODE_IMPROVEMENTS_ROADMAP.md) - Detailed improvement plans
- [CLAUDE.md](CLAUDE.md) - Development guide for AI assistants
- [TUTORIAL.md](TUTORIAL.md) - User tutorial
