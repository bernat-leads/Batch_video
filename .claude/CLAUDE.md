# CLAUDE.md — Lead Alliances Bulk Video Pipeline

Bulk video pipeline — mass-produces short-form video ads from Excel scripts via a multi-step API pipeline (TTS → Segmentation → Image Gen → Assembly → Upload).

## Mandatory Workflow

**Never jump straight to code.** Always: `/prime` → `/plan` → Review → `/implement`

## Tasks

Linear MCP (`.claude/.mcp.json`). Project: **Lead Alliances - Bulk Video Pipeline**

## TDD

Tests before code. Backend: `apps/api/__tests__/` (pytest). E2E: `apps/react/e2e/` (Playwright).

## Quick Reference

| What | Where |
|------|-------|
| React app | `apps/react/` |
| Backend API | `apps/api/api/` (routes, models, schemas, crud) |
| Pipeline stages | `apps/api/api/videos/pipeline/` |
| Celery tasks | `apps/api/api/videos/pipeline/tasks.py`, `apps/api/api/batches/tasks.py` |
| API client | `packages/api-client/` (Orval-generated) |
| Settings | `apps/api/api/settings.py` (Pydantic, `env_prefix="API_"`) |

## Architecture Docs

Read these when working on the relevant area:

- **[Pipeline Architecture](.claude/docs/pipeline-architecture.md)** — flow, ownership, retry strategy, adding providers
- **[Backend Patterns](.claude/docs/backend-patterns.md)** — async/sync rules, DB engines, module structure, services, settings, error handling, types
- **[Frontend Patterns](.claude/docs/frontend-patterns.md)** — file org, API calls, code splitting, SSE, transitions, styling

## SOPs — Reusable Patterns & Standards

Reference these when building new features, refactoring, or starting new projects:

| SOP | Read when... |
|-----|-------------|
| **[Backend SOP](.claude/docs/sops/backend-sop.md)** | Adding routes, models, schemas, CRUD, services, Celery tasks, DI, auth, storage, Redis, SSE |
| **[Frontend SOP](.claude/docs/sops/frontend-sop.md)** | Adding pages, dialogs, tables, hooks, API calls, SSE, file upload, theming, components |
| **[Infrastructure SOP](.claude/docs/sops/infrastructure-sop.md)** | Setting up monorepo, Docker, CI/CD, Alembic, env vars, git workflow |
| **[Claude Agent SOP](.claude/docs/sops/claude-agent-sop.md)** | Starting any task — mandatory workflow, checklists, anti-patterns, file naming |
| **[Design Patterns SOP](.claude/docs/sops/design-patterns-sop.md)** | Choosing architecture: Facade, Strategy, Builder, Factory, Observer, Adapter, Template Method, Command |
| **[Refactoring SOP](.claude/docs/sops/refactoring-sop.md)** | Cleaning up code: extracting methods/classes, simplifying conditionals, organizing data, React-specific refactoring |

### When to read which SOP

- **Building a new feature end-to-end:** Claude Agent SOP (workflow) → Backend SOP (API layer) → Frontend SOP (UI layer)
- **Adding a new domain/entity:** Backend SOP §2-8 (model → schema → crud → route → migration)
- **Choosing between patterns:** Design Patterns SOP cheat sheet (bottom of file)
- **Code review / cleanup:** Refactoring SOP decision tree (bottom of file)
- **New project from template:** Infrastructure SOP + Claude Agent SOP §2 (init checklist)
- **Swapping an external provider:** Design Patterns SOP §2 (Strategy pattern)

## Git

Conventional Commits. Branch: `hyp-123-short-description`. PR flow: branch → `dev` → `main`.

## Commands

```bash
pnpm dev                    # Start all apps
pnpm build                  # Build everything
pnpm lint / pnpm test       # Lint / test all
pnpm db:migrate             # Run DB migrations
pnpm run generate-api       # Regenerate API client
poetry run pytest           # Backend tests only
```
