# GitHub Project Setup Guide

## Created Issues Summary

Successfully created **17 GitHub issues** from ROADMAP.md and combined_todo_document.md.

**Note:** Some duplicate issues (42-45, 57-61) were created and subsequently closed.

### Phase 1 - Foundation Setup (COMPLETED)
- [Issue #23](https://github.com/julihocc/dynasir/issues/23): Extract exceptions to core module
- [Issue #24](https://github.com/julihocc/dynasir/issues/24): Migrate to pyproject.toml  
- [Issue #25](https://github.com/julihocc/dynasir/issues/25): Configure development tools
- [Issue #26](https://github.com/julihocc/dynasir/issues/26): Set up basic package structure
- [Issue #27](https://github.com/julihocc/dynasir/issues/27): Initialize test framework

### Phase 2 - Core Extraction (COMPLETED)
- [Issue #46](https://github.com/julihocc/dynasir/issues/46): Extract DataContainer class
- [Issue #47](https://github.com/julihocc/dynasir/issues/47): Create abstract base classes
- [Issue #48](https://github.com/julihocc/dynasir/issues/48): Extract Model class
- [Issue #49](https://github.com/julihocc/dynasir/issues/49): Extract transformation utilities

### Phase 3 - Advanced Features (COMPLETED)
- [Issue #50](https://github.com/julihocc/dynasir/issues/50): Analysis Module Extraction
- [Issue #51](https://github.com/julihocc/dynasir/issues/51): Modern Pandas Syntax Migration

### Future Phases (PLANNED)
- [Issue #52](https://github.com/julihocc/dynasir/issues/52): DataContainer Refactoring - Separation of Concerns
- [Issue #53](https://github.com/julihocc/dynasir/issues/53): Model Class - VAR Forecasting Separation
- [Issue #54](https://github.com/julihocc/dynasir/issues/54): Configuration Management System
- [Issue #55](https://github.com/julihocc/dynasir/issues/55): Performance Optimizations
- [Issue #56](https://github.com/julihocc/dynasir/issues/56): Enhanced Documentation and Tutorials

## Labels Created

The following labels were created for organization:
- `phase-1` - Phase 1: Foundation Setup (Blue #0052CC)
- `phase-2` - Phase 2: Core Extraction (Green #00875A)
- `phase-3` - Phase 3: Advanced Features (Red #FF5630)
- `completed` - Task completed (Bright Green #00FF00)
- `testing` - Testing related (Yellow #FFAB00)
- `refactoring` - Code refactoring (Purple #6554C0)
- `documentation` - Documentation improvements (Gold #FFC400)

## Quick Start: View Created Issues

All active issues can be viewed at: https://github.com/julihocc/dynasir/issues

Filter by label:
```powershell
# View all Phase 1 completed tasks
gh issue list --label "phase-1,completed"

# View all refactoring work
gh issue list --label "refactoring"

# View future planned work
gh issue list --search "Future in:title"
```

## Creating the GitHub Project

To create a GitHub Project and organize these issues:

### Option 1: Via GitHub Web Interface

1. Go to https://github.com/julihocc/dynasir/projects
2. Click "New Project"
3. Choose "Board" template
4. Name it: "DynaSIR v1.0 Refactoring Roadmap"
5. Add description from ROADMAP.md

### Option 2: Update GitHub CLI Token Permissions (Projects v2 required scope)

If you prefer automation via CLI (GraphQL under the hood):

1. Open: https://github.com/settings/tokens
2. Create NEW token (recommended) with scopes: `repo`, `read:org`, `workflow`, `project` (critical).
3. (Fine-grained PAT) ensure repository access includes `dynasir` and set **Projects** permission to Read & Write.
4. Authenticate / refresh locally:
   ```powershell
   gh auth login          # choose HTTPS, paste token when prompted
   gh auth status
   gh auth refresh -h github.com -s project
   ```
5. Sanity check GraphQL access:
   ```powershell
   gh api graphql -f query='query { viewer { login } }'
   ```
6. (Optional) Verify token has project scope by attempting a dry-run create (will fail fast if missing):
   ```powershell
   gh api graphql -f query='query { rateLimit { remaining } }'
   ```

### Option 2b: Use Automation Script (Recommended)

Script provided: `scripts/create_github_project.ps1`

Run after granting scopes:
```powershell
pwsh ./scripts/create_github_project.ps1
```
What the script does:
- Resolves owner node id
- Creates Project V2 (title: DynaSIR v1.0 Refactoring Roadmap)
- Links the project to the repository so it shows under the repo Projects tab
- Adds issues #23-27, #46-49, #50-51, #52-56 automatically

Verbose mode:
```powershell
pwsh ./scripts/create_github_project.ps1 -Verbose
```

If you encounter scope errors, re-run:
```powershell
gh auth refresh -h github.com -s project
pwsh ./scripts/create_github_project.ps1
```

### Option 2c: Manual CLI (Older gh without project extension)

If you install the official projects extension (optional):
```powershell
gh extension install github/gh-projects
```
Then (if supported by your gh version):
```powershell
gh projects create --owner julihocc --title "DynaSIR v1.0 Refactoring Roadmap"
```

Otherwise fall back to GraphQL (Option 3 below) or the script.

Note: GitHub Projects v2 are owned by a user or organization. To make a project appear at the repository level, link it to the repository (the automation script performs this via the `linkProjectV2ToRepository` mutation).

### GraphQL Mutations Reference

Create project:
```graphql
mutation($ownerId:ID!, $title:String!) {
  createProjectV2(input:{ownerId:$ownerId, title:$title}) {
    projectV2 { id title url number }
  }
}
```

Add issue to project:
```graphql
mutation($projectId:ID!, $contentId:ID!) {
  addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}) {
    item { id }
  }
}
```

PowerShell loop (manual alternative):
```powershell
$issues = 23,24,25,26,27,46,47,48,49,50,51,52,53,54,55,56
$projectId = 'REPLACE_WITH_PROJECT_ID'
foreach ($n in $issues) {
  $node = gh api repos/julihocc/dynasir/issues/$n --jq .node_id
  gh api graphql -f query='mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}' -F p=$projectId -F c=$node
  Start-Sleep -Milliseconds 300
}
```

### Option 3: Use GitHub Projects API Directly

```powershell
# Get repository ID
gh api repos/julihocc/dynasir --jq '.node_id'

# Create project (requires project scope)
gh api graphql -f query='
  mutation {
    createProjectV2(input: {
      ownerId: "MDQ6VXNlcjUyMzE1ODI="
      title: "DynaSIR v1.0 Refactoring Roadmap"
    }) {
      projectV2 {
        id
        number
        url
      }
    }
  }
'
```

## Project Board Organization

Recommended columns:

1. **Backlog** - Future planned work (Issues 52-56)
2. **In Progress** - Currently being worked on
3. **Completed** - Done tasks (Issues 23-51)
4. **Blocked** - Waiting on dependencies

## Linking Documents

The project is based on two key documents:

1. **ROADMAP.md** - High-level phases and achievements
2. **combined_todo_document.md** - Detailed technical analysis

Both documents should be referenced in the project description or pinned as project resources.

## Next Steps

1. Create the GitHub Project using one of the methods above
2. Add all created issues (23-56) to the project
3. Organize issues into appropriate columns
4. Add milestones for each phase
5. Set up project views by phase labels

## Issue URLs

All created issues are available at:
- https://github.com/julihocc/dynasir/issues/23 through /56

You can view all refactoring-related issues with:
```
gh issue list --label refactoring
gh issue list --label phase-1,completed
```

## Repository Information

- Repository: julihocc/dynasir
- Owner: julihocc
- Current Branch: agentic-refactorization
- Project Scope: Repository-level (not organization-level)

---

Generated: November 21, 2025
Source Documents: ROADMAP.md, combined_todo_document.md
