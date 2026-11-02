# GitHub Issue Draft: Implement ARIMA Backend for Annual Incidence Data

**Copy this content to create a new GitHub issue**

---

## Title
Implement ARIMA Backend for Annual Incidence Data (v0.10.0)

## Labels
`enhancement`, `v0.10.0`, `forecasting`, `measles-integration`

## Milestone
v0.10.0

## Description

### Problem Statement

The library currently supports only VAR (Vector Autoregression) for forecasting epidemic rates. While VAR works excellently for COVID-19 data (daily cumulative), it **fails** for eliminated disease surveillance data (annual incidence) due to mathematical constraints.

**Current Limitation**:
- Annual frequency + incidence mode → constant rates (beta = 1.0)
- Constant rates → zero variance → singular covariance matrix
- VAR cannot fit: `LinAlgError: N-th leading minor not positive definite`

**Real-World Impact**:
- WHO/CDC publish measles/polio/rubella data **annually**
- Data format is **incident cases** (not cumulative)
- Users with only annual data are blocked from using the library
- Current workaround (use monthly data) is not always feasible

**Documentation**: See [known-limitations.md](https://github.com/julihocc/dynasir/blob/main/docs/user-guide/known-limitations.md)

### Proposed Solution

Implement **ARIMA (AutoRegressive Integrated Moving Average)** backend as an alternative to VAR for forecasting.

**Why ARIMA?**
- Forecasts incident cases (I) **directly** - no rate modeling needed
- Handles annual data naturally
- Appropriate for sporadic/seasonal patterns (measles outbreaks)
- Well-established time series method
- Available via statsmodels (already a dependency)

**Key Advantage**: ARIMA forecasts the compartment values directly, bypassing the rate estimation problem entirely.

### Implementation Plan

#### Phase 1: Backend Interface Design

Create abstract `ForecastingBackend` interface:

```python
# src/dynasir/models/forecasting/backend.py
from abc import ABC, abstractmethod

class ForecastingBackend(ABC):
    """Abstract base class for forecasting backends."""

    @abstractmethod
    def fit(self, data, **kwargs):
        """Fit the forecasting model."""
        pass

    @abstractmethod
    def forecast(self, steps, **kwargs):
        """Generate forecasts with confidence intervals."""
        pass

    @abstractmethod
    def supports_mode(self, mode: str) -> bool:
        """Check if backend supports a given mode."""
        pass
```

#### Phase 2: ARIMA Backend Implementation

```python
# src/dynasir/models/forecasting/arima_backend.py
from statsmodels.tsa.arima.model import ARIMA
from .backend import ForecastingBackend

class ARIMAForecastingBackend(ForecastingBackend):
    """
    ARIMA-based forecasting for incident cases.

    Forecasts compartment values (I, R, D) directly without
    rate modeling. Suitable for annual incidence data.
    """

    def fit(self, data, order=(1,1,1), **kwargs):
        """
        Fit ARIMA model on incident cases.

        Args:
            data: DataFrame with I (incident cases) column
            order: (p, d, q) ARIMA order
        """
        self.model = ARIMA(data['I'], order=order)
        self.fitted = self.model.fit()

    def forecast(self, steps, alpha=0.05):
        """
        Forecast future incident cases.

        Returns:
            DataFrame with lower, point, upper forecast
        """
        forecast = self.fitted.get_forecast(steps=steps)
        forecast_df = forecast.summary_frame(alpha=alpha)
        # Map to dynasir format (lower, point, upper)
        return forecast_df

    def supports_mode(self, mode: str) -> bool:
        """ARIMA works best with incidence mode."""
        return mode == 'incidence'
```

#### Phase 3: Integration with Model Class

Update `Model.fit_model()` to support backend selection:

```python
# src/dynasir/models/sird.py
def fit_model(self, backend='var', **kwargs):
    """
    Fit forecasting model.

    Args:
        backend: 'var' (default) or 'arima'
        **kwargs: Backend-specific parameters
            VAR: max_lag, ic
            ARIMA: order (p,d,q)
    """
    if backend == 'var':
        # Existing VAR logic
        self.var_forecasting.fit_logit_ratios_model(**kwargs)
    elif backend == 'arima':
        # New ARIMA logic
        from .forecasting.arima_backend import ARIMAForecastingBackend
        self.forecaster = ARIMAForecastingBackend()
        self.forecaster.fit(self.data, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

#### Phase 4: Documentation & Examples

1. Update user guide with ARIMA usage
2. Create example notebook: `examples/notebooks/08_arima_annual_measles.ipynb`
3. Update CLAUDE.md with backend selection guidance
4. Add to README features list

### API Design

**User Interface** (simple and intuitive):

```python
# Current (VAR - works for COVID)
container = DataContainer(covid_data, mode='cumulative', frequency='D')
model = Model(container)
model.fit_model(max_lag=14)  # VAR backend (default)

# New (ARIMA - works for annual measles)
container = DataContainer(measles_data, mode='incidence', frequency='YE')
model = Model(container)
model.fit_model(backend='arima', order=(1,1,1))  # ARIMA backend
```

**Backward Compatibility**: Fully maintained
- Default backend remains 'var'
- Existing code works unchanged
- New parameter is optional

### Success Criteria

- [ ] `ARIMAForecastingBackend` class implemented
- [ ] Backend selection works in `Model.fit_model()`
- [ ] Annual incidence data forecasts successfully
- [ ] Confidence intervals generated correctly
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Example notebook created
- [ ] Backward compatibility verified

### Testing Strategy

```python
# tests/unit/models/test_arima_backend.py
def test_arima_backend_annual_incidence():
    """Test ARIMA backend with annual incidence data."""
    # Annual measles data (the problematic case)
    data = pd.DataFrame({
        'I': [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45],
        'D': [0] * 12,
        'N': [110_000_000] * 12
    }, index=pd.date_range('2010', periods=12, freq='YE'))

    container = DataContainer(data, mode='incidence', frequency='YE')
    model = Model(container, start='2010', stop='2019')

    # This should work (currently fails with VAR)
    model.fit_model(backend='arima', order=(1,1,1))
    model.forecast(steps=3)

    assert model.forecast_results is not None
    assert len(model.forecast_results) == 3
```

### Future Enhancements (v0.10.1+)

**Phase 2**: Prophet backend for seasonal patterns
**Phase 3**: Auto-selection (detect constant rates → use ARIMA)

See [OPTION_D_IMPLEMENTATION.md](https://github.com/julihocc/dynasir/blob/main/docs/development/OPTION_D_IMPLEMENTATION.md) for complete roadmap.

### Related Issues & Documentation

- **Issue #127**: AnnualFrequencyHandler Verification
- **Issue #128**: Complete Measles Workflow (identified limitation)
- **Task 2**: [Verification Results](https://github.com/julihocc/dynasir/blob/main/docs/development/VERIFICATION_RESULTS.md#task-2-complete-measles-workflow-128)
- **Option D Plan**: [OPTION_D_IMPLEMENTATION.md](https://github.com/julihocc/dynasir/blob/main/docs/development/OPTION_D_IMPLEMENTATION.md)
- **Limitation Docs**: [known-limitations.md](https://github.com/julihocc/dynasir/blob/main/docs/user-guide/known-limitations.md)
- **Branch**: `feature/document-annual-incidence-limitation`

### Implementation Notes

**Dependencies**: No new dependencies needed
- statsmodels already required for VAR
- ARIMA available in statsmodels.tsa.arima

**Complexity**: Medium
- Clear interface design
- Existing VAR backend provides template
- Well-defined scope

**Timeline**: 2-3 weeks
- Week 1: Backend interface + ARIMA implementation
- Week 2: Integration + testing
- Week 3: Documentation + examples

### Questions for Discussion

1. Should we support automatic backend selection based on data characteristics?
2. Should ARIMA forecast all compartments (I, R, D) or just I?
3. How should we handle simulation scenarios with ARIMA forecasts?
4. Should we add model selection criteria (AIC/BIC) for ARIMA order?

---

**Priority**: High - Blocks real-world use cases (eliminated disease surveillance)
**Difficulty**: Medium - Clear scope, existing architecture to follow
**Impact**: High - Enables annual incidence data forecasting

cc: @julihocc
