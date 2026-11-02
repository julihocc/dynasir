# GitHub Project Organization Plan - DynaSIR Library

**Date**: December 2025  
**Repository**: julihocc/dynasir  
**Total Issues**: 131 (15 open, 116 closed)

## Executive Summary

This document provides a comprehensive plan to organize all dynasir GitHub issues into a structured project board with clear swim lanes, priorities, and dependencies.

---

## Proposed Project Structure

### Project Name: **DynaSIR Development Roadmap**

### Description
Centralized tracking for dynasir library development across releases v0.10.0 through v1.0.0, including feature development, bug fixes, documentation, and performance optimization.

---

## Swim Lanes (Columns)

### 1. **Current Sprint (v0.10.0)** 🔥
**Purpose**: Active work on reporting enhancements branch  
**Issues**: 3-5 issues currently being developed

**Current Contents**:
- (No new issues - v0.10.0 feature work complete, in testing phase)

---

### 2. **Next Release (v0.11.0)** 📦
**Purpose**: Planned work for immediate next release (Q1 2026)  
**Issues**: 8-12 issues prioritized for v0.11.0

**Proposed Contents**:
- **NEW Issue #144**: v0.11.0 PyPI Release Preparation (HIGH PRIORITY)
- **NEW Issue #146**: Backward Compatibility Test Suite (HIGH PRIORITY - blocker)
- #93: Backward compatibility tests (from epic #97)
- #94: Update CLAUDE.md for multi-backend (MEDIUM PRIORITY)
- #96: Update pyproject.toml dependencies (MEDIUM PRIORITY)
- #109: Outbreak-specific metrics (MEDIUM PRIORITY - from epic #108)
- #63-73: November 2025 priority issues (review needed)

**Success Criteria**:
- All HIGH priority issues resolved
- PyPI release successful
- Backward compatibility validated
- Documentation complete

---

### 3. **Backlog - High Priority** ⚡
**Purpose**: Important features for v1.0.0 or next minor releases  
**Issues**: 10-15 high-value features

**Proposed Contents**:
- #110: Probabilistic forecasting (from epic #108)
- #112: Coverage-based SIRDV with waning immunity (from epic #108)
- **NEW Issue #145**: Performance Benchmarking & Profiling Suite
- #124-126: Outbreak monitoring tools (Low-Medium priority)
- Any stale issues from #63-73 that are still relevant

---

### 4. **Backlog - Research & Exploration** 🔬
**Purpose**: Experimental features, academic integrations, future directions  
**Issues**: 5-10 exploratory items

**Proposed Contents**:
- Advanced LSTM backend improvements (from epic #97)
- Spatial epidemic modeling (future consideration)
- Real-time data integration APIs
- Bayesian parameter estimation
- Sensitivity analysis tools

---

### 5. **Documentation** 📚
**Purpose**: Ongoing documentation improvements  
**Issues**: Documentation gaps, user guides, examples

**Proposed Contents**:
- #94: Update CLAUDE.md for multi-backend
- User guide expansions for v0.10.0 features
- API reference documentation
- Tutorial notebook improvements
- Performance guide (from new issue #145)

---

### 6. **Completed (Archive)** ✅
**Purpose**: Recently completed work for reference  
**Issues**: Last 20-30 closed issues (auto-archive older ones)

**Proposed Contents**:
- #111, #120-122: Scenario analysis (CLOSED v0.9.1)
- #82-92: Multi-backend phases 1-3 (CLOSED v0.8.0)
- #113-119: SIRDV implementation (CLOSED v0.6.1)
- Phase 1 & 2 measles integration issues (CLOSED)

**Note**: GitHub can auto-archive issues closed >90 days ago

---

## Issue Triage Results

### Issues to CLOSE (Completed Work Verified)

Based on codebase verification, these issues can be confidently closed:

1. **#111**: Scenario Analysis Framework
   - **Status**: CLOSED (if not already)
   - **Verification**: `Model.create_scenario()` implemented at [src/dynasir/models/sird.py](src/dynasir/models/sird.py#L684)
   - **Artifacts**: Method with full parameter modifier support

2. **#120**: Create `Model.create_scenario()` Method
   - **Status**: CLOSED (if not already)
   - **Verification**: Same as #111, implemented in v0.9.1
   - **Evidence**: Released in v0.9.1 release notes

3. **#121**: Create `compare_scenarios()` Visualization
   - **Status**: CLOSED (if not already)
   - **Verification**: Function implemented at [src/dynasir/analysis/visualization.py](src/dynasir/analysis/visualization.py#L116)
   - **Artifacts**: Full comparison plot utility with examples

4. **#122**: Scenario Analysis Example Notebook
   - **Status**: CLOSED (if not already)
   - **Verification**: Notebook exists at `examples/scenario_analysis_measles.ipynb`
   - **Evidence**: Part of validated 7-notebook suite

### Issues to UPDATE (Add Progress Notes)

1. **#108**: Epic - Phase 3 Advanced Features
   - **Action**: Updated with v0.12.0 progress report
   - **Note**: 25% complete (scenario analysis done, 3 features remaining)

2. **#97**: Epic - Multi-Backend Refactoring
   - **Action**: Updated with 95% completion status
   - **Note**: Phase 4 testing/docs nearly complete

### Issues to REVIEW (November 2025 Priority Block)

**Priority Issues #63-73** - Created November 21, 2025:

These need individual assessment:
- #63: API Consistency Review (check if API_AUDIT.md addresses this)
- #64: R0 Calculation Methods (verify implementation status)
- #65: Visualization Utilities Enhancement (check recent additions)
- #66: Test Coverage Improvement (currently 99.5%, may be resolved)
- #67: Documentation Completeness Audit (ongoing, not closeable)
- #68: Performance Optimization (now covered by new issue #145)
- #69: Error Handling Standardization (needs codebase review)
- #70: Configuration Management (pydantic-settings implemented, verify completeness)
- #71: Logging System Implementation (needs verification)
- #72: Type Hints Completeness (mypy passing, may be mostly done)
- #73: Dependency Management (pyproject.toml mature, verify)

**Recommendation**: Create todo list for #63-73 review in separate session

---

## Priority Matrix

### HIGH Priority (v0.11.0 - Must Have)
1. **NEW #144**: v0.11.0 PyPI Release Preparation
2. **NEW #146**: Backward Compatibility Test Suite
3. #93: Backward compatibility tests
4. Issues from #63-73 marked as blockers

### MEDIUM Priority (v0.11.0 - Should Have)
5. #94: Update CLAUDE.md
6. #96: Update pyproject.toml dependencies
7. #109: Outbreak metrics
8. **NEW #145**: Performance benchmarking

### LOW Priority (v1.0.0 or later - Nice to Have)
9. #110: Probabilistic forecasting
10. #112: Coverage-based SIRDV
11. #124-126: Outbreak monitoring tools
12. LSTM backend enhancements

---

## Dependency Graph

```
v0.11.0 Release (#144)
  ├─ DEPENDS ON: Backward Compatibility Tests (#146, #93)
  ├─ DEPENDS ON: Documentation Updates (#94)
  └─ DEPENDS ON: Dependency Review (#96)

Backward Compatibility (#146)
  └─ DEPENDS ON: Multi-backend epic complete (#97)

v1.0.0 Planning
  ├─ DEPENDS ON: v0.11.0 released (#144)
  ├─ Phase 3 Advanced Features (#108)
  │   ├─ Outbreak Metrics (#109) ← Can start independently
  │   ├─ Probabilistic Forecasting (#110)
  │   └─ Coverage-based SIRDV (#112)
  └─ Performance Baseline (#145) ← Informs optimization work
```

---

## Implementation Steps

### Step 1: Manual Issue Creation ✅ READY
Create 3 new issues from `PROPOSED_ISSUES_v0.11.0.md`:
- [ ] Issue #144: v0.11.0 PyPI Release Preparation
- [ ] Issue #145: Performance Benchmarking Suite
- [ ] Issue #146: Backward Compatibility Test Suite

### Step 2: Update Existing Issues ✅ COMPLETE
- [x] Update Epic #108 with progress
- [x] Update Epic #97 with completion status
- [ ] Review and update/close issues #63-73

### Step 3: Create GitHub Project
1. Go to https://github.com/julihocc/dynasir/projects
2. Click "New project"
3. Select "Board" template
4. Name: "DynaSIR Development Roadmap"
5. Add description from this document

### Step 4: Configure Columns
Create 6 columns with automation:
1. **Current Sprint (v0.10.0)** - No automation
2. **Next Release (v0.11.0)** - Auto-add issues with v0.11.0 milestone
3. **Backlog - High Priority** - Manual placement
4. **Backlog - Research** - Manual placement
5. **Documentation** - Auto-add issues with "documentation" label
6. **Completed (Archive)** - Auto-move closed issues, auto-archive after 90 days

### Step 5: Populate Project Board
**Batch 1: Next Release (v0.11.0)**
- Add issues #144, #146, #93, #94, #96, #109
- Set milestone to v0.11.0
- Apply priority labels

**Batch 2: Backlog - High Priority**
- Add issues #110, #112, #145, #124-126
- Set milestone to v1.0.0 or "Future"
- Apply "enhancement" labels

**Batch 3: Documentation**
- Add issue #94
- Add any documentation-labeled issues from #63-73
- Apply "documentation" label

**Batch 4: Completed Archive**
- Add recently closed issues #111, #120-122
- Add multi-backend issues #82-92
- Set filter to auto-archive after 90 days

### Step 6: Configure Views
Create custom views:
1. **By Priority** - Group by priority label (high/medium/low)
2. **By Milestone** - Group by milestone (v0.10.0/v0.11.0/v1.0.0)
3. **By Epic** - Filter by parent issue (#97, #103, #108)
4. **By Status** - Default board view (columns)

---

## Milestones

### Create/Update Milestones

1. **v0.10.0** (CURRENT)
   - Due: December 2025
   - Status: 95% complete (reporting tools branch)
   - Issues: 0-2 remaining

2. **v0.11.0** (NEXT)
   - Due: January 2026
   - Status: Planning phase
   - Issues: 8-12 total

3. **v1.0.0** (FUTURE)
   - Due: Q2 2026
   - Status: Roadmap phase
   - Issues: 15-20 planned

---

## Labels to Apply

### Priority Labels
- `priority-high` (red) - Blockers, critical bugs
- `priority-medium` (yellow) - Important features
- `priority-low` (blue) - Nice-to-have enhancements

### Type Labels
- `bug` (red) - Something broken
- `enhancement` (green) - New features
- `documentation` (blue) - Docs improvements
- `testing` (purple) - Test suite additions
- `performance` (orange) - Speed/memory optimization
- `release` (pink) - Release preparation tasks

### Epic Labels
- `epic` (dark blue) - Parent tracking issues (#97, #103, #108)
- `phase-1`, `phase-2`, `phase-3`, `phase-4` - Epic sub-phases

### Status Labels (Optional)
- `in-progress` (yellow) - Actively being developed
- `blocked` (red) - Waiting on dependencies
- `needs-review` (purple) - Awaiting feedback

---

## Automation Rules

### Recommended GitHub Actions Workflows

1. **Auto-assign to Project**
   - Trigger: Issue opened
   - Action: Add to "Backlog - High Priority" column
   - Filter: Issues with label `enhancement` or `bug`

2. **Move to Next Release on Milestone**
   - Trigger: Milestone assigned (v0.11.0)
   - Action: Move to "Next Release (v0.11.0)" column

3. **Auto-archive Completed**
   - Trigger: Issue closed for >90 days
   - Action: Archive from "Completed" column

4. **Stale Issue Warning**
   - Trigger: No activity for 60 days (for open issues)
   - Action: Add comment asking for status update
   - Label: `stale`

---

## Maintenance Schedule

### Weekly Review (Every Monday)
- Move completed issues to "Completed" column
- Update issue progress notes
- Reassess priorities in "Next Release"
- Add new issues to appropriate columns

### Sprint Planning (Every 2 Weeks)
- Review "Next Release" readiness
- Move issues between backlog and active sprint
- Update epic progress percentages
- Adjust milestone due dates if needed

### Quarterly Planning (Every 3 Months)
- Review v1.0.0 roadmap alignment
- Archive old completed issues (>90 days)
- Create new milestones for future releases
- Update project board structure if needed

---

## Success Metrics

Track these KPIs monthly:

1. **Velocity**: Issues completed per week (target: 2-3)
2. **Cycle Time**: Days from "Next Release" to "Completed" (target: <14 days)
3. **Milestone Progress**: % completion of v0.11.0 (target: 100% by January)
4. **Backlog Health**: Issues in backlog with no milestone (target: <20%)
5. **Stale Issues**: Open issues >60 days with no activity (target: <10%)

---

## References

- GitHub Projects Docs: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- DynaSIR Repository: https://github.com/julihocc/dynasir
- Issue List: https://github.com/julihocc/dynasir/issues
- Proposed New Issues: `PROPOSED_ISSUES_v0.11.0.md`

---

## Appendix: Full Issue List by Category

### Epics (3 total)
- #97: Multi-Backend Refactoring (95% complete)
- #103: Phase 2 Core Extensions (status unknown)
- #108: Phase 3 Advanced Features (25% complete)

### v0.11.0 Candidates (10-12 issues)
- #144 (NEW): v0.11.0 Release Preparation
- #146 (NEW): Backward Compatibility Tests
- #93: Backward compatibility tests
- #94: Update CLAUDE.md
- #96: Update pyproject.toml
- #109: Outbreak metrics
- Plus: relevant issues from #63-73 after review

### Backlog - High Priority (8-10 issues)
- #145 (NEW): Performance Benchmarking
- #110: Probabilistic forecasting
- #112: Coverage-based SIRDV
- #124-126: Outbreak monitoring

### Recently Completed (Archive)
- #111, #120-122: Scenario analysis
- #82-92: Multi-backend implementation
- #113-119: SIRDV features
- Phases 1-2 measles integration

### Needs Review (11 issues)
- #63-73: November 2025 priority block

---

**End of Document**
