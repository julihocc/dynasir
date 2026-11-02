# v0.10.0 Roadmap - Next Steps After v0.9.0 Release

**Date Created**: December 13, 2025
**Current Version**: 0.9.0 (released to PyPI)
**Target Version**: 0.10.0 or 0.9.1 (TBD)

## Current Situation Analysis

### What Was Released in v0.9.0 (December 13, 2025)
- ✅ Native multi-frequency support (Daily, Business Day, Weekly, Monthly, Annual)
- ✅ Incidence mode for eliminated diseases
- ✅ Frequency-aware VAR defaults
- ✅ FrequencyHandler architecture (5 concrete implementations)
- ✅ Seasonal pattern detection
- ✅ 394 tests passing (+52 new tests)
- ✅ Complete documentation reorganization
- ✅ 100% backward compatible

**PyPI**: https://pypi.org/project/dynasir/0.9.0/
**GitHub Release**: https://github.com/julihocc/dynasir/releases/tag/v0.9.0

### What Was Added AFTER v0.9.0 Release (PR #123)
- ✅ **Importation Modeling** (importation_rate parameter)
- ✅ **Scenario Analysis** (Model.create_scenario(), compare_scenarios())
- ✅ **USA Measles Validation** (validation notebook + data fetching)
- ✅ **Examples**: fetch_measles_data.py, validation notebooks

**Status**: Merged to main but NOT released to PyPI

### Open Issues Requiring Attention
- #127-137: Notebook testing and verification (Phase 1-4)
- #124-126: Outbreak detection and monitoring
- #108-112: Phase 3 Advanced Features (Epic)
- #97: Multi-backend time series refactoring

## Decision Point: v0.9.1 vs v0.10.0

### Option 1: Release v0.9.1 (Patch Release)
**Include:**
- Importation modeling
- Scenario analysis
- USA measles validation
- Bug fixes (if any)

**Rationale:**
- These are incremental additions to existing features
- No breaking changes
- Builds on measles integration from v0.9.0
- Quick release to get new features to users

**Timeline:** 1-2 days
1. Update version to 0.9.1
2. Update CHANGELOG.md
3. Run full test suite
4. Build and publish to PyPI
5. Create GitHub release

### Option 2: Work Toward v0.10.0 (Minor Release)
**Include:**
- Everything from v0.9.1
- Outbreak detection (#124-126)
- Enhanced visualization
- Performance optimizations
- Additional features from roadmap

**Rationale:**
- Significant new capabilities warrant minor version bump
- More time for comprehensive testing
- Opportunity for larger improvements

**Timeline:** 2-4 weeks

## Recommended Approach: v0.9.1 First

**Immediate Action**: Release v0.9.1 to get importation modeling and scenario analysis to users

**Plan**:
1. **v0.9.1** (This week)
   - Release current main branch
   - Include importation modeling + scenario analysis
   - Verify notebooks work
   - Quick turnaround

2. **v0.10.0** (Next month)
   - Larger feature set
   - Outbreak detection
   - Performance improvements
   - See detailed roadmap below

## v0.9.1 Release Checklist

### Pre-Release Tasks
- [ ] Update version in pyproject.toml (0.9.0 → 0.9.1)
- [ ] Update version in src/dynasir/__init__.py
- [ ] Update test expectations for version
- [ ] Run full test suite (pytest)
- [ ] Verify all notebooks execute (#133-135)
- [ ] Update CHANGELOG.md with v0.9.1 entry
- [ ] Create release notes

### Release Tasks
- [ ] Commit version updates
- [ ] Tag release: `git tag -a v0.9.1 -m "..."`
- [ ] Push tags: `git push origin v0.9.1`
- [ ] Build package: `python -m build`
- [ ] Upload to PyPI: `twine upload dist/dynasir-0.9.1*`
- [ ] Create GitHub release with notes

### Post-Release Tasks
- [ ] Close related issues (#106, #107, #111, #116, #120-122)
- [ ] Update project board
- [ ] Announce release
- [ ] Begin v0.10.0 planning

## v0.10.0 Roadmap (Detailed)

### Phase 1: Notebook Verification & Testing
**Issues**: #127-137
**Goal**: Ensure all examples and notebooks are working and up-to-date

**Tasks**:
1. Verify AnnualFrequencyHandler (#127)
2. Verify complete measles workflow (#128)
3. Create verification documentation (#129)
4. Create new native annual notebook (#130)
5. Remove outdated version references (#131)
6. Audit all notebooks (#132)
7. Execute full test suite (#133-135)
8. Decide on release strategy (#136-137)

**Timeline**: 1 week
**Priority**: High (blocking v0.9.1)

### Phase 2: Outbreak Detection & Monitoring
**Issues**: #124-126
**Goal**: Add real-time outbreak detection capabilities

**Features**:
1. **Outbreak Detection Module** (#124)
   - Threshold-based detection
   - Statistical anomaly detection
   - Trend analysis
   - Configurable sensitivity

2. **Model Integration** (#125)
   - Integrate detection into Model class
   - Automatic monitoring during forecasting
   - Alert system for outbreaks

3. **Visualization** (#126)
   - Outbreak alert visualizations
   - Time series with outbreak markers
   - Risk level indicators

**Timeline**: 1-2 weeks
**Priority**: Medium

### Phase 3: Advanced Features (Epic #108)
**Issues**: #108-112
**Goal**: Probabilistic forecasting and advanced modeling

**Features**:
1. **Outbreak-Specific Metrics** (#109)
   - Peak detection
   - Outbreak duration
   - Attack rate calculations
   - R0 estimation improvements

2. **Probabilistic Forecasting** (#110)
   - Already have Monte Carlo simulations
   - Enhance with prediction intervals
   - Uncertainty quantification
   - Ensemble methods

3. **Waning Immunity** (#112)
   - Coverage-based SIRDV extension
   - Time-dependent vaccination effectiveness
   - Booster dose modeling

**Timeline**: 2-3 weeks
**Priority**: Medium-High

### Phase 4: Performance & Optimization
**Goal**: Speed improvements for production use

**Tasks**:
1. Profile current implementation
2. Optimize frequency handler lookups
3. Cache seasonal pattern detection
4. Parallel VAR fitting for multiple regions
5. Benchmarking suite

**Timeline**: 1 week
**Priority**: Medium

### Phase 5: Multi-Backend Support (#97)
**Goal**: Pluggable forecasting backends

**Features**:
1. Backend registry pattern
2. ARIMA implementation
3. Prophet implementation (optional dependency)
4. LSTM implementation (optional dependency)
5. Automatic backend selection based on data characteristics

**Timeline**: 2-3 weeks
**Priority**: Low (can be v0.11.0)

## v0.10.0 Features Summary

Based on v0.9.0 release notes, here's what was promised:

### 1. Native Frequency Support ✅
**Status**: ALREADY IMPLEMENTED in v0.9.0!
- FrequencyHandler architecture ✅
- Annual/Monthly/Weekly/Daily/Business Day ✅
- No more daily reindexing ✅

### 2. Specialized Annual Methods
**Status**: Partially done, needs enhancement
**Tasks**:
- [ ] Annual-specific VAR configuration
- [ ] Small sample size handling
- [ ] Bootstrap methods for uncertainty
- [ ] Annual-aware cross-validation

### 3. Enhanced Visualization
**Status**: Needs implementation
**Tasks**:
- [ ] Incidence-specific plots
- [ ] Outbreak detection visualizations
- [ ] Interactive dashboards (optional plotly)
- [ ] Comparison plots for scenarios

### 4. Performance Optimizations
**Status**: Needs implementation
**Tasks**:
- [ ] Profiling and benchmarking
- [ ] Caching improvements
- [ ] Parallel processing enhancements
- [ ] Memory optimization

### 5. Additional Backends (LSTM)
**Status**: Needs design and implementation
**Tasks**:
- [ ] Backend abstraction layer
- [ ] LSTM implementation
- [ ] ARIMA implementation
- [ ] Prophet integration

## Timeline Estimation

### v0.9.1 Release
**Target**: December 16-18, 2025 (this week)
**Effort**: 1-2 days

### v0.10.0 Release
**Target**: January 15-31, 2026
**Effort**: 4-6 weeks of development

**Breakdown**:
- Week 1: Notebook verification (#127-137)
- Week 2: Outbreak detection (#124-126)
- Week 3-4: Advanced features (#108-112)
- Week 5: Performance optimization
- Week 6: Testing, documentation, release

## Success Metrics for v0.10.0

### Code Quality
- [ ] Test coverage ≥ 85%
- [ ] All pre-commit hooks passing
- [ ] Type hints complete
- [ ] Documentation comprehensive

### Performance
- [ ] Benchmark suite established
- [ ] No performance regression vs v0.9.0
- [ ] 20%+ improvement in annual data processing

### Features
- [ ] Outbreak detection functional
- [ ] Enhanced visualizations available
- [ ] At least 2 additional backends implemented
- [ ] Waning immunity model working

### User Experience
- [ ] All notebooks execute without errors
- [ ] Clear migration guide from v0.9.x
- [ ] Examples cover all major features
- [ ] API documentation complete

## Next Immediate Actions

### This Week (v0.9.1)
1. **Test Suite** - Run pytest and verify 394+ tests passing
2. **Notebook Verification** - Manually test critical notebooks
3. **Version Update** - Bump to 0.9.1
4. **CHANGELOG** - Document importation modeling and scenario analysis
5. **Release** - Tag, build, publish to PyPI

### Next Week (v0.10.0 Planning)
1. **Issue Triage** - Organize #124-137 into milestones
2. **Architecture Design** - Plan outbreak detection module
3. **Prototyping** - Start outbreak detection implementation
4. **Benchmarking** - Establish performance baselines

## References

- **v0.9.0 Release Notes**: [docs/releases/RELEASE_NOTES_v0.9.0.md](../releases/RELEASE_NOTES_v0.9.0.md)
- **PR #119** (v0.9.0): Native Multi-Frequency and Incidence Mode
- **PR #123**: Importation Modeling and Scenario Analysis
- **Epic #108**: Phase 3 Advanced Features
- **Issue #97**: Multi-Backend Time Series Refactoring

## Questions to Answer

1. **v0.9.1 vs v0.10.0?** → Recommend v0.9.1 first (quick release)
2. **Include outbreak detection in v0.9.1?** → No, save for v0.10.0
3. **Multi-backend in v0.10.0?** → Optional, can defer to v0.11.0
4. **Waning immunity in v0.10.0?** → Yes, if time permits
5. **Target timeline for v0.10.0?** → January 2026

---

**Next Steps**: Decide on v0.9.1 release, then begin v0.10.0 development

**Last Updated**: December 13, 2025
**Status**: Planning Phase
