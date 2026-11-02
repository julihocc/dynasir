# API Consistency Audit - Priority 3

**Date:** November 26, 2025  
**Branch:** Priority-3--Code-Quality  
**Version:** 0.6.1-dev  

## Audit Summary

### Test Coverage
- **Total Tests:** 141 test functions
- **Target Coverage:** 80%+ (to be measured)

### Core Classes Audited

#### 1. Model (src/dynasir/models/sird.py)
Main user-facing API class.

**Public Methods:**
- `__init__(data_container, start, stop, days_to_forecast)` ✅
- `create_model(*args, **kwargs)` ✅ Main API
- `create_logit_ratios_model(*args, **kwargs)` ⚠️ Deprecated (v0.8.0)
- `fit_model(*args, **kwargs)` ✅ Main API
- `fit_logit_ratios_model(*args, **kwargs)` ⚠️ Deprecated (v0.8.0)
- `forecast(steps, **kwargs)` ✅ Main API
- `forecast_logit_ratios(steps, **kwargs)` ⚠️ Deprecated (v0.8.0)
- `run_simulations(n_jobs)` ✅ New in v0.6.0
- `generate_result()` ✅
- `calculate_R0()` ✅ Returns pd.Series
- `forecast_R0()` ✅ Returns pd.DataFrame
- `visualize_results(compartment, testing_data, log_response)` ✅
- `evaluate_forecast(testing_data)` ✅

**Properties:**
- `logit_ratios_model` ⚠️ Backward compatibility
- `logit_ratios_model_fitted` ⚠️ Backward compatibility

**API Status:** ✅ Consistent - modern names without "logit_ratios" prefix

#### 2. BaseModel (src/dynasir/models/base.py)
Abstract base for model interfaces.

**Abstract Methods:**
- `create_model(*args, **kwargs)` ✅
- `fit_model(*args, **kwargs)` ✅
- `forecast(steps, **kwargs)` ✅
- `run_simulations(n_jobs)` ✅
- `evaluate_forecast(testing_data)` ✅
- `visualize_results(compartment, testing_data, log_response)` ✅

**Utility Methods:**
- `get_sird_compartments()` ✅
- `get_sird_rates()` ✅
- `get_logit_rates()` ✅
- `validate_sird_data(data)` ✅

**API Status:** ✅ Consistent interface

#### 3. VARForecaster (src/dynasir/models/forecasting/var.py)
Internal forecasting engine.

**Public Methods:**
- `__init__(data)` ✅
- `create_model()` ✅
- `fit(*args, **kwargs)` ✅
- `forecast_interval(steps, alpha, simulation_ci)` ✅

**API Status:** ✅ Clean internal API

#### 4. EpidemicSimulation (src/dynasir/models/simulation.py)
Parallel Monte Carlo simulation engine.

**Public Methods:**
- `__init__(data, forecasting_box, forecasting_interval)` ✅
- `simulate_for_given_levels(levels)` ✅
- `create_simulation_box()` ✅
- `run_simulations(n_jobs)` ✅ Parallel support v0.6.0
- `create_results_dataframe(compartment)` ✅
- `generate_result()` ✅

**Module Function:**
- `_run_single_simulation(...)` ✅ Picklable for multiprocessing

**API Status:** ✅ Consistent with parallelization

## Findings

### ✅ Strengths
1. **Modern API names:** Main methods use clean names without legacy prefixes
2. **Backward compatibility:** Deprecated methods properly warn users
3. **Parallel support:** New `n_jobs` parameter consistently added
4. **Delegation pattern:** Model class delegates to VARForecasting and EpidemicSimulation
5. **Type hints:** Present in most method signatures

### ⚠️ Areas for Improvement

#### 1. Docstring Completeness
**Status:** INCOMPLETE  
**Priority:** HIGH

Many methods lack examples:
- `Model.create_model()` - No example
- `Model.fit_model()` - No example
- `Model.forecast()` - No example
- `Model.run_simulations()` - No parallel example
- `Model.calculate_R0()` - No example
- `Model.forecast_R0()` - No example

**Action:** Add comprehensive examples to all public methods

#### 2. Type Hints Coverage
**Status:** PARTIAL  
**Priority:** MEDIUM

Some methods use `*args, **kwargs` without documenting types:
- `Model.create_model(*args, **kwargs)` - No args actually used
- `Model.fit_model(*args, **kwargs)` - Should specify `max_lag: int`, `ic: str`

**Action:** Replace generic signatures with explicit parameters

#### 3. Return Type Annotations
**Status:** INCOMPLETE  
**Priority:** MEDIUM

Methods missing explicit return types:
- `Model.generate_result()` - Returns None but not annotated
- `EpidemicSimulation.create_simulation_box()` - Returns None but not annotated

**Action:** Add explicit `-> None` or proper return types

#### 4. Legacy Property Names
**Status:** ACCEPTABLE  
**Priority:** LOW

Properties for backward compatibility:
- `Model.logit_ratios_model` 
- `Model.logit_ratios_model_fitted`

These are acceptable for v0.6.x but should be documented as deprecated.

**Action:** Add deprecation notices in docstrings

## Priority 3 Action Items

### Task 1: Complete Docstrings with Examples
**Files:**
- `src/dynasir/models/sird.py`
- `src/dynasir/models/base.py`
- `src/dynasir/models/simulation.py`
- `src/dynasir/models/forecasting/var.py`

**Template:**
```python
def method_name(self, param: type) -> ReturnType:
    """
    Brief description.

    Detailed explanation of what the method does, including any important
    algorithm details or mathematical foundations.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When it's raised

    Example:
        >>> from dynasir import DataContainer, Model
        >>> container = DataContainer(data, window=7)
        >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
        >>> model.method_name(param)
    """
```

### Task 2: Enhance Type Hints
**Files:**
- `src/dynasir/models/sird.py`

**Changes:**
```python
# Before:
def fit_model(self, *args, **kwargs) -> None:

# After:
def fit_model(self, max_lag: int = 10, ic: str = "aic") -> None:
```

### Task 3: Add Test Coverage Measurement
**Command:**
```bash
pytest --cov=src/dynasir --cov-report=html --cov-report=term
```

**Target:** 80%+ coverage

### Task 4: Document Deprecated Methods
**Files:**
- `src/dynasir/models/sird.py`

Add deprecation timeline to docstrings.

## API Stability Commitment

### Stable API (v0.6.x → v1.0.0)
These methods will NOT change:
- `Model.create_model()`
- `Model.fit_model()`
- `Model.forecast()`
- `Model.run_simulations()`
- `Model.calculate_R0()`
- `Model.forecast_R0()`

### Deprecated API (Remove in v0.8.0)
These methods have 2 version grace period:
- `Model.create_logit_ratios_model()` → use `create_model()`
- `Model.fit_logit_ratios_model()` → use `fit_model()`
- `Model.forecast_logit_ratios()` → use `forecast()`

### Internal API (May Change)
Not guaranteed stable:
- `VARForecasting` internal methods
- `EpidemicSimulation` internal methods
- `_run_single_simulation()` function signature

## Next Steps

1. ✅ Complete this API audit document
2. ⏸️ Add comprehensive docstring examples (Task 1)
3. ⏸️ Enhance type hints (Task 2)
4. ⏸️ Measure test coverage (Task 3)
5. ⏸️ Complete deprecation documentation (Task 4)
6. ⏸️ Run full test suite
7. ⏸️ Update TUTORIAL.md with all public methods
