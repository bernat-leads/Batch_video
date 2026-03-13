# Create Task

Turn a loose idea, rough notes, or scattered input into a structured, plannable task document.

## Variables

input: $ARGUMENTS (describe the task — can include rough ideas, file paths, screenshots, user quotes, or anything that conveys intent)

---

## Instructions

**You are creating a TASK DOCUMENT, not a plan or implementation.** Your job is to take messy, unstructured input and produce a clear, Jira-like task that can later be fed to `/plan`.

---

## Phase 1: Parse the Input

1. Read the input carefully — it may be rough, partial, or conversational
2. If file paths are mentioned, read those files to extract relevant context
3. If the input references existing code, scan the codebase to understand the current state
4. Identify:
   - **What** needs to be done (the core ask)
   - **Why** it matters (motivation, user need, bug impact)
   - **Where** in the stack it touches (frontend, backend, database, agent, packages, infra)
   - **Type** of work: feature | bug | improvement | chore | refactor

---

## Phase 2: Generate Task ID

1. Use today's date: `YYYY-MM-DD`
2. Check `.claude/tasks/` for existing files starting with today's date
3. Assign the next sequential number (001, 002, etc.)
4. Create a descriptive slug from the task title (lowercase, hyphenated)
5. Full ID format: `TASK-YYYY-MM-DD-NNN`
6. Filename format: `YYYY-MM-DD-NNN-{descriptive-slug}.md`

---

## Phase 3: Write the Task Document

Save the task to `.claude/tasks/YYYY-MM-DD-NNN-{descriptive-slug}.md` using this format:

```
# Task: [Clear, concise title]

**ID:** TASK-YYYY-MM-DD-NNN
**Created:** YYYY-MM-DD
**Type:** feature | bug | improvement | chore | refactor
**Priority:** high | medium | low
**Status:** Open
**Layers:** frontend | backend | database | agent | packages | infra

---

## Summary

[2-3 sentence clear description of what needs to be done and why]

## Background / Context

[Any relevant context, links, user quotes, or file references that informed this task]

## Requirements

- [ ] [Specific, testable requirement]
- [ ] [Specific, testable requirement]
- [ ] [Specific, testable requirement]

## Acceptance Criteria

- [ ] [How to verify this is done correctly]
- [ ] [How to verify this is done correctly]

## References

- [File paths, URLs, screenshots, or related tasks mentioned in the input]

## Notes

[Any open questions, assumptions, or considerations for planning]
```

**Writing guidelines:**

- **Title:** Short, action-oriented (e.g., "Add logout button to profile page")
- **Summary:** Clear enough that someone unfamiliar with the conversation could understand
- **Requirements:** Break vague requests into specific, testable items
- **Acceptance Criteria:** Describe observable outcomes, not implementation details
- **Priority:** Default to `medium` unless the input suggests urgency or triviality
- **Notes:** Capture any ambiguity — don't guess, flag it as an open question

---

## Phase 4: Present for Review

After creating the task file:

1. Display the full task document
2. Ask if anything needs to be changed or clarified
3. Once confirmed, provide the file path and suggest next step:

```
Task saved to: .claude/tasks/YYYY-MM-DD-NNN-{slug}.md

Next step: /plan .claude/tasks/YYYY-MM-DD-NNN-{slug}.md
```
