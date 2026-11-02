# Option D Implementation Plan: Hybrid Approach for Annual Incidence Limitation

**Date**: December 19, 2025
**Decision**: Option D - Hybrid approach for handling annual incidence data limitation

## Overview

Based on the verification findings from Tasks 1-2, we've identified that annual incidence data produces constant rates that prevent VAR model fitting. Rather than blocking progress, we're implementing a hybrid approach that:

1. **Documents the limitation clearly** - Users understand the constraint
2. **Creates monthly examples for now** - Provides immediate working examples
3. **Plans non-VAR backend for future** - Keeps enhancement options open

## Immediate Actions (Current Sprint)

### 1. Documentation Updates

**File**: `docs/user-guide/limitations.md` (create new)
- Document the annual + incidence + VAR limitation
- Explain the mathematical root cause
- Provide clear guidance on alternatives
- Include code examples showing what works

**File**: `src/dynasir/data/frequency_handlers.py`
- Add docstring warning to AnnualFrequencyHandler
- Note that incidence mode may produce constant rates
- Recommend monthly/weekly data for eliminated diseases

**File**: `CLAUDE.md` (update)
- Add section on known limitations
- Update best practices for frequency selection
- Guide users toward appropriate data frequencies

### 2. Create Working Monthly Measles Example

**File**: `examples/monthly_measles_forecasting.ipynb` (Task 4 revised)
- Use monthly measles data (ME frequency)
- Demonstrate incidence mode with realistic sporadic patterns
- Show importation modeling (v0.9.1 feature)
- Include scenario analysis
- Verify all components work end-to-end

**Data Source**: WHO measles surveillance data (monthly aggregates)
- More realistic than annual for disease surveillance
- Sufficient temporal resolution for VAR modeling
- Recovery lag = 0.5 months (reasonable approximation)

### 3. Update Existing Notebooks (Tasks 5-6)

**Review and update**:
- Remove any references to annual measles forecasting
- Update frequency recommendations
- Ensure all examples use appropriate frequencies
- Add notes about limitation where relevant

### 4. Testing and Verification (Tasks 7-8)

**Run full test suite** (Task 7):
```bash
pytest tests/ -v --cov=src/dynasir
```

**Manual verification** (Task 8):
- Run monthly measles notebook end-to-end
- Verify importation modeling works
- Test scenario analysis
- Check visualization quality

**Test download scripts** (Task 9):
- Verify data fetching works
- Check monthly aggregation logic
- Validate data format

## Future Enhancements (v0.10.0+)

### Non-VAR Forecasting Backend

**Goal**: Enable annual incidence data forecasting without VAR

**Approach 1: Direct Case Count Forecasting**
- Forecast incident cases (I) directly using ARIMA/Prophet
- Skip rate modeling entirely
- Use forecasted I values in simulation
- Simpler, but less epidemiologically grounded

**Approach 2: Importation-Only Simulation**
- Accept that rates are constant for annual data
- Focus on importation modeling
- Use historical average rates
- Simulate with stochastic importation events

**Approach 3: Hybrid Time-Series Models**
- ARIMA for incident cases
- Prophet for seasonal patterns
- Ensemble approaches
- More sophisticated, better for complex patterns

### Architecture Changes Needed

1. **Forecasting Backend Abstraction**
   - Create `ForecastingBackend` interface
   - Implementations: `VARBackend`, `ARIMABackend`, `ProphetBackend`
   - Auto-select based on frequency + mode combination

2. **Graceful Fallback**
   - Detect constant rate scenario
   - Warn user
   - Automatically switch to appropriate backend
   - Or raise informative error with suggestions

3. **Configuration Options**
   ```python
   # Future API
   model.fit_model(
       backend="auto",  # or "var", "arima", "prophet"
       max_lag=None,    # auto-select based on backend
       **backend_kwargs
   )
   ```

## Implementation Timeline

### Current Sprint (This Week)
- [x] Task 1: Verify AnnualFrequencyHandler
- [x] Task 2: Verify measles workflow
- [x] Task 3: Create verification documentation
- [ ] Task 4: Create monthly measles notebook (revised scope)
- [ ] Task 5: Update notebook 07 references
- [ ] Task 6: Audit all notebooks
- [ ] Task 7: Execute test suite
- [ ] Task 8: Manual verification
- [ ] Task 9: Test download scripts

### Documentation Sprint (Next Week)
- [ ] Create `docs/user-guide/limitations.md`
- [ ] Update `CLAUDE.md` with limitation guidance
- [ ] Add docstring warnings to AnnualFrequencyHandler
- [ ] Update README with frequency selection guide

### Future (v0.10.0 Planning)
- [ ] Design forecasting backend interface
- [ ] Prototype ARIMA backend
- [ ] Test with annual incidence data
- [ ] Evaluate performance vs alternatives

## Success Criteria

**Immediate (This Sprint)**:
- ✅ Limitation is clearly documented
- ✅ Working monthly measles example exists
- ✅ All notebooks reviewed and updated
- ✅ Test suite passes
- ✅ Manual verification complete

**Future (v0.10.0)**:
- Annual incidence data can be forecasted
- Multiple backend options available
- Auto-detection works reliably
- Performance meets requirements

## Risk Mitigation

**Risk**: Users still try annual + incidence + VAR
- **Mitigation**: Clear error messages with actionable suggestions
- **Example**: "Annual incidence data produces constant rates. Try: (1) Use monthly/weekly data, (2) Use ARIMA backend [v0.10.0+], or (3) See docs/limitations.md"

**Risk**: Monthly data not available for all use cases
- **Mitigation**: Provide data aggregation utilities
- **Mitigation**: Support multiple data sources (WHO, CDC, etc.)

**Risk**: Non-VAR backends significantly different API
- **Mitigation**: Design unified interface from start
- **Mitigation**: Extensive testing for backward compatibility

## Questions for Future Discussion

1. Should we support quarterly (QE) frequency as middle ground?
2. What's minimum data requirements for ARIMA backend?
3. How to handle missing data in monthly time series?
4. Should we auto-aggregate annual to monthly if possible?

## References

- Task 1 Results: [VERIFICATION_RESULTS.md](VERIFICATION_RESULTS.md#task-1)
- Task 2 Results: [VERIFICATION_RESULTS.md](VERIFICATION_RESULTS.md#task-2)
- Root Cause Analysis: [VERIFICATION_RESULTS.md](VERIFICATION_RESULTS.md#root-cause-analysis)
- Original Plan: [NOTEBOOK_VERIFICATION_PLAN.md](planning/NOTEBOOK_VERIFICATION_PLAN.md)

---

**Status**: APPROVED
**Next Action**: Proceed with Task 4 - Create monthly measles example notebook
