# Implement

Execute an implementation plan created by `/plan`. Read the plan, write production code, and verify the work.

## Variables

plan_path: $ARGUMENTS (path to the plan file, e.g., `.claude/plans/2026-02-18-add-ei-dimension.md`)

---

## Phase 1: Load Context

1. **Read the plan file completely.** Understand every section.
2. **Read relevant reference docs** based on the plan's "Layers" field:
   - Frontend → `apps/mkdocs/docs/reference/frontend.md`
   - Backend → `apps/mkdocs/docs/reference/backend.md`
   - Database → `apps/mkdocs/docs/reference/database.md`
   - Agent → `apps/mkdocs/docs/reference/agent-system.md`
   - Always → `apps/mkdocs/docs/reference/coding-conventions.md`
3. **Verify prerequisites:**
   - Are there open questions? If yes, ask the user before proceeding.
   - Are there dependencies? Check they're met.

---

## Phase 2: Execute

Follow the plan's Implementation Steps in exact order.

**For each step:**

1. **Read the target file(s)** — verify the code matches what the plan expects
2. **Write the code** — follow the plan's specifications and coding conventions
3. **Verify** — the change looks correct before moving on

**Code quality rules:**

- Follow patterns documented in `apps/mkdocs/docs/reference/coding-conventions.md`
- Match the style of surrounding code
- Use proper TypeScript types (no `any`)
- Use proper Python type hints
- Import from the correct locations (check reference docs)
- Handle errors appropriately for the layer (frontend vs backend)

---

## Phase 3: Post-Implementation

After all steps are complete:

1. **Run relevant checks:**
   - If frontend changed: `pnpm lint` (or check for type errors)
   - If backend changed: `poetry run pytest` (if tests exist)
   - If API schemas changed: `pnpm run generate-api`
   - If DB models changed: generate migration
2. **Verify the Validation checklist** from the plan
3. **Update the plan status** — change "Draft" to "Implemented", add implementation notes

---

## Phase 4: Report

```
## Implementation Complete

### Summary
- [What was done]

### Files Changed
**Created:**
- `path/to/new-file.ts`

**Modified:**
- `path/to/modified-file.ts`

### Validation
- [x] [Passed check]
- [ ] [Failed check — with explanation]

### Deviations from Plan
[None, or list what changed and why]

### Plan Status
Updated `.claude/plans/YYYY-MM-DD-{name}.md` to "Implemented"
```
