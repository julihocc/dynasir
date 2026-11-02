# GitHub Project Board Setup Guide

**Status**: Ready for Manual Creation  
**Date**: December 26, 2025

---

## Quick Setup (5-10 minutes)

### Step 1: Navigate to Projects
1. Go to https://github.com/julihocc/dynasir
2. Click the **"Projects"** tab at the top
3. Click **"New project"** button

### Step 2: Create Board
1. **Project name**: `DynaSIR Development Roadmap`
2. **Description**: `Centralized tracking for dynasir library development across releases v0.10.0 through v1.0.0, including feature development, bug fixes, documentation, and performance optimization.`
3. **Template**: Select **"Table"** or **"Board"** (Board recommended)
4. Click **"Create project"**

### Step 3: Create Custom Columns

After project is created, you'll see a default "Status" column. Customize it to these 6 columns:

#### Column 1: Current Sprint (v0.10.0)
- Status: Active development
- Color: Red/Orange
- Issues: None currently (v0.10.0 complete)

#### Column 2: Next Release (v0.11.0)
- Status: Planned for immediate release
- Color: Blue
- Auto-add: Issues with v0.11.0 milestone
- **Initial issues to add:**
  - #147 (v0.11.0 PyPI Release Preparation)
  - #146 (Backward Compatibility Tests)
  - #93 (From multi-backend epic)
  - #94 (Update CLAUDE.md)
  - #96 (Update pyproject.toml)
  - #109 (Outbreak metrics)

#### Column 3: Backlog - High Priority
- Status: Important features for v1.0.0 or next minor release
- Color: Yellow/Amber
- **Issues to add:**
  - #145 (Performance Benchmarking)
  - #110 (Probabilistic forecasting)
  - #112 (Coverage-based SIRDV)
  - #124 (Outbreak monitoring - part 1)
  - #125 (Outbreak monitoring - part 2)
  - #126 (Outbreak monitoring - part 3)

#### Column 4: Backlog - Research & Exploration
- Status: Exploratory work, future directions
- Color: Purple
- **Issues to add:**
  - Any experimental feature requests
  - Future LSTM backend improvements
  - Spatial epidemic modeling (future)
  - Bayesian parameter estimation (future)

#### Column 5: Documentation
- Status: Documentation improvements and guides
- Color: Green
- **Issues to add:**
  - #94 (Update CLAUDE.md - also in v0.11.0)
  - Any documentation-labeled issues from #63-73
  - PERFORMANCE_GUIDE.md creation tasks
  - API reference improvements

#### Column 6: Completed (Archive)
- Status: Recently completed work (reference only)
- Color: Gray
- Auto-move: Closed issues for >90 days
- **Initial issues to add:**
  - #111 (Scenario analysis - closed)
  - #120 (create_scenario - closed)
  - #121 (compare_scenarios - closed)
  - #122 (Scenario example - closed)
  - #82-92 (Multi-backend phases 1-3)
  - #113-119 (SIRDV implementation)

---

## Step 4: Configure Automation (Optional but Recommended)

### Auto-add to v0.11.0 Column
1. Click the three dots (...) next to "Next Release (v0.11.0)" column
2. Select **"Manage automation"**
3. Set to: Auto-add issues with milestone **v0.11.0**

### Auto-move to Completed
1. Click three dots next to "Completed (Archive)" column
2. Select **"Manage automation"**
3. Set to: Auto-move closed issues

### Auto-archive Completed
1. In the completed column settings
2. Enable "Archive after X days" (recommended: 90 days)

---

## Step 5: Create Views (Optional)

GitHub Projects allows multiple views of the same board:

### View 1: Priority View
- Group by: **Priority label** (high-priority, medium, low)
- Sort by: Creation date

### View 2: Milestone View
- Group by: **Milestone** (v0.10.0, v0.11.0, v1.0.0)
- Sort by: Due date

### View 3: Epic View
- Filter by: **Epic** issues only
- Show: Epic parent + child issues

### View 4: Default Status View
- Group by: **Column** (current board layout)
- Sort by: Priority

---

## Step 6: Add Issues to Project

### Batch 1: Next Release (v0.11.0) - Priority
1. Open each issue:
   - #147, #146, #93, #94, #96, #109
2. On the issue page, scroll to "Projects" section
3. Click **"Add to project"**
4. Select **"DynaSIR Development Roadmap"**
5. Set column to **"Next Release (v0.11.0)"**

### Batch 2: Backlog - High Priority
1. Issues: #145, #110, #112, #124, #125, #126
2. Add to project, column: **"Backlog - High Priority"**

### Batch 3: Documentation
1. Issues: #94 (if not already added)
2. Filter #63-73 for documentation items
3. Add to project, column: **"Documentation"**

### Batch 4: Completed Archive
1. Issues: #111, #120-122, #82-92
2. Add to project, column: **"Completed (Archive)"**

---

## Step 7: Configure Project Settings

### Access & Visibility
1. Click **"Settings"** (three dots in top right)
2. **Public or Private**: Recommend **Public** (matches repo)
3. **Permissions**: Only repository admins can manage

### Custom Fields (Optional)

Add custom fields for better tracking:

- **Effort Estimate**: Small (1-2 days), Medium (3-5 days), Large (1+ week)
- **Status**: Not Started, In Progress, In Review, Blocked, Waiting
- **Component**: Data, Models, Analysis, Infrastructure, Documentation
- **Target Version**: v0.10.0, v0.11.0, v1.0.0, Backlog

---

## Step 8: Share & Maintain

### Share with Team
- Copy project link: https://github.com/julihocc/dynasir/projects/[project-number]
- Add to repository README
- Include in development documentation

### Weekly Maintenance
- **Every Monday**: Move completed issues to "Completed" column
- **Every Monday**: Update issue progress in descriptions
- **Biweekly**: Reassess priorities in "Next Release" column
- **Monthly**: Update epic progress percentages

### Sprint Planning (Biweekly)
- Move issues from "Backlog" to "Next Release" as work begins
- Ensure HIGH priority issues are in Next Release column
- Identify blockers in current sprint

---

## Troubleshooting

### Issue: Can't find Projects tab
- **Solution**: Make sure you're on the repository page, not your profile
- URL should be: https://github.com/julihocc/dynasir

### Issue: Automation not working
- **Solution**: Ensure you have admin/maintain permissions on the repository
- Click **"Settings"** > **"Collaborators"** to check your role

### Issue: Can't add specific issue to project
- **Solution**: Close and reopen the issue page, or refresh the browser
- Ensure the project is public if issue is public

### Issue: Custom fields not appearing
- **Solution**: Custom fields are available in table view only
- Switch to **"Table"** view from the view dropdown

---

## Reference: Issue Categorization

### Next Release (v0.11.0) - Must Complete
```
#147 - Release Preparation (BLOCKER if #146 not done)
#146 - Backward Compatibility Tests (BLOCKER)
#93  - Implement Backward Compatibility Tests
#94  - Update CLAUDE.md
#96  - Update pyproject.toml
#109 - Outbreak Metrics
```

### Backlog - High Priority (v1.0.0)
```
#145 - Performance Benchmarking
#110 - Probabilistic Forecasting
#112 - Coverage-based SIRDV
#124 - Outbreak Monitoring Part 1
#125 - Outbreak Monitoring Part 2
#126 - Outbreak Monitoring Part 3
```

### Completed (Reference)
```
#111, #120-122 - Scenario Analysis (v0.9.1)
#82-92 - Multi-backend Refactoring (v0.8.0)
#113-119 - SIRDV Implementation (v0.6.1)
Phases 1-2 Measles Integration
```

---

## Links

- **GitHub Projects Docs**: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- **Repository**: https://github.com/julihocc/dynasir
- **Issues**: https://github.com/julihocc/dynasir/issues
- **New Issue #147**: https://github.com/julihocc/dynasir/issues/147
- **New Issue #145**: https://github.com/julihocc/dynasir/issues/145
- **New Issue #146**: https://github.com/julihocc/dynasir/issues/146

---

## Completion Checklist

- [ ] Project created with name "DynaSIR Development Roadmap"
- [ ] 6 columns configured (Current Sprint, Next Release, Backlog High, Backlog Research, Documentation, Completed)
- [ ] Automation rules configured (v0.11.0 milestone, auto-move closed)
- [ ] 24+ issues added to appropriate columns
- [ ] Custom views created (optional)
- [ ] Project link shared in README or team documentation
- [ ] Weekly maintenance schedule established

---

**Estimated Setup Time**: 15-20 minutes  
**Status**: Ready for Manual Creation  
**Date**: December 26, 2025
