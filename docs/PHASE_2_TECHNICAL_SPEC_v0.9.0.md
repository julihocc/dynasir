# Phase 2 Technical Specification: v0.9.0

**Document Version**: 1.0  
**Date**: December 7, 2025  
**Author**: GitHub Copilot (based on EPYDEMICS_IMPROVEMENTS.md analysis)  
**Status**: Draft for Review

---

## Executive Summary

Version 0.9.0 implements the core measles integration features identified in Phase 1 analysis. This release moves beyond workarounds to provide native support for annual surveillance data through three major enhancements:

1. **Incidence Mode**: Forecast incident cases (I) directly instead of cumulative totals (C)
2. **Native Multi-frequency**: Model annual/monthly data without artificial daily reindexing
3. **Importation Modeling**: Support eliminated diseases with low R0 but sporadic outbreaks

**Target Release**: Q1 2026 (8-10 weeks development)  
**PyPI Release**: Yes (first comprehensive measles support)

---

## Problem Statement Review

### Current Limitations (v0.8.0)

From `EPYDEMICS_IMPROVEMENTS.md`, the critical blockers are:

1. **Cumulative Assumption**: Requires monotonically increasing C(t), fails for measles patterns like 220 → 55 → 667
2. **Daily Frequency Lock**: Reindexing 40 annual points → 13,516 daily points creates meaningless rates
3. **Epidemic State Assumptions**: Models ongoing transmission (R0 ≈ 1), not eliminated diseases (R0 = 0.23)

### Success Criteria

v0.9.0 succeeds when:
- USA measles 1980-2020 can be modeled without workarounds
- Forecasts predict outbreak probability, not just cumulative totals
- Annual data stays annual (no 365x inflation)
- 100% backward compatibility with COVID-19 workflows

---

## Feature 1: Incidence Mode

### Motivation

**Problem**: Measles annual cases go UP and DOWN (outbreaks vs baseline), but current implementation requires monotonic cumulative C(t).

**Example**:
```python
# Current (cumulative) - FAILS
Year  | C (cumulative) | dC (incident) | Status
2010  |            100 |           100 | OK
2011  |             85 |           -15 | ERROR: C decreased!

# Desired (incidence) - WORKS
Year  | I (incident)   | Notes
2010  |            100 | Baseline
2011  |             85 | Decline (good)
2012  |            650 | Outbreak (predict this!)
```

### Technical Design

#### API Changes

**DataContainer**:
```python
from dynasir import DataContainer

# v0.8.0 (default cumulative mode)
container = DataContainer(data, mode='cumulative')  # Default

# v0.9.0 (new incidence mode)
container = DataContainer(data, mode='incidence')
```

**Input Data Format**:
```python
# Incidence mode expects:
data = pd.DataFrame({
    'I': [100, 85, 650, 70],      # Incident cases (can vary)
    'D': [5, 3, 12, 4],            # Deaths
    'N': [1000000] * 4,            # Population
    'date': pd.date_range('2010', periods=4, freq='YE')
})
```

#### Feature Engineering Changes

**Current (Cumulative)**:
```python
def feature_engineering(data):
    # Assumes C is cumulative, always increasing
    R = C.shift(14) - D  # Recovered
    I = C - R - D        # Infected (active)
    S = N - I - R - D    # Susceptible
    # ... rates from dC = diff(C)
```

**New (Incidence)**:
```python
def feature_engineering(data, mode='cumulative'):
    if mode == 'cumulative':
        # Current logic (backward compatible)
        dC = C.diff()
        R = C.shift(14) - D
        I = C - R - D
        S = N - I - R - D
        
    elif mode == 'incidence':
        # I is already incident cases (input column)
        dC = I  # Incident cases per period
        C = I.cumsum()  # Calculate cumulative if needed
        
        # Recovered: cumulative incident minus deaths, lagged
        R = I.shift(RECOVERY_LAG).cumsum() - D
        R = R.clip(lower=0)  # Can't be negative
        
        # Susceptible: remaining population
        S = N - C - D  # Simplified (assumes no recovered flow back)
        
        # Active: incident cases this period
        # (In annual data, represents avg active during year)
        A = S + I  # Active population for rate calculations
```

**Key Differences**:
- Input `I` is incident, not derived from `diff(C)`
- `C` calculated as `cumsum(I)` if needed
- `R` calculation simplified (cumulative incident minus deaths)
- Forecasting targets `I` (not `C`)

#### Forecasting Changes

**Current**: Forecast logit(α, β, γ) → inverse → future C values

**New (Incidence)**: Forecast logit(α, β, γ) → inverse → future I values

```python
# In VARForecasting.forecast()
if self.mode == 'incidence':
    # After inverse logit, reconstruct I (not C)
    forecasted_I = # ... simulation based on rates
    forecasting_box.I = forecasted_I  # Primary forecast
    forecasting_box.C = forecasted_I.cumsum()  # Derived
else:
    # Current behavior (forecast C)
    forecasting_box.C = forecasted_C  # Primary forecast
```

#### Validation

**New Validation Rules**:
```python
def validate_incidence_data(data):
    """Validate data for incidence mode."""
    required_cols = ['I', 'D', 'N']  # I instead of C
    
    if 'I' not in data.columns:
        raise ValueError(
            "Incidence mode requires 'I' (incident cases) column. "
            "Current data has columns: {list(data.columns)}"
        )
    
    # I can be zero (no cases that year)
    if (data['I'] < 0).any():
        raise ValueError("Incident cases 'I' cannot be negative")
    
    # No monotonic requirement (this is the point!)
    # I can go up and down
```

### Implementation Plan

**Files to Modify**:
1. `src/dynasir/data/container.py`: Add `mode` parameter
2. `src/dynasir/data/features.py`: Dual-mode feature engineering
3. `src/dynasir/data/validation.py`: Add `validate_incidence_data()`
4. `src/dynasir/models/sird.py`: Pass mode to forecasting/simulation
5. `src/dynasir/models/simulation.py`: Handle incidence-based simulation

**New Files**:
- `src/dynasir/models/incidence.py`: Incidence-specific utilities (optional)

**Tests**:
- `tests/unit/data/test_incidence_mode.py`: Feature engineering tests
- `tests/integration/test_incidence_workflow.py`: End-to-end measles workflow
- `tests/integration/test_backward_compatibility.py`: Ensure COVID still works

**Estimated Effort**: 40-50 hours (2-3 weeks)

---

## Feature 2: Native Multi-frequency Support

### Motivation

**Problem**: Annual data → daily reindex creates 365 identical values per year, producing meaningless rates.

**Current (v0.8.0)**:
```
Input: 40 annual points (1980-2020)
↓ reindex(freq='D')
Output: 13,516 daily points (365 per year forward-filled)
↓ diff() for rates
Result: 364 days of rate=0, then 1 spike
```

**Desired (v0.9.0)**:
```
Input: 40 annual points (1980-2020)
↓ NO reindexing
Processing: 40 annual points
↓ Annual rates
Result: 40 annual α, β, γ rates (meaningful)
```

### Technical Design

#### API Changes

**DataContainer**:
```python
# v0.8.0 - everything becomes daily
container = DataContainer(data, window=7)  # Daily smoothing

# v0.9.0 - respect native frequency
container = DataContainer(
    data, 
    frequency='annual',  # Or 'monthly', 'weekly', 'daily'
    window=1             # Window in native frequency units
)
```

**Frequency Detection Enhancement**:
```python
# Current: detect but still reindex to daily
detected = detect_frequency(data)  # Returns 'Y'
# Still does: reindex(freq='D') → warning

# New: detect and preserve
detected = detect_frequency(data)
if detected == 'Y':
    # Process as annual, no reindexing
    freq_handler = AnnualFrequencyHandler(data)
elif detected == 'M':
    freq_handler = MonthlyFrequencyHandler(data)
# ... etc
```

#### Frequency Handler Design

**Base Class**:
```python
class FrequencyHandler(ABC):
    """Abstract base for frequency-specific data handling."""
    
    @abstractmethod
    def get_lag_default(self) -> int:
        """Return appropriate lag for this frequency."""
        pass
    
    @abstractmethod
    def calculate_rates(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate α, β, γ in this frequency."""
        pass
    
    @abstractmethod
    def reindex_if_needed(self, data: pd.DataFrame) -> pd.DataFrame:
        """Reindex only if necessary (e.g., gaps in data)."""
        pass
```

**Annual Implementation**:
```python
class AnnualFrequencyHandler(FrequencyHandler):
    def get_lag_default(self) -> int:
        return 1  # 1 year lag for recovery
    
    def calculate_rates(self, data: pd.DataFrame) -> pd.DataFrame:
        # No diff() → no artificial zeros
        # Calculate rates from annual changes
        
        # For annual: C(t) - C(t-1) = incident cases in year t
        dC = data['C'].diff()  # Annual incident
        dR = data['R'].diff()
        dD = data['D'].diff()
        
        # Rates are annual (not daily)
        alpha = (data['A'] * dC) / (data['I'] * data['S'])
        beta = dR / data['I']
        gamma = dD / data['I']
        
        return prepare_for_logit_function(
            pd.DataFrame({'alpha': alpha, 'beta': beta, 'gamma': gamma})
        )
    
    def reindex_if_needed(self, data: pd.DataFrame) -> pd.DataFrame:
        # Only fill gaps (missing years), don't inflate to daily
        if data.index.freq != 'YE':
            # Ensure annual index
            data = data.asfreq('YE')
        return data.ffill()  # Fill missing years only
```

#### VAR Lag Selection

**Current**: `max_lag=10` assumes daily data (10 days)

**New**: Frequency-aware lag selection
```python
def fit_model(self, max_lag=None, ic='aic'):
    if max_lag is None:
        # Auto-select based on frequency
        max_lag = self.frequency_handler.get_default_lag()
        # Annual: 3-5 years
        # Monthly: 6-12 months
        # Weekly: 4-8 weeks
        # Daily: 7-14 days
    
    # Ensure max_lag doesn't exceed data length
    max_lag = min(max_lag, len(self.data) // 3)
    
    # Standard VAR lag selection
    selector = self.var_model.select_order(maxlags=max_lag)
    optimal_lag = getattr(selector, ic)
```

#### Forecasting Output

**Current**: Always returns daily forecasts

**New**: Returns forecasts in native frequency
```python
# Annual data → annual forecasts (no aggregation needed!)
model.forecast(steps=10)  # 10 years, not 10 days

# Model knows it's annual, interprets steps correctly
# forecasting_interval has 10 annual dates
```

### Implementation Plan

**Files to Modify**:
1. `src/dynasir/data/container.py`: Add `frequency` parameter
2. `src/dynasir/data/preprocessing.py`: Conditional reindexing
3. `src/dynasir/data/features.py`: Frequency-aware rate calculation
4. `src/dynasir/models/sird.py`: Accept frequency from container
5. `src/dynasir/models/forecasting/var.py`: Frequency-aware lag selection

**New Files**:
- `src/dynasir/data/frequency_handlers.py`: FrequencyHandler classes
- `src/dynasir/core/constants.py`: Update RECOVERY_LAG_BY_FREQUENCY

**Tests**:
- `tests/unit/data/test_frequency_handlers.py`: Each handler class
- `tests/integration/test_native_annual.py`: End-to-end annual workflow
- `tests/integration/test_native_monthly.py`: Monthly surveillance data

**Estimated Effort**: 50-60 hours (3-4 weeks)

---

## Feature 3: Importation Modeling

### Motivation

**Problem**: USA measles has R0 = 0.23 (well below 1), but outbreaks still occur due to imported cases and vaccine hesitancy pockets.

**Current Model**:
```
dI/dt = (R0 - 1) * I
If R0 < 1: I → 0 (epidemic dies out)
Forecast: Zero cases forever (WRONG for measles)
```

**Reality**:
```
USA: ~50-100 baseline cases/year from importation
Outbreaks: Local amplification when vaccine coverage drops
Need: Model both importation and local transmission
```

### Technical Design

#### API Changes

**Model Initialization**:
```python
from dynasir import Model

# v0.8.0 - no importation
model = Model(container, start='1980', stop='2015')

# v0.9.0 - with importation
model = Model(
    container, 
    start='1980', 
    stop='2015',
    importation_rate=5.0,  # Expected imported cases per time unit
    importation_variance=2.0  # Optional: stochasticity
)
```

#### Simulation Dynamics

**Modified SIRD Equations**:
```python
# Current (no importation)
dS = -alpha * S * I / A
dI = alpha * S * I / A - beta * I - gamma * I
dR = beta * I
dD = gamma * I

# New (with importation)
importation = np.random.poisson(importation_rate)  # Poisson distributed

dS = -alpha * S * I / A
dI = alpha * S * I / A - beta * I - gamma * I + importation  # Add imports
dR = beta * I
dD = gamma * I

# Key: importation adds to dI regardless of R0
# Enables outbreaks even when R0 << 1
```

**Implementation in Simulation**:
```python
class EpidemicSimulation:
    def __init__(
        self, 
        data, 
        forecasting_box, 
        forecasting_interval,
        importation_rate=0.0,  # Default: no importation
        importation_variance=0.0
    ):
        self.importation_rate = importation_rate
        self.importation_variance = importation_variance
    
    def _calculate_next_step(self, current_state, rates):
        """One time step of SIRD dynamics."""
        S, I, R, D, A = current_state
        alpha, beta, gamma = rates
        
        # Standard SIRD flows
        new_infections = alpha * S * I / A
        new_recoveries = beta * I
        new_deaths = gamma * I
        
        # Importation (eliminated diseases)
        if self.importation_rate > 0:
            if self.importation_variance > 0:
                # Stochastic importation
                imported = np.random.normal(
                    self.importation_rate,
                    self.importation_variance
                )
                imported = max(0, imported)  # Can't be negative
            else:
                # Deterministic importation
                imported = self.importation_rate
        else:
            imported = 0
        
        # Update compartments
        dS = -new_infections
        dI = new_infections - new_recoveries - new_deaths + imported
        dR = new_recoveries
        dD = new_deaths
        
        return (S + dS, I + dI, R + dR, D + dD, A + dS + dI)
```

#### Interpretation

**R0 with Importation**:
```python
# Effective reproduction when importation present
R_effective = R0 + (importation_rate / I_baseline)

# Example (measles):
# R0 = 0.23 (local transmission insufficient)
# importation_rate = 5 cases/year
# I_baseline ≈ 50 cases/year
# R_effective ≈ 0.23 + (5/50) = 0.33

# Still < 1, but importation maintains endemic level
```

### Implementation Plan

**Files to Modify**:
1. `src/dynasir/models/sird.py`: Add `importation_rate` parameter
2. `src/dynasir/models/simulation.py`: Modify `_calculate_next_step()`
3. `src/dynasir/analysis/evaluation.py`: Interpret R0 with importation

**New Files**:
- `src/dynasir/models/importation.py`: Importation modeling utilities

**Tests**:
- `tests/unit/models/test_importation.py`: Simulation dynamics with imports
- `tests/integration/test_eliminated_disease.py`: Measles/polio scenarios
- `tests/unit/models/test_importation_stochastic.py`: Variance handling

**Documentation**:
- When to use importation modeling (R0 < 1 scenarios)
- Calibrating importation_rate from surveillance data
- Interpreting forecasts for eliminated diseases

**Estimated Effort**: 20-25 hours (1-1.5 weeks)

---

## Migration Path from v0.8.0

### For Existing Users (COVID-19)

**No changes required** - v0.9.0 is 100% backward compatible:

```python
# v0.8.0 code works unchanged in v0.9.0
from dynasir import DataContainer, Model

container = DataContainer(covid_data)  # mode='cumulative' (default)
model = Model(container, start='2020-01-01', stop='2020-12-31')
model.create_model()
model.fit_model(max_lag=10)
model.forecast(steps=30)  # 30 days (default frequency='D')
```

### For New Users (Measles)

**v0.8.0 (Workaround)**:
```python
# Suppress warnings, use temporal aggregation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*FREQUENCY MISMATCH.*")
    container = DataContainer(measles_annual_data, window=1)

model = Model(container, start='1980', stop='2015')
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=365*10)  # 10 years in days
model.run_simulations()
model.generate_result()

# Aggregate back to annual
annual_forecast = model.aggregate_forecast('C', target_frequency='Y', aggregate_func='last')
```

**v0.9.0 (Native)**:
```python
# No warnings, native annual support
container = DataContainer(
    measles_annual_data, 
    mode='incidence',      # I can vary up/down
    frequency='annual',    # Native annual processing
    window=1               # 1-year smoothing
)

model = Model(
    container, 
    start='1980', 
    stop='2015',
    importation_rate=5.0   # ~5 imported cases/year
)
model.create_model()
model.fit_model(max_lag=5)     # 5 years
model.forecast(steps=10)        # 10 years (not days!)
model.run_simulations()
model.generate_result()

# Already annual - no aggregation needed!
annual_forecast = model.results['I']  # Direct incident cases
```

### Deprecation Policy

**v0.9.0**: 
- `aggregate_forecast()` remains but not needed for native frequencies
- Frequency mismatch warnings still emitted for `mode='cumulative'` with annual data

**v1.0.0** (Future):
- May deprecate `aggregate_forecast()` in favor of native frequency support
- Warnings become errors for mismatched frequencies

---

## Testing Strategy

### Unit Tests (150+ new tests)

**Incidence Mode**:
- Feature engineering with incident input
- I can decrease (not fail validation)
- Forecasts return future I values
- Cumulative C derived correctly
- Edge cases: zero incident years

**Native Multi-frequency**:
- FrequencyHandler for each supported frequency
- Lag selection scales with frequency
- No artificial reindexing
- Rate calculations in native frequency
- Index frequency preservation

**Importation Modeling**:
- Simulation dynamics with imports
- Deterministic vs stochastic importation
- R0 < 1 scenarios don't forecast to zero
- Importation rate calibration

### Integration Tests (20+ new tests)

**End-to-End Workflows**:
1. USA measles 1980-2020 (incidence + annual + importation)
2. Pertussis cyclical patterns (incidence + monthly)
3. Influenza seasonality (incidence + weekly)
4. COVID-19 unchanged (cumulative + daily, no importation)

**Backward Compatibility**:
- All v0.7.0 and v0.8.0 examples still work
- No breaking API changes
- Default behavior unchanged

### Validation Against Real Data

**Test Datasets**:
1. **Measles** (USA 1980-2020): CDC annual surveillance
2. **Pertussis** (USA 1950-2020): 3-5 year cycles
3. **Influenza** (USA 2010-2020): Weekly ILI surveillance
4. **Dengue** (Florida 2015-2020): Importation + local

**Success Metrics**:
- RMSE on incident cases (not cumulative)
- Outbreak detection rate (sensitivity)
- False alarm rate (specificity)
- Forecast calibration (predicted vs observed)

### Benchmarking

**Compare Against**:
- EpiEstim (R package) - R0 estimation
- Prophet (Facebook) - time series forecasting
- statsmodels ARIMA - classical time series
- Classical SEIR models - compartmental dynamics

**DynaSIR Should**:
- Match SEIR on compartmental dynamics
- Match Prophet on seasonal patterns
- Outperform ARIMA on outbreak detection
- Provide more interpretable forecasts than black-box ML

---

## Implementation Timeline

### Phase 2.1: Incidence Mode (Weeks 1-3)

**Week 1**: Design & validation
- Finalize API design
- Write validation logic
- Create test fixtures (measles data)

**Week 2**: Feature engineering
- Implement dual-mode feature_engineering()
- Update DataContainer
- Unit tests for incidence calculations

**Week 3**: Forecasting integration
- Modify VARForecasting for incidence mode
- Update simulation engine
- Integration tests

**Deliverable**: Incidence mode working, 50+ tests passing

### Phase 2.2: Native Multi-frequency (Weeks 4-7)

**Week 4**: Frequency handlers
- Design FrequencyHandler base class
- Implement AnnualFrequencyHandler
- Unit tests for handlers

**Week 5**: Preprocessing changes
- Conditional reindexing logic
- Frequency-aware smoothing
- Update constants

**Week 6**: Forecasting changes
- Frequency-aware lag selection
- Native frequency output
- Update Model class

**Week 7**: Testing & refinement
- Integration tests (annual/monthly/weekly)
- Performance optimization
- Edge case handling

**Deliverable**: Native annual support, no reindexing artifacts

### Phase 2.3: Importation Modeling (Week 8)

**Week 8**: Implementation
- Add importation_rate parameter
- Modify simulation dynamics
- Stochastic importation option
- Tests for R0 < 1 scenarios

**Deliverable**: Importation modeling functional

### Phase 2.4: Documentation & Release (Weeks 9-10)

**Week 9**: Documentation
- Update USER_GUIDE.md
- Create migration guide
- Update API reference
- Write measles tutorial notebook

**Week 10**: Release preparation
- Final testing (all 450+ tests)
- Backward compatibility verification
- Performance profiling
- CHANGELOG.md update
- PyPI release preparation

**Deliverable**: v0.9.0 ready for PyPI release

---

## Risk Assessment

### High Risk

**1. Breaking Backward Compatibility**
- Mitigation: Extensive backward compatibility tests
- Mitigation: Default behavior unchanged (cumulative + daily)
- Mitigation: Beta testing with COVID-19 users

**2. Feature Engineering Complexity**
- Risk: Dual-mode logic introduces bugs
- Mitigation: Separate code paths with clear switches
- Mitigation: Comprehensive unit tests for each mode

### Medium Risk

**3. Frequency Handler Complexity**
- Risk: Annual/monthly/weekly edge cases
- Mitigation: Base class enforces interface
- Mitigation: Progressive rollout (annual first, then monthly)

**4. Importation Model Accuracy**
- Risk: Hard to calibrate importation_rate from data
- Mitigation: Provide calibration utilities
- Mitigation: Document use cases and limitations

### Low Risk

**5. Performance Regression**
- Risk: Additional conditionals slow down processing
- Mitigation: Profile before/after
- Mitigation: Cache frequency detection results

---

## Success Metrics

### Functional Requirements

- [ ] USA measles 1980-2020 models without workarounds
- [ ] Annual data stays annual (no 365x inflation)
- [ ] Incident cases can go up/down (not monotonic)
- [ ] R0 < 1 scenarios don't forecast to zero
- [ ] All v0.7.0/v0.8.0 examples still work

### Performance Requirements

- [ ] Processing time < 2x v0.8.0 for daily data
- [ ] Memory usage unchanged
- [ ] Test suite < 10 minutes

### Quality Requirements

- [ ] 450+ tests passing (100% pass rate)
- [ ] Code coverage > 85%
- [ ] No breaking API changes
- [ ] Documentation complete (USER_GUIDE + API docs)

---

## Post-v0.9.0 Roadmap (v1.0.0)

### Phase 3 Features (Optional)

**Coverage-Based SIRDV**:
- Input vaccination_coverage % (not cumulative V)
- Model waning immunity (V → S flow)
- Herd immunity thresholds
- Scenario analysis: 90% vs 95% coverage

**Outbreak Detection Module**:
- Classify baseline vs outbreak periods
- Probabilistic outbreak forecasts
- Outbreak-specific metrics (detection rate, false alarms)

**Scenario Analysis Framework**:
- `forecast_scenarios()` for multi-parameter sets
- Compare importation 0.1 vs 0.5 vs 1.0
- Visualize scenario overlays

### Long-term Vision

**v1.0.0**: "The epidemiological forecasting toolkit"
- COVID-19: Excellent (already proven)
- Measles: Excellent (v0.9.0)
- Influenza: Good (v0.9.0 + seasonal)
- Pertussis: Good (v0.9.0 + endemic)
- Generic: Extensible for any infectious disease

---

## Appendix A: API Reference Summary

### DataContainer (v0.9.0)

```python
DataContainer(
    raw_data: pd.DataFrame,
    window: int = 7,
    mode: str = 'cumulative',      # NEW: 'cumulative' or 'incidence'
    frequency: str = None,          # NEW: 'D', 'W', 'M', 'Y', or auto-detect
)
```

### Model (v0.9.0)

```python
Model(
    data_container: DataContainer,
    start: Optional[str] = None,
    stop: Optional[str] = None,
    days_to_forecast: Optional[int] = None,
    forecaster: str = 'var',
    importation_rate: float = 0.0,  # NEW: imported cases per time unit
    importation_variance: float = 0.0,  # NEW: stochastic variation
    **forecaster_kwargs
)
```

### Key Methods (Unchanged)

```python
model.create_model()
model.fit_model(max_lag=None, ic='aic')  # max_lag now frequency-aware
model.forecast(steps=30)  # steps interpreted by frequency
model.run_simulations(n_jobs=None)
model.generate_result()
model.visualize_results(compartment_code, testing_data, log_response)
model.evaluate_forecast(testing_data, compartment_codes)
```

---

## Appendix B: Example Use Cases

### Case 1: USA Measles (Eliminated Disease)

```python
import pandas as pd
from dynasir import DataContainer, Model

# Annual incident cases (can vary)
measles_data = pd.DataFrame({
    'I': [100, 85, 220, 650, 70, 55],  # Incident cases (up/down)
    'D': [5, 3, 8, 12, 4, 3],
    'N': [300_000_000] * 6,
    'date': pd.date_range('2015', periods=6, freq='YE')
}).set_index('date')

container = DataContainer(
    measles_data,
    mode='incidence',       # I can vary
    frequency='annual',     # Native annual
    window=1                # 1-year smoothing
)

model = Model(
    container,
    start='2015',
    stop='2018',
    importation_rate=5.0,   # ~5 imported cases/year
    importation_variance=2.0
)

model.create_model()
model.fit_model(max_lag=3)  # 3 years
model.forecast(steps=5)      # 5 years
model.run_simulations()
model.generate_result()

# Forecast already annual - direct access
forecast = model.results['I']
print(f"Expected cases 2019: {forecast.loc['2019', 'mean']:.0f}")
```

### Case 2: Pertussis (Cyclical Endemic)

```python
# Monthly incident cases with 3-5 year cycles
pertussis_data = pd.DataFrame({
    'I': monthly_cases,  # 240 months (20 years)
    'D': monthly_deaths,
    'N': [10_000_000] * 240,
    'date': pd.date_range('2000-01', periods=240, freq='ME')
}).set_index('date')

container = DataContainer(
    pertussis_data,
    mode='incidence',
    frequency='monthly',
    window=3  # 3-month smoothing
)

model = Model(container, importation_rate=0.5)  # Low importation
model.create_model()
model.fit_model(max_lag=12)  # 12 months
model.forecast(steps=24)      # 2 years ahead
```

### Case 3: COVID-19 (Unchanged)

```python
# v0.7.0/v0.8.0 code works without modification
from dynasir import DataContainer, Model, process_data_from_owid

raw_data = process_data_from_owid(iso_code="USA")
container = DataContainer(raw_data, window=7)  # Defaults OK

model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_model()
model.fit_model(max_lag=10)
model.forecast(steps=30)
```

---

## Appendix C: Decision Log

### Design Decisions

**1. Why `mode` parameter instead of auto-detect?**
- Decision: Explicit `mode='incidence'` required
- Rationale: Ambiguous data could be either (cumulative with decline, or incident)
- Alternative rejected: Auto-detect from monotonicity (too error-prone)

**2. Why separate `frequency` from `mode`?**
- Decision: Orthogonal parameters
- Rationale: `mode` = data type (cumulative vs incident), `frequency` = temporal resolution
- Example: Can have daily incident data or annual incident data

**3. Why Poisson for importation?**
- Decision: `np.random.poisson(importation_rate)` by default
- Rationale: Importation events are rare, countable → Poisson is natural
- Alternative: Normal distribution (if importation_variance specified)

**4. Why not deprecate `aggregate_forecast()` in v0.9.0?**
- Decision: Keep for transition period
- Rationale: Users may have v0.8.0 workflows with aggregation
- Future: Deprecate in v1.0.0 when native frequencies mature

---

## Sign-Off

This specification is ready for:
- [ ] Technical review by maintainers
- [ ] Community feedback (GitHub Discussions)
- [ ] Implementation kickoff

**Next Step**: Create GitHub issues for each feature (Incidence Mode, Native Multi-frequency, Importation Modeling) and assign to v0.9.0 milestone.
