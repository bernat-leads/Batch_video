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
