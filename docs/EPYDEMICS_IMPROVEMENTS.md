# Insights for Improving DynaSIR: Annual Surveillance Data Support

## Executive Summary

DynaSIR (v0.7.0) works excellently for COVID-19 but struggles with annual surveillance data like measles. This document provides actionable insights for extending dynasir to handle eliminated/endemic diseases with annual reporting.

**Author Context**: Analysis based on attempting to model North American measles data (1980-2020) using dynasir.

---

## Problem 1: Cumulative vs Incident Data Philosophy

### Current Design (COVID-19)
- Input: Cumulative confirmed cases (C) - always increasing
- Calculation: `dC = diff(C)` for daily incidence
- Forecast: Future cumulative totals
- Goal: "What will total cases reach?"

### Measles Reality
- Available: Annual incident cases (new cases per year)
- Pattern: Goes up AND down (outbreaks vs elimination)
- Forecast need: "How many new cases next year?"
- Goal: Predict outbreak risk, not cumulative totals

### Example Data Comparison

**COVID (what dynasir expects):**
```
Date       | Cumulative | Daily New | Notes
2020-03-01 |        100 |       100 | Growing
2020-03-02 |        250 |       150 | Always up
2020-03-03 |        450 |       200 | Monotonic
```

**Measles (what we have):**
```
Year | Annual Cases | Notes
2010 |           63 | Baseline
2011 |          220 | Outbreak
2012 |           55 | Back to baseline
2013 |          187 | Small outbreak
2014 |          667 | Major outbreak (Disneyland)
2015 |          188 | Declining
2016 |           85 | Low
```

### Proposed Solution

**Add `mode` parameter to DataContainer:**
```python
container = DataContainer(
    data,
    mode='cumulative',  # Current default (COVID)
    # OR
    mode='incidence'    # New option (Measles)
)
```

**Behavior:**
- `mode='cumulative'`: Current behavior
  - Input C must be monotonic increasing
  - Calculate dC = diff(C)
  - Forecast future C values

- `mode='incidence'`: New behavior
  - Input I = incident cases (can vary)
  - Calculate C = cumsum(I) if needed
  - Forecast future I values (not C)
  - Allow I to go up/down in forecasts

---

## Problem 2: Time Frequency Mismatch

### Current Assumption
- Data is daily (or can be meaningfully interpolated to daily)
- Reindexing from annual to daily creates 13,516 daily points from 40 annual points
- Forward-fill creates 365 identical days per year

### What Happens to Measles Data

**Input (annual):**
```
1980-07-01: 13,506 cases
1981-07-01:  3,124 cases
1982-07-01:  1,714 cases
```

**After reindex to daily:**
```
1980-07-01: 13,506 cases
1980-07-02: 13,506 cases  (forward-filled)
1980-07-03: 13,506 cases  (forward-filled)
...
1981-06-30: 13,506 cases  (365 days same value!)
1981-07-01: 16,630 cases  (step function!)
```

**Calculated rates are meaningless:**
- Alpha, beta, gamma derived from artificial daily patterns
- Step functions create spiky rates
- VAR model forecasts these artificial patterns

### Proposed Solutions

**Option A: Native Annual Support**
```python
container = DataContainer(
    data,
    frequency='annual'  # Don't reindex to daily
)

model = Model(
    container,
    start='1980',      # Year instead of date
    stop='2015',
    periods_to_forecast=10  # 10 years, not days
)
```

**Option B: Aggregation-Aware Forecasting**
```python
container = DataContainer(
    data,
    source_frequency='annual',
    model_frequency='daily',  # Internal modeling
    forecast_frequency='annual'  # Aggregate forecasts back
)
```

**Option C: Explicit Temporal Aggregation**
```python
model.forecast(
    steps=365*10,  # 10 years in days
    aggregate='annual',  # Return annual forecasts
    aggregate_func='sum'  # Sum daily to annual
)
```

---

## Problem 3: Epidemic State Assumptions

### Current Design (Ongoing Epidemic)
- Assumes active transmission (R0 near or above 1)
- Models continuous infection dynamics
- Forecasts next wave

### Measles Reality (Eliminated Disease)
- USA: R0 = 0.23 (well below 1)
- Endemic transmission interrupted
- Cases are mostly importations + small outbreaks
- Zero cases possible (and common)

### R0 Interpretation Issues

**Current dynasir output:**
```
USA R0 = 0.23
```

**What this means:**
- Measles is eliminated (correct!)
- Each case infects 0.23 others on average
- Epidemic is dying out (true)

**But for forecasting:**
- R0 < 1 means "forecast to zero"
- Misses outbreak risk from importations
- Doesn't model sporadic resurgence
- Can't predict vaccine hesitancy impact

### Proposed Solutions

**Add Importation Parameter:**
```python
model = Model(
    container,
    importation_rate=0.1,  # Expected imported cases per time unit
    # Models: I(t+1) = R0 * I(t) + importation
)
```

**Add Stochastic Outbreak Module:**
```python
model = Model(
    container,
    outbreak_model='poisson',  # Random outbreak timing
    baseline_rate=50,          # Expected annual baseline
    outbreak_prob=0.1          # Probability of outbreak year
)
```

---

## Problem 4: Vaccination Modeling

### Current SIRDV Implementation
- V = cumulative vaccinated (always increasing)
- Delta (δ) = vaccination rate (dV/dt)
- Works well for vaccine rollout (COVID)

### Measles Vaccination Reality
- Routine childhood immunization (ongoing for decades)
- Coverage percentage (e.g., 95% of birth cohort)
- Need: Model coverage maintenance vs dropout

### Current Approach (in notebook)
```python
# Estimate cumulative vaccinated from coverage %
birth_cohort = population / life_expectancy
annual_vaccinated = coverage_pct * birth_cohort
V_cumulative = cumsum(annual_vaccinated)
```

**Problems:**
1. V always increases (even with vaccine hesitancy)
2. Doesn't model loss of immunity
3. Can't simulate coverage drops
4. Misses herd immunity thresholds

### Proposed Solutions

**Add Coverage-Based SIRDV:**
```python
model = SIRDVCoverage(
    container,
    coverage_target=0.95,      # Target coverage
    coverage_actual_col='mcv1',  # Actual data
    waning_rate=0.01,          # Immunity waning
    herd_threshold=0.95        # Measles herd immunity
)
```

**Or Enhance Current SIRDV:**
```python
# Allow decreasing V (waning immunity)
# Add S_waning: V -> S pathway
# Model coverage gaps explicitly
```

---

## Problem 5: Forecasting Goals

### What dynasir forecasts (COVID):
1. Future cumulative cases
2. Hospital capacity needs
3. Next wave timing
4. Intervention impact

### What we need for measles:
1. **Outbreak probability**: Chance of outbreak next year
2. **Outbreak size distribution**: If outbreak occurs, how big?
3. **Coverage gaps impact**: What if vaccination drops to 90%?
4. **Importation risk**: Effect of international travel
5. **Herd immunity threshold**: When is population protected?

### Proposed Solutions

**Add Probabilistic Forecasting:**
```python
forecast_result = model.forecast_probabilistic(
    periods=10,
    n_simulations=10000,
    output_metrics=[
        'outbreak_probability',  # P(cases > threshold)
        'outbreak_size_quantiles',  # Distribution
        'time_to_elimination'  # When R0 < 1 sustained
    ]
)
```

**Add Scenario Analysis:**
```python
scenarios = model.forecast_scenarios([
    {'coverage': 0.95, 'importation': 0.1},  # Current
    {'coverage': 0.90, 'importation': 0.1},  # Vaccine hesitancy
    {'coverage': 0.95, 'importation': 0.5},  # More travel
])
```

---

## Problem 6: Performance Metrics

### Current Metrics (COVID)
- MAE, MSE, RMSE on cumulative cases
- SMAPE on daily incidence
- Good for continuous epidemics

### Issues for Measles
- Many zero-case years (or near-zero)
- Outbreaks are rare events
- Metrics don't capture outbreak prediction

### Example Problem
```
Actual:  [50, 60, 55, 650, 70, 55]  # Year 4 is outbreak
Forecast: [55, 55, 55, 55, 55, 55]  # Missed outbreak
RMSE: Good! (only one year wrong)
But: FAILED to predict outbreak (main goal!)
```

### Proposed Metrics

**Add Outbreak-Specific Metrics:**
```python
metrics = evaluate_forecast(
    predictions, actual,
    outbreak_threshold=200,  # Define "outbreak"
    metrics=[
        'outbreak_detection_rate',  # Sensitivity
        'false_alarm_rate',         # Specificity
        'outbreak_timing_error',    # Days early/late
        'outbreak_size_error'       # Magnitude error
    ]
)
```

---

## Implementation Recommendations

### Phase 1: Quick Wins (Backward Compatible)

1. **Add `incidence_mode` flag**
   - Detect if input data is incident vs cumulative
   - Warn users when using annual data

2. **Add temporal aggregation**
   - `forecast(..., aggregate='annual')`
   - Return yearly forecasts from daily model

3. **Enhance documentation**
   - Clear examples of when NOT to use dynasir
   - Guidance on data frequency requirements

### Phase 2: Core Extensions

1. **Multi-frequency support**
   - Native annual, monthly, weekly modeling
   - No artificial daily interpolation

2. **Incidence-first modeling**
   - Forecast incident cases directly
   - Optional cumulative calculation

3. **Importation modeling**
   - Add external force of infection
   - Model eliminated diseases

### Phase 3: Advanced Features

1. **Outbreak detection module**
   - Classify outbreak vs baseline
   - Probabilistic outbreak forecasts

2. **Coverage-based SIRDV**
   - Model vaccination coverage
   - Herd immunity dynamics

3. **Scenario comparison**
   - Multi-scenario forecasts
   - Intervention impact

---

## Example Use Cases After Improvements

### Use Case 1: Measles Outbreak Forecasting
```python
from dynasir import DataContainer, IncidenceModel

# Load annual incident cases (not cumulative!)
data = pd.DataFrame({
    'I': annual_incident_cases,  # New cases per year
    'N': population,
    'coverage': vaccination_coverage  # %
})

container = DataContainer(
    data,
    mode='incidence',
    frequency='annual'
)

model = IncidenceModel(
    container,
    start='1980',
    stop='2015',
    model_type='SIRDV',
    importation_rate=5,  # ~5 imported cases/year
    coverage_based=True
)

model.create_model()
model.fit_model()

# Forecast 10 years
forecast = model.forecast(
    periods=10,
    scenarios=[
        {'coverage': 0.95},  # Maintain coverage
        {'coverage': 0.90},  # Vaccine hesitancy
    ]
)

# Outbreak probability
prob = forecast.outbreak_probability(threshold=200)
print(f"Outbreak risk (95% coverage): {prob[0]:.1%}")
print(f"Outbreak risk (90% coverage): {prob[1]:.1%}")
```

### Use Case 2: Influenza Surveillance (Weekly Data)
```python
data = pd.DataFrame({
    'I': weekly_flu_cases,
    'N': population
})

container = DataContainer(
    data,
    mode='incidence',
    frequency='weekly'
)

model = IncidenceModel(
    container,
    seasonal=True,  # Model seasonality
    period=52       # Weekly in year
)

forecast = model.forecast(
    periods=52,  # 1 year ahead
    aggregate='monthly'  # Report by month
)
```

---

## Testing Data Sources

To validate improvements, test with:

1. **Measles (Eliminated)**
   - USA 1980-2020 (this dataset)
   - Europe post-elimination
   - Expect: Low baseline + rare outbreaks

2. **Pertussis (Cyclical Endemic)**
   - USA 1950-present
   - Clear 3-5 year cycles
   - Expect: Oscillating incidence

3. **Influenza (Seasonal)**
   - Weekly ILI surveillance
   - Strong seasonality
   - Expect: Annual winter peaks

4. **Dengue (Imported + Local)**
   - Florida or Texas
   - Mix of imported and local
   - Expect: Travel-related baseline + local amplification

---

## API Design Considerations

### Maintain Backward Compatibility
- Current COVID workflow unchanged
- New features opt-in via parameters
- Clear migration guide

### Explicit vs Implicit
```python
# GOOD: Explicit frequency
DataContainer(data, frequency='annual')

# BAD: Guess from date index
# (Users may have daily dates with annual data)
```

### Clear Defaults
```python
# For cumulative COVID data
mode='cumulative'  # Current default

# For incident surveillance data
mode='incidence'   # Must be explicit
```

---

## Validation Strategy

Before release:

1. **Reproduce COVID results**
   - Ensure backward compatibility
   - Same forecasts as v0.7.0

2. **Test on measles**
   - Compare to classical SEIR models
   - Validate outbreak predictions
   - Check physical plausibility

3. **Benchmark performance**
   - Compare to: statsmodels ARIMA, Prophet, EpiEstim
   - On: measles, flu, pertussis data

4. **User testing**
   - Public health practitioners
   - Epidemiologists familiar with surveillance data

---

## Documentation Needs

1. **When to use dynasir**
   - COVID-like: Ongoing epidemic, daily data, cumulative reporting
   - Measles-like: Eliminated disease, annual surveillance, incident cases
   - Flu-like: Seasonal endemic, weekly data, cyclical patterns

2. **When NOT to use**
   - Very sparse data (< 20 time points)
   - Highly stochastic small outbreaks
   - Non-infectious diseases

3. **Data preparation guide**
   - How to structure incident vs cumulative
   - Handling vaccination coverage data
   - Dealing with missing years

---

## Summary of Key Issues Found

| Issue | Current Behavior | Impact on Measles | Priority |
|-------|------------------|-------------------|----------|
| Cumulative assumption | Requires monotonic C | Meaningless forecasts | HIGH |
| Daily frequency | Reindex to daily | Artificial patterns | HIGH |
| Eliminated diseases | Assumes R0 near 1 | Forecasts to zero | MEDIUM |
| Vaccination model | Cumulative V | Can't model coverage gaps | MEDIUM |
| Forecast metrics | MAE/RMSE on C | Misses outbreak events | LOW |
| Annual data | No native support | Data distortion | HIGH |

---

## Conclusion

DynaSIR is a powerful tool but needs extension for surveillance data. The core issues are:

1. **Cumulative vs incidence** paradigm
2. **Time frequency** handling
3. **Eliminated disease** dynamics

With these enhancements, dynasir could become the go-to tool for:
- Eliminated disease surveillance (measles, polio)
- Endemic disease forecasting (flu, pertussis)
- Vaccine impact modeling
- Outbreak early warning systems

The current v0.7.0 SIRDV implementation is excellent for COVID but needs adaptation for annual surveillance contexts.
