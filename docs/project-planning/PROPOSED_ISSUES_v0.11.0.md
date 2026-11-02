# Proposed GitHub Issues for v0.11.0 Planning

**Date**: December 2025  
**Status**: Draft - Ready for Manual Creation

## Overview

These 3 issues should be created to support the v0.11.0 release cycle and ongoing library improvements.

---

## Issue 1: v0.11.0 PyPI Release Preparation

**Title**: v0.11.0 PyPI Release Preparation  
**Labels**: enhancement, documentation, release  
**Priority**: HIGH

### Overview

Prepare dynasir library for PyPI publication as v0.11.0, completing all post-v0.10.0 documentation, testing, and packaging requirements.

### Prerequisites

- [x] v0.10.0 released (fractional recovery lag + reporting tools)
- [ ] All notebooks validated against v0.10.0 API
- [ ] CLAUDE.md updated with v0.10.0 features
- [ ] PyPI API token configured in GitHub Secrets

### Tasks

#### 1. Documentation Updates
- [ ] Update CLAUDE.md with `ModelReport` class usage
- [ ] Update README.md with v0.10.0 features (reporting tools)
- [ ] Verify all 7 example notebooks run without errors
- [ ] Update USER_GUIDE.md with reporting workflow examples
- [ ] Create CHANGELOG.md entry for v0.11.0

#### 2. Packaging & Dependencies
- [ ] Review pyproject.toml dependencies (ensure prophet, scikit-learn versions correct)
- [ ] Verify all extras_require groups (`dev`, `test`, `docs`)
- [ ] Update version number to 0.11.0 in `__init__.py` and `pyproject.toml`
- [ ] Generate fresh `requirements.txt` for PyPI metadata

#### 3. Testing & Quality Assurance
- [ ] Run full test suite: `pytest` (target: 100% pass rate)
- [ ] Run slow tests: `pytest -m slow` (25+ integration tests)
- [ ] Code quality checks: `black`, `isort`, `flake8`, `mypy`
- [ ] Coverage report: `pytest --cov` (target: >85%)
- [ ] Backward compatibility validation (see #93)

#### 4. Pre-Release Checklist
- [ ] Tag release commit: `git tag v0.11.0`
- [ ] Push tag to trigger release workflow: `git push origin v0.11.0`
- [ ] Monitor GitHub Actions for successful build
- [ ] Verify PyPI upload completes (check https://pypi.org/project/dynasir/)
- [ ] Test installation: `pip install dynasir==0.11.0` in clean virtualenv

#### 5. Post-Release
- [ ] Create GitHub Release with release notes
- [ ] Update documentation site (if applicable)
- [ ] Announce release on social media/mailing lists
- [ ] Close milestone v0.11.0

### Success Criteria

- [ ] Package successfully installs via `pip install dynasir`
- [ ] All 7 example notebooks execute without errors
- [ ] Test coverage >85%
- [ ] No breaking changes from v0.10.0
- [ ] Documentation complete and accurate

### Timeline

**Target Release Date**: January 2026  
**Estimated Effort**: 2-3 days

### Related Issues

- #97: Multi-backend refactoring (dependencies)
- #108: Phase 3 advanced features (roadmap alignment)
- #93: Backward compatibility tests (blocker)

### References

- PyPI Publication Guide: `docs/releases/PYPI_PUBLICATION_GUIDE.md`
- Release Workflow: `.github/workflows/release.yml`
- Version Management: `src/dynasir/__init__.py`

---

## Issue 2: Performance Benchmarking & Profiling Suite

**Title**: Performance Benchmarking & Profiling Suite  
**Labels**: enhancement, performance  
**Priority**: MEDIUM

### Problem

While v0.9.1+ handles annual + incidence mode correctly (fractional recovery lag fix), performance benchmarks and profiling data are missing. The library needs systematic performance validation across:
- Different data frequencies (annual, monthly, weekly, daily)
- Parallel vs sequential simulation modes
- Various dataset sizes (10-1000 time points)
- Multiple forecasting backends (VAR, Prophet, ARIMA)

### Proposed Solution

Create comprehensive performance benchmarking suite to:
1. Profile bottleneck operations (VAR fitting, simulation runs)
2. Compare parallel speedup across CPU core counts
3. Benchmark memory usage for large datasets
4. Validate O(n) complexity assumptions

### Acceptance Criteria

#### 1. Benchmarking Script
Create `benchmarks/performance_profiling.py` with:
- [ ] Timing decorator for key methods (`fit_model`, `forecast`, `run_simulations`)
- [ ] Memory profiler integration (`memory_profiler` package)
- [ ] Multi-frequency test cases (annual, monthly, weekly, daily)
- [ ] Dataset size sweep (10, 50, 100, 500, 1000 time points)
- [ ] Parallel vs sequential comparison (1, 2, 4, 8 cores)

#### 2. Performance Metrics
Track and report:
- [ ] VAR model fitting time vs dataset size
- [ ] Forecast generation time vs forecast horizon
- [ ] Simulation time vs number of scenarios (27 scenarios standard)
- [ ] Parallel speedup efficiency (actual vs theoretical)
- [ ] Memory usage per time point

#### 3. Documentation
- [ ] Create `docs/PERFORMANCE_GUIDE.md` with:
  - Typical performance characteristics
  - Recommended parallelization settings
  - Memory usage guidelines
  - Optimization tips for large datasets

#### 4. CI Integration
- [ ] Add performance regression test to GitHub Actions
- [ ] Fail CI if performance degrades >20% from baseline
- [ ] Generate performance comparison reports in PRs

### Implementation Notes

#### Example Benchmarking Code
```python
import timeit
from memory_profiler import profile

@profile
def benchmark_fit_model(data_size, frequency):
    """Profile memory during model fitting."""
    # Generate synthetic data
    container = generate_synthetic_data(size=data_size, freq=frequency)
    model = Model(container)
    
    # Time fitting operation
    start = timeit.default_timer()
    model.fit_model(max_lag=3)
    elapsed = timeit.default_timer() - start
    
    return elapsed

# Run benchmarks
for size in [10, 50, 100, 500]:
    for freq in ['YE', 'ME', 'W', 'D']:
        time = benchmark_fit_model(size, freq)
        print(f"{freq} {size}: {time:.3f}s")
```

#### Profiling Tools
- `cProfile`: Standard library profiler
- `memory_profiler`: Line-by-line memory usage
- `py-spy`: Sampling profiler (no code changes)
- `timeit`: Accurate timing measurements

### Success Metrics

- [ ] Baseline performance documented for all frequencies
- [ ] Parallel speedup validated (>3x on 4 cores)
- [ ] Memory usage <100MB for typical datasets (<1000 points)
- [ ] VAR fitting completes <5s for annual data (50 years)
- [ ] Simulation runs <30s for 27 scenarios (4 cores)

### Related Issues

- #100: Parallel simulations (implemented, needs benchmarking)
- #97: Multi-backend refactoring (backend comparison needed)
- #108: Phase 3 features (may impact performance)

### References

- Existing: `benchmarks/parallel_benchmark_report.md`
- Existing: `benchmarks/parallel_simulation_benchmark.py`
- Python Profiling: https://docs.python.org/3/library/profile.html

---

## Issue 3: Implement Backward Compatibility Test Suite

**Title**: Implement Backward Compatibility Test Suite  
**Labels**: testing, high-priority  
**Priority**: HIGH (blocker for v0.11.0)

### Problem

Issue #93 identified the need for comprehensive backward compatibility tests to ensure v0.8.0+ (multi-backend refactoring) maintains 100% compatibility with v0.7.0 behavior when using default parameters.

### Current State

- ✅ All existing unit tests pass (421/423)
- ✅ Multi-backend functionality implemented (#82-#92)
- ❌ No dedicated backward compatibility test suite
- ❌ No explicit v0.7.0 behavior regression tests

### Proposed Solution

Create a dedicated test module `tests/test_backward_compatibility.py` that:
1. Loads v0.7.0 reference results (pickled outputs)
2. Runs equivalent v0.8.0+ code with default parameters
3. Asserts numerical equality of forecasts, compartments, R0 calculations

### Acceptance Criteria

#### 1. Reference Data Collection
- [ ] Run v0.7.0 on 5 representative datasets (cumulative COVID, incidence measles, etc.)
- [ ] Save pickled outputs: forecasts, simulations, R0 values
- [ ] Store in `tests/fixtures/v0_7_0_reference/`

#### 2. Compatibility Test Suite
Create `tests/test_backward_compatibility.py` with tests for:
- [ ] **Forecast equivalence**: Same point forecasts for default VAR backend
- [ ] **Confidence intervals**: Same lower/upper bounds (within tolerance)
- [ ] **Simulation results**: Same scenario distributions
- [ ] **R0 calculations**: Identical R0 series and R0 forecasts
- [ ] **Result structure**: Same DataFrame columns, index, dtypes

#### 3. Test Cases
Cover these workflows:
- [ ] Basic SIRD model (COVID-19 cumulative)
- [ ] SIRDV with vaccination (cumulative mode)
- [ ] Incidence mode (measles annual data)
- [ ] Multi-frequency (annual, monthly, weekly, daily)
- [ ] Different forecast horizons (5, 10, 30 steps)

#### 4. Tolerance Specifications
Define acceptable numerical differences:
- [ ] Point forecasts: `np.allclose(atol=1e-6, rtol=1e-5)`
- [ ] Confidence intervals: `np.allclose(atol=1e-5, rtol=1e-4)`
- [ ] R0 values: `np.allclose(atol=1e-3, rtol=1e-3)`
- [ ] Compartment values: Exact integer match for counts

### Implementation Notes

#### Example Test Structure
```python
import pytest
import pickle
import numpy as np
from dynasir import Model, DataContainer

class TestBackwardCompatibility:
    """Ensure v0.8.0+ maintains v0.7.0 behavior."""
    
    @pytest.fixture
    def v0_7_0_covid_result(self):
        """Load v0.7.0 reference output."""
        with open("tests/fixtures/v0_7_0_reference/covid_forecast.pkl", "rb") as f:
            return pickle.load(f)
    
    def test_forecast_equivalence_covid(self, sample_covid_data, v0_7_0_covid_result):
        """Test default VAR behavior matches v0.7.0."""
        # Run current version with default backend
        container = DataContainer(sample_covid_data, mode='cumulative')
        model = Model(container)  # No forecaster param = VAR default
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)
        
        # Compare forecasts
        current_forecast = model.forecasting_box.alpha.point
        reference_forecast = v0_7_0_covid_result['alpha_point']
        
        assert np.allclose(current_forecast, reference_forecast, atol=1e-6, rtol=1e-5)
```

#### Test Execution Strategy
1. **Generate references**: Run once on clean v0.7.0 checkout
2. **Commit fixtures**: Add pickled outputs to git (small files)
3. **Run in CI**: Execute on every PR to catch regressions
4. **Update on breaking changes**: If intentional API change, regenerate fixtures

### Success Criteria

- [ ] 10+ backward compatibility tests passing
- [ ] Tests cover all major workflows (SIRD, SIRDV, cumulative, incidence)
- [ ] CI fails if any compatibility test fails
- [ ] Documentation explains how to update reference fixtures
- [ ] Zero breaking changes detected in default usage

### Blockers

- Need v0.7.0 environment to generate reference data (can use Docker or separate virtualenv)

### Related Issues

- #93: Original tracking issue (from multi-backend epic #97)
- #97: Multi-backend refactoring epic
- Issue #144 (from above): v0.11.0 release preparation (blocker for this)

### Timeline

**Priority**: HIGH (blocker for v0.11.0 release)  
**Estimated Effort**: 2-3 days  
**Target Completion**: Before v0.11.0 release (January 2026)

### References

- Epic: #97 (Phase 4, Issue #93)
- Multi-backend Implementation: PR #xyz (when created)
- Testing Guide: `tests/README.md` (to be created)

---

## Instructions for Manual Creation

Since the GitHub issue write tool is currently disabled, please create these 3 issues manually:

1. Go to https://github.com/julihocc/dynasir/issues/new
2. Copy the title and body content from each issue above
3. Apply the suggested labels
4. Set the appropriate milestone (v0.11.0 for issues 1 and 3)
5. Link related issues as mentioned in each issue body

## Next Steps After Creation

Once these issues are created:
1. Update Epic #108 to reference the new performance issue
2. Update Epic #97 to reference the backward compatibility issue
3. Create a v0.11.0 milestone if it doesn't exist
4. Organize all issues in a GitHub Project board (see next section)
