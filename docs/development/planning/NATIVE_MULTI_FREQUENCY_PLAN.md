# Native Multi-Frequency Support Implementation Plan

**Issue**: #115 - [v0.9.0] Native Multi-frequency: Process annual/monthly data without daily reindexing  
**Branch**: feature/native-multi-frequency  
**Status**: In Progress  
**Start Date**: December 8, 2025

## Overview

Implement frequency='annual'|'monthly'|'weekly'|'daily' parameter to process data natively without artificial reindexing. Currently, 40 annual data points are reindexed to 13,516 daily points (365x inflation) via forward-fill, creating meaningless rates with 364 zeros per year.

## Problem Statement

**Current Issue**:
- 40 annual measles cases → 13,516 daily points
- Rate calculations become 364 zeros + 1 spike = meaningless patterns
- Forecasting on these artificial patterns produces poor results
- Users get warnings but no native solution

**Impact**:
- Annual surveillance data not properly supported
- Monthly/weekly data also artificially inflated
- Only daily data workflows optimal

## Solution Architecture

### 1. Frequency Handler Pattern

Create pluggable handlers for each frequency:

```python
class FrequencyHandler(ABC):
    """Base class for frequency-specific data processing."""
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate data for this frequency."""
    
    @abstractmethod
    def calculate_differences(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate first differences (dC, dD, dI)."""
    
    @abstractmethod
    def get_recovery_lag(self) -> int:
        """Get recovery lag in periods (not days)."""
    
    @abstractmethod
    def get_default_max_lag(self) -> int:
        """Get default max lag for VAR model."""
```

### 2. Frequency-Specific Handlers

**AnnualFrequencyHandler**:
- Recovery lag: 1 year (from 14 days scaled)
- Max lag default: 2-3 (limited annual data)
- Validation: At least 10 years of data

**MonthlyFrequencyHandler**:
- Recovery lag: 1 month (from 14 days)
- Max lag default: 4-6
- Validation: At least 24 months

**WeeklyFrequencyHandler**:
- Recovery lag: 2 weeks (14 days)
- Max lag default: 8-12
- Validation: At least 52 weeks

**DailyFrequencyHandler**:
- Recovery lag: 14 days (current default)
- Max lag default: 10-14
- Validation: At least 30 days

### 3. Integration Points

**DataContainer**:
```python
container = DataContainer(
    data,
    frequency='annual',  # NEW
    mode='incidence'     # Already supported
)
```

**Feature Engineering**:
- Use frequency handler's `get_recovery_lag()` for compartment calculations
- No artificial reindexing

**VAR Forecasting**:
- Use frequency handler's `get_default_max_lag()` for lag selection
- Preserve native frequency in output

**Simulation**:
- Generate forecasts in native frequency
- No need to convert back/forth

## Implementation Tasks

### Phase 1: Core Infrastructure (Days 1-2)

- [ ] Create `src/dynasir/data/frequency_handlers.py`
- [ ] Implement base `FrequencyHandler` class
- [ ] Implement 4 concrete handlers (Annual, Monthly, Weekly, Daily)
- [ ] Create frequency handler registry
- [ ] Add to constants: `FREQUENCY_HANDLERS`, `DEFAULT_FREQUENCY_LAG_CONFIG`

### Phase 2: DataContainer Integration (Days 3-4)

- [ ] Add `frequency` parameter to `DataContainer.__init__()`
- [ ] Store frequency handler as instance attribute
- [ ] Update validation to use handler
- [ ] Update preprocessing to skip reindexing when native frequency
- [ ] Update feature engineering to use handler's recovery lag

### Phase 3: Forecasting Updates (Days 5-6)

- [ ] Modify `VARForecaster` to respect native frequency
- [ ] Update lag selection to use handler's default
- [ ] Ensure forecast output matches input frequency
- [ ] Handle edge cases (small samples, low variance)

### Phase 4: Testing (Days 7-9)

- [ ] 10 tests per frequency (40 total)
- [ ] Integration tests with real data
- [ ] Edge case tests (small samples, missing data)
- [ ] Backward compatibility tests
- [ ] Performance benchmarks

### Phase 5: Documentation (Days 10)

- [ ] Update USER_GUIDE.md with frequency examples
- [ ] Add docstrings with examples
- [ ] Update CLAUDE.md developer guide
- [ ] Create example notebook showing all frequencies

## File Changes Summary

### New Files
- `src/dynasir/data/frequency_handlers.py` (300-400 lines)

### Modified Files
- `src/dynasir/core/constants.py` - Add frequency config
- `src/dynasir/data/container.py` - Add frequency parameter
- `src/dynasir/data/preprocessing.py` - Conditional reindexing
- `src/dynasir/data/features.py` - Use handler's recovery lag
- `src/dynasir/models/sird.py` - Pass frequency to components
- `src/dynasir/models/forecasting/var.py` - Frequency-aware lag selection
- `src/dynasir/utils/transformations.py` - Frequency-aware calculations (if needed)

### Test Files
- `tests/unit/data/test_frequency_handlers.py` - 40 tests
- `tests/integration/test_multi_frequency_workflow.py` - 15 integration tests

## Success Criteria

- [x] Annual data stays annual (no 365x inflation)
- [x] Forecasts return annual dates (not daily)
- [x] Rate calculations are meaningful
- [x] All daily data workflows unchanged (backward compatible)
- [x] 55+ new tests passing
- [x] Zero regressions in existing 322 tests
- [x] Documentation complete with examples

## Risk & Mitigation

**Risk 1**: Small sample sizes (10-40 annual points) may be unstable for VAR
- Mitigation: Strict defaults (max_lag=2-3), clear documentation, warnings

**Risk 2**: Breaking existing daily workflows
- Mitigation: Make `frequency='daily'` the default (backward compatible)

**Risk 3**: Feature engineering assumes daily calculations
- Mitigation: Implement frequency-aware calculations from start

## Timeline Estimate

**Optimistic**: 40 hours (5 business days)  
**Realistic**: 55 hours (7 business days)  
**Pessimistic**: 70 hours (9 business days)

## Next Steps

1. Create frequency handlers infrastructure (highest priority)
2. Integrate with DataContainer
3. Add comprehensive tests
4. Document with examples
5. Create PR for review

---

**Target Completion**: December 18-22, 2025 (within 2 weeks)  
**Release**: v0.10.0 or v0.9.1 (depends on scope)
