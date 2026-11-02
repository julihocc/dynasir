# Multi-Backend Time Series Refactoring - Project Organization

## Overview

This document describes the GitHub project organization for the v0.8.0 Multi-Backend Time Series Refactoring initiative.

## Issues Created

**Total**: 16 issues (#82-#97)
**Milestone**: [v0.8.0 - Multi-Backend Support](https://github.com/julihocc/dynasir/milestone/4)
**Meta Issue**: [#97 - Multi-Backend Time Series Refactoring](https://github.com/julihocc/dynasir/issues/97)

### Phase 1: Abstraction Layer (4 issues)
Build the foundation for multi-backend support

| Issue | Title | Est. Hours | Priority |
|-------|-------|------------|----------|
| [#82](https://github.com/julihocc/dynasir/issues/82) | Create BaseForecaster ABC interface | 4-6 | Critical |
| [#83](https://github.com/julihocc/dynasir/issues/83) | Create ForecasterRegistry and decorator pattern | 4-6 | Critical |
| [#84](https://github.com/julihocc/dynasir/issues/84) | Refactor VARForecaster to implement BaseForecaster | 3-4 | High |
| [#85](https://github.com/julihocc/dynasir/issues/85) | Create ForecastingOrchestrator (backend-agnostic) | 6-8 | Critical |

**Total Estimated Time**: 17-24 hours (~3-4 days)

### Phase 2: Model Integration (2 issues)
Integrate the abstraction layer into the Model class

| Issue | Title | Est. Hours | Priority |
|-------|-------|------------|----------|
| [#86](https://github.com/julihocc/dynasir/issues/86) | Add forecaster parameter to Model class | 4-6 | Critical |
| [#87](https://github.com/julihocc/dynasir/issues/87) | Add backend-specific configuration to Settings | 2-3 | Medium |

**Total Estimated Time**: 6-9 hours (~1-2 days)

### Phase 3: New Backends (3 issues)
Implement alternative forecasting backends

| Issue | Title | Est. Hours | Priority |
|-------|-------|------------|----------|
| [#88](https://github.com/julihocc/dynasir/issues/88) | Implement ProphetForecaster backend | 8-10 | High |
| [#89](https://github.com/julihocc/dynasir/issues/89) | Implement ARIMAForecaster backend | 8-10 | High |
| [#90](https://github.com/julihocc/dynasir/issues/90) | Create LSTMForecaster stub for future implementation | 1-2 | Low |

**Total Estimated Time**: 17-22 hours (~3-4 days)

### Phase 4: Testing & Documentation (6 issues)
Comprehensive testing and documentation

| Issue | Title | Est. Hours | Priority |
|-------|-------|------------|----------|
| [#91](https://github.com/julihocc/dynasir/issues/91) | Create comprehensive test suite for ForecasterRegistry | 3-4 | Medium |
| [#92](https://github.com/julihocc/dynasir/issues/92) | Create multi-backend integration tests | 6-8 | Medium |
| [#93](https://github.com/julihocc/dynasir/issues/93) | Add backward compatibility tests for v0.7.0 code | 4-5 | High |
| [#94](https://github.com/julihocc/dynasir/issues/94) | Update CLAUDE.md with multi-backend documentation | 3-4 | Medium |
| [#95](https://github.com/julihocc/dynasir/issues/95) | Create multi_backend_comparison.py example | 4-5 | Low |
| [#96](https://github.com/julihocc/dynasir/issues/96) | Update pyproject.toml with optional dependencies | 1-2 | Medium |

**Total Estimated Time**: 21-28 hours (~3-4 days)

## Overall Timeline

**Total Estimated Time**: 61-83 hours (approximately 3-4 weeks)
**Target Release Date**: January 27, 2025

## Dependency Graph

```
Phase 1 (Foundation)
├─ #82 BaseForecaster ABC ────────┐
├─ #83 ForecasterRegistry ────────┼──→ #84 VARForecaster refactor ──┐
└─────────────────────────────────┴──→ #85 ForecastingOrchestrator ─┤
                                                                      │
Phase 2 (Integration)                                                 │
└─ #86 Model integration ←────────────────────────────────────────────┤
   └─ #87 Config updates                                              │
                                                                      │
Phase 3 (Backends)                                                    │
├─ #88 ProphetForecaster ←────────────────────────────────────────────┤
├─ #89 ARIMAForecaster ←──────────────────────────────────────────────┤
└─ #90 LSTMForecaster stub ←──────────────────────────────────────────┤
                                                                      │
Phase 4 (Testing & Docs)                                              │
├─ #91 Registry tests ←───────────────────────────────────────────────┘
├─ #92 Multi-backend tests ←──────────────────────────────────────────┐
├─ #93 Backward compat tests ←────────────────────────────────────────┤
├─ #94 Documentation ←─────────────────────────────────────────────────┤
├─ #95 Example script ←────────────────────────────────────────────────┤
└─ #96 Dependencies ←──────────────────────────────────────────────────┘
```

## GitHub Project Setup (Manual)

Since GitHub CLI doesn't have permissions to create projects automatically, follow these manual steps:

### 1. Create the Project

1. Navigate to: https://github.com/julihocc/dynasir/projects
2. Click **"New project"**
3. Choose **"Board"** template
4. Set name: **"Multi-Backend Time Series Refactoring"**
5. Set description: **"v0.8.0 - Add support for multiple forecasting backends (VAR, Prophet, ARIMA, LSTM)"**
6. Click **"Create project"**

### 2. Configure Custom Fields

Add these custom fields to track additional metadata:

| Field Name | Type | Options |
|------------|------|---------|
| **Phase** | Single select | Phase 1, Phase 2, Phase 3, Phase 4 |
| **Estimated Hours** | Number | (range: 1-10) |
| **Priority** | Single select | Critical, High, Medium, Low |

### 3. Create Views

Set up these views for different perspectives:

#### Board View (Default)
Columns:
- **Backlog** - All open issues not yet started
- **Ready** - Issues ready to work on (dependencies met)
- **In Progress** - Currently being worked on
- **In Review** - Has PR, awaiting review
- **Done** - Closed issues

#### Timeline View
- Group by: Phase
- Sort by: Estimated Hours (descending)
- Show dependencies

#### Table View
Columns to show:
- Issue number and title
- Phase
- Priority
- Estimated Hours
- Assignees
- Status

### 4. Add All Issues to Project

**Automated approach** (if you have project created):
```bash
# Replace PROJECT_NUMBER with your project number
PROJECT_NUMBER=1  # Update this

for i in {82..97}; do
  gh issue edit $i --add-project "Multi-Backend Time Series Refactoring"
done
```

**Manual approach**:
1. Open each issue (#82-#97)
2. Click "Projects" in right sidebar
3. Select "Multi-Backend Time Series Refactoring"
4. Set Phase field (Phase 1/2/3/4)
5. Set Priority (Critical/High/Medium/Low)

### 5. Organize Issues by Phase

Use the custom "Phase" field to group issues:

| Phase | Issues |
|-------|--------|
| Phase 1 | #82, #83, #84, #85 |
| Phase 2 | #86, #87 |
| Phase 3 | #88, #89, #90 |
| Phase 4 | #91, #92, #93, #94, #95, #96 |

### 6. Set Priorities

**Critical** (blocks other work):
- #82 BaseForecaster ABC
- #83 ForecasterRegistry
- #85 ForecastingOrchestrator
- #86 Model integration

**High** (core features):
- #84 VARForecaster refactor
- #88 ProphetForecaster
- #89 ARIMAForecaster
- #93 Backward compatibility tests

**Medium** (important but not blocking):
- #87 Config updates
- #91 Registry tests
- #92 Multi-backend tests
- #94 Documentation
- #96 Dependencies

**Low** (nice to have):
- #90 LSTM stub
- #95 Example script

## Quick Commands

### View Issues by Phase
```bash
# Phase 1
gh issue list --label "phase-1" --state open

# Phase 2
gh issue list --label "phase-2" --state open

# Phase 3
gh issue list --label "phase-3" --state open

# Phase 4
gh issue list --label "phase-4" --state open
```

### View All Project Issues
```bash
gh issue list --milestone "v0.8.0 - Multi-Backend Support" --state all
```

### View Meta Issue
```bash
gh issue view 97
```

### Check Milestone Progress
```bash
gh api repos/julihocc/dynasir/milestones/4 --jq '{title: .title, open: .open_issues, closed: .closed_issues, progress: "\(.closed_issues)/\(.open_issues + .closed_issues)"}'
```

## Progress Tracking

Track overall progress using the meta issue (#97):

1. Open https://github.com/julihocc/dynasir/issues/97
2. Update phase checkboxes as work completes
3. Link pull requests as they're created
4. Document any blockers or plan changes

## Success Metrics

- [ ] All 16 issues closed
- [ ] 100% backward compatibility verified
- [ ] Test coverage >90% for new modules
- [ ] Documentation complete
- [ ] Example script runs successfully
- [ ] Zero breaking changes in default usage

## Resources

- **Implementation Plan**: `/home/codespace/.claude/plans/goofy-questing-moore.md`
- **Repository**: https://github.com/julihocc/dynasir
- **Meta Issue**: https://github.com/julihocc/dynasir/issues/97
- **Milestone**: https://github.com/julihocc/dynasir/milestone/4
- **Issues**: https://github.com/julihocc/dynasir/issues?q=is%3Aissue+milestone%3A%22v0.8.0+-+Multi-Backend+Support%22

## Next Steps

1. ✅ Issues created (#82-#97)
2. ✅ Milestone created (v0.8.0)
3. ✅ Issues assigned to milestone
4. ⏳ Create GitHub project (manual step required)
5. ⏳ Add issues to project
6. ⏳ Begin Phase 1 implementation (#82)

---

*Last Updated: 2025-01-29*
