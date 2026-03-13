# Plan

Create a code-aware implementation plan for a feature, fix, or change to the Human Maps application.

## Variables

requirements: $ARGUMENTS (describe the feature, fix, or change you want to implement — can also be a path to a task file from `/create-task`, e.g. `.claude/tasks/2026-02-18-001-add-logout-button.md`)

---

## Instructions

**You are creating a PLAN, not implementing code.** Research the codebase thoroughly, then produce a detailed plan document.

**If the input is a task file path** (e.g. `.claude/tasks/*.md`), read that file first and use its Requirements, Acceptance Criteria, and Context as the basis for the plan.

---

## Phase 1: Understand the Request

1. Read the requirements carefully
2. Identify which layers of the stack are involved (frontend, backend, agent, database, packages)
3. Read the relevant reference docs from `apps/mkdocs/docs/reference/`:
   - Frontend work → read `apps/mkdocs/docs/reference/frontend.md`
   - Backend work → read `apps/mkdocs/docs/reference/backend.md`
   - Database changes → read `apps/mkdocs/docs/reference/database.md`
   - Agent changes → read `apps/mkdocs/docs/reference/agent-system.md`
   - Package changes → read `apps/mkdocs/docs/reference/shared-packages.md`
   - Infra changes → read `apps/mkdocs/docs/reference/infrastructure.md`
   - Always read `apps/mkdocs/docs/reference/coding-conventions.md`

---

## Phase 2: Scan the Codebase

**This is critical.** Before writing any plan, scan the actual code.

1. **Find relevant files:** Use glob/grep to locate files related to the request
   - Search for related component names, function names, route patterns
   - Look for existing patterns similar to what's being requested
2. **Read key files:** Read the most relevant files completely
   - For each file, note the full path, key line numbers, and important code patterns
3. **Identify touchpoints:** Find all files that will need to change
   - Trace the data flow: UI component → API call → backend route → model → database
4. **Find examples to follow:** Locate the closest existing implementation to what's being built
   - If adding a new page, find a similar existing page
   - If adding a new endpoint, find a similar existing endpoint
   - If adding a new agent node, study existing nodes

---

## Phase 3: Write the Plan

Create the plan in `.claude/plans/` with filename: `YYYY-MM-DD-{descriptive-name}.md`

Use this format:

```
# Plan: [Descriptive Title]

**Created:** YYYY-MM-DD
**Status:** Draft
**Request:** [one-line summary]
**Layers:** [frontend | backend | database | agent | packages | infra]

---

## Overview

[2-3 sentences: what will be built and why]

## Relevant Code

### Existing Files (will be modified)

For each file that needs changes:

**`path/to/file.ts`** (lines X-Y)
- Purpose: [what this file does]
- Changes needed: [what needs to change]
- Key code:
  ```
  [relevant snippet from the file, with line numbers]
  ```

### Reference Files (patterns to follow)

For each file that serves as an example:

**`path/to/example.ts`**
- Pattern: [what pattern this demonstrates]
- Key code:
  ```
  [relevant snippet showing the pattern]
  ```

### New Files to Create

For each new file:

| File Path | Purpose | Pattern Source |
|-----------|---------|---------------|
| `path/to/new-file.ts` | [what it does] | [existing file it's modeled after] |

## Database Changes

[If applicable: new tables, columns, migrations needed]

## API Changes

[If applicable: new endpoints, schema changes, client regeneration]

## Implementation Steps

### Step 1: [Title]

**What:** [Clear description]
**Where:** `path/to/file.ts` (lines X-Y)
**How:**
- [Specific action with code reference]
- [Specific action with code reference]

**Code to write:**
```
[Actual code or pseudo-code for this step]
```

### Step 2: [Title]
... (continue for all steps)

## Testing

- [ ] [What to test and how]
- [ ] [What to test and how]

## Validation

- [ ] [How to verify the implementation works]
- [ ] Conventions followed (check against coding-conventions.md)
- [ ] No regressions in existing functionality
```

---

## Phase 4: Report

After creating the plan:

1. Summarize what the plan covers
2. List any open questions
3. Provide the full path: `.claude/plans/YYYY-MM-DD-{name}.md`
4. Remind user to run `/implement .claude/plans/YYYY-MM-DD-{name}.md` to execute
