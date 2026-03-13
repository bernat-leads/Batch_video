# CLAUDE.md — Internal Tool Template

This file is automatically loaded at the start of every Claude Code session.

---

## What This Is

This is the **development workspace** for an **internal tool application** — a React SPA with TanStack Router and a FastAPI backend. No AI agents, no CMS, no auth (add your own). Built on the [monorepo-base-template](https://github.com/Hyperion-AI-Agency/monorepo-base-template).

## Mandatory Workflow

**Claude must NEVER jump straight to writing code for new tasks or features.** The workflow is always:

1. **`/prime`** → 2. **`/plan`** → 3. **Review** → 4. **`/implement`**

## Task Management (Linear MCP)

Tasks are managed in **Linear** via MCP server (configured in `.claude/.mcp.json`).

## Test-Driven Development (TDD)

**Tests must be written BEFORE implementation code.**

Backend tests: `apps/api/__tests__/` (pytest)
E2E tests: `apps/react/e2e/` (Playwright)

---

## Quick Reference

| What | Where |
|------|-------|
| React app | `apps/react/` (Vite + TanStack Router) |
| Backend API | `apps/api/` (FastAPI) |
| API modules | `apps/api/api/` (routes, models, schemas, crud) |
| Celery worker | `apps/api/worker/` (optional) |
| UI components | `packages/ui/` (shadcn/ui) |
| Analytics | `packages/analytics/` (PostHog) |
| Sentry | `packages/sentry/` |
| API client | `packages/api-client/` (Orval-generated) |
| Email templates | `packages/email/` |
| Env config (React) | `apps/react/src/env.ts` (t3-env) |
| Env config (FastAPI) | `apps/api/api/settings.py` (Pydantic) |
| E2E tests | `apps/react/e2e/` (Playwright) |
| Backend tests | `apps/api/__tests__/` (pytest) |
| Storybook | `apps/storybook/` |
| Keycloak theme | `apps/keycloak-theme/` |
| Tooling | `tooling/` (typescript-config, prettier-config, eslint-config) |

## Git Workflow

- **Commit messages follow Conventional Commits** for semantic-release
- PR flow: feature branch → `dev` → `main`

## Key Commands

```bash
pnpm dev                    # Start all apps
pnpm build                  # Build everything
pnpm lint                   # Lint all packages
pnpm test                   # Run all tests
pnpm db:migrate             # Run DB migrations
pnpm run generate-api       # Regenerate FastAPI client
poetry run start            # Start FastAPI only
poetry run pytest           # Backend tests only
```
