# DynaSIR Development Roadmap - Project Organization

**Status**: ✅ ORGANIZED VIA LABELS  
**Date**: December 26, 2025  
**Alternative**: Use GitHub Project board (manual creation still available)

---

## Project Organization via Labels (GitHub CLI)

Since the GITHUB_TOKEN scope doesn't include V2 Project creation permissions, we've organized all issues using a **label-based system** via the GitHub CLI. This provides the same organizational benefits with full automation.

---

## 🏷️ Label System Overview

### Project Location Labels

| Label | Color | Issues | Purpose |
|-------|-------|--------|---------|
| `project-v0.11.0` | Blue | #147, #146, #109, #93, #94, #96 | Next release candidates |
| `project-backlog-high` | Amber | #145, #110, #112, #124, #125, #126 | High priority backlog |
| `project-backlog-research` | Purple | Future issues | Research & exploration |

### Component Labels (for filtering)

| Label | Color | Purpose |
|-------|-------|---------|
| `component-data` | Blue | Data handling & validation |
| `component-models` | Blue | Epidemiological models |
| `component-analysis` | Blue | Analysis & reporting tools |

### Status Labels (for workflow)

| Label | Color | Purpose |
|-------|-------|---------|
| `project-in-progress` | Gray | Currently being worked on |
| `project-blocked` | Red | Waiting on dependencies |

---

## 📋 Current Issue Organization

### Next Release (v0.11.0) - 6 Issues

Issues labeled with `project-v0.11.0`:

1. **#147** - v0.11.0 PyPI Release Preparation (HIGH)
   - Tags: project-v0.11.0, release, enhancement, documentation
   - Depends on: #146

2. **#146** - Implement Backward Compatibility Test Suite (HIGH - BLOCKER)
   - Tags: project-v0.11.0, testing, high-priority
   - Timeline: Must complete before release

3. **#109** - Outbreak-Specific Metrics (MEDIUM)
   - Tags: project-v0.11.0, component-analysis
   - From epic #108

4. **#93** - Backward Compatibility Tests (From #97)
   - Tags: project-v0.11.0, testing
   - Implementation details

5. **#94** - Update CLAUDE.md (From #97)
   - Tags: project-v0.11.0, documentation
   - For multi-backend documentation

6. **#96** - Update pyproject.toml (From #97)
   - Tags: project-v0.11.0, documentation
   - Dependency review

**View all**: https://github.com/julihocc/dynasir/issues?q=label:project-v0.11.0

---

### Backlog - High Priority (v1.0.0) - 6 Issues

Issues labeled with `project-backlog-high`:

1. **#145** - Performance Benchmarking & Profiling Suite
   - Tags: project-backlog-high, performance, enhancement
   - Timeline: v1.0.0 or v0.12.0
   - Priority: Medium (informational)

2. **#110** - Probabilistic Forecasting
   - Tags: project-backlog-high, component-analysis, enhancement
   - From epic #108
   - Timeline: v1.0.0

3. **#112** - Coverage-Based SIRDV with Waning Immunity
   - Tags: project-backlog-high, component-models, enhancement
   - From epic #108
   - Timeline: v1.0.0

4. **#124** - Outbreak Monitoring Integration (Part 1)
   - Tags: project-backlog-high, component-analysis
   - From epic #108

5. **#125** - Outbreak Monitoring Integration (Part 2)
   - Tags: project-backlog-high, component-analysis
   - From epic #108

6. **#126** - Outbreak Monitoring Integration (Part 3)
   - Tags: project-backlog-high, component-analysis
   - From epic #108

**View all**: https://github.com/julihocc/dynasir/issues?q=label:project-backlog-high

---

## 🔗 Quick Filter Links

### By Project Phase

- **Next Release (v0.11.0)**: https://github.com/julihocc/dynasir/issues?q=label:project-v0.11.0
- **Backlog - High Priority**: https://github.com/julihocc/dynasir/issues?q=label:project-backlog-high
- **Backlog - Research**: https://github.com/julihocc/dynasir/issues?q=label:project-backlog-research
- **In Progress**: https://github.com/julihocc/dynasir/issues?q=label:project-in-progress
- **Blocked**: https://github.com/julihocc/dynasir/issues?q=label:project-blocked

### By Component

- **Data Issues**: https://github.com/julihocc/dynasir/issues?q=label:component-data
- **Models Issues**: https://github.com/julihocc/dynasir/issues?q=label:component-models
- **Analysis Issues**: https://github.com/julihocc/dynasir/issues?q=label:component-analysis

### By Type

- **Performance**: https://github.com/julihocc/dynasir/issues?q=label:performance
- **Testing**: https://github.com/julihocc/dynasir/issues?q=label:testing
- **Documentation**: https://github.com/julihocc/dynasir/issues?q=label:documentation
- **Enhancement**: https://github.com/julihocc/dynasir/issues?q=label:enhancement

---

## 🚀 Using the Label System

### To View All Next Release Issues
```bash
# Command line
gh issue list --repo julihocc/dynasir --label project-v0.11.0

# Or use the web link
https://github.com/julihocc/dynasir/issues?q=label:project-v0.11.0
```

### To Add an Issue to the Project
```bash
# Add to v0.11.0
gh issue edit <issue-number> --add-label project-v0.11.0

# Or add to backlog high priority
gh issue edit <issue-number> --add-label project-backlog-high

# And optionally add component labels
gh issue edit <issue-number> --add-label component-analysis
```

### To Track Progress
1. Filter issues by `project-v0.11.0` label
2. Update individual issue status in comments
3. Use `project-in-progress` label when work starts
4. Use `project-blocked` label if dependent on another issue

---

## 📊 Current Status Summary

| Category | Count | Status |
|----------|-------|--------|
| v0.11.0 Issues | 6 | Ready to assign |
| High Priority Backlog | 6 | Planned for v1.0.0 |
| Total in Project | 12 | Organized |
| Blockers | 1 (#146) | Must complete first |

---

## Comparison: Labels vs GitHub Project Board

### Label System (Current - Via GitHub CLI)
✅ **Advantages**:
- Full automation via gh CLI
- Works with existing token
- Multiple label combinations possible
- Instant filtering with URLs
- No additional setup needed
- Can save searches

❌ **Limitations**:
- No visual kanban board
- Requires clicking issue links to see them all
- Limited to 2-3 levels of organization

### GitHub Project Board (Alternative - Manual)
✅ **Advantages**:
- Visual kanban board with swim lanes
- Drag-and-drop interface
- Multiple views (board, table)
- Custom fields
- Better for visual progress tracking

❌ **Limitations**:
- Requires manual creation
- Manual issue assignment to columns
- Need to use web UI

---

## 📈 Next Steps

### Option 1: Continue with Label-Based Organization (Current)
1. Use filter links above to view organized issues
2. Add `project-v0.11.0` label to any new release issues
3. Move issues between labels as they progress
4. Track progress via issue comments

### Option 2: Create GitHub Project Board (Manual)
Follow the guide in `GITHUB_PROJECT_SETUP_GUIDE.md` to:
1. Create visual project board on GitHub web
2. Set up 6 swim lanes
3. Configure automation
4. Drag issues between columns

### Option 3: Hybrid Approach (Recommended)
- Use **labels for filtering** (current system)
- Create **GitHub Project board** for visual tracking
- Labels sync issues to project columns via automation

---

## 🔄 Maintenance Workflow

### Weekly Check-In
```bash
# See all v0.11.0 issues and their current status
gh issue list --repo julihocc/dynasir --label project-v0.11.0 -L 20
```

### When Starting Work
```bash
# Add in-progress label
gh issue edit <issue> --add-label project-in-progress
```

### When Blocked
```bash
# Add blocked label and explain in comment
gh issue edit <issue> --add-label project-blocked
gh issue comment <issue> --body "Blocked on completion of #XXX"
```

### When Completed
```bash
# Remove project labels
gh issue edit <issue> --remove-label project-v0.11.0 project-in-progress
```

---

## 📚 Documentation References

- **Issue #147**: v0.11.0 PyPI Release Preparation
- **Issue #146**: Backward Compatibility Test Suite (BLOCKER)
- **Issue #145**: Performance Benchmarking Suite
- **Setup Guide**: `GITHUB_PROJECT_SETUP_GUIDE.md`
- **Planning Docs**: `GITHUB_PROJECT_PLAN.md`

---

## Conclusion

The project organization is **now complete** using GitHub CLI and the label system:

✅ 3 new issues created (#147, #146, #145)  
✅ Organizational labels created (project-*, component-*)  
✅ 12 issues organized and labeled  
✅ Quick filter links documented  
✅ CLI workflows established  

**Status**: Ready for sprint planning and implementation!

---

**Last Updated**: December 26, 2025  
**Organization Method**: GitHub Labels + CLI  
**Total Issues Organized**: 12 (v0.11.0: 6, Backlog High: 6)
