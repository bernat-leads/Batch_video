# CLAUDE.md — Lead Alliances Bulk Video Pipeline

This file is automatically loaded at the start of every Claude Code session.

---

## What This Is

**Bulk video pipeline for Lead Alliances** — a web app that mass-produces short-form video ads (TikTok/Reels/Shorts) from Excel scripts. A marketing team uploads an Excel file with 10-100 ad scripts, and the system processes each through a multi-step API pipeline to output finished 9:16 MP4 videos with AI-generated visuals, voiceover, and burned-in captions.

### Video Pipeline

1. **ElevenLabs TTS** — Convert script to voiceover audio with word-level timestamps
2. **Claude Segmentation** (claude-sonnet-4-6) — Chunk script into 5-8s segments, generate image prompts + Ken Burns directions
3. **Gemini Imagen 3** — Generate 1080x1920 images per segment in parallel
4. **Remotion Assembly** — Compose video with Ken Burns effects, sync audio, burn in TikTok-style captions

### Tech Stack

- **Frontend:** React + Vite + TanStack Router + shadcn/ui
- **Backend:** Python + FastAPI
- **Queue:** Redis + Celery (4 parallel workers)
- **Storage:** Cloudflare R2
- **Video:** Remotion
- **Monorepo:** Turborepo + pnpm
- **Deployment:** Docker on VPS

## Mandatory Workflow

**Claude must NEVER jump straight to writing code for new tasks or features.** The workflow is always:

1. **`/prime`** → 2. **`/plan`** → 3. **Review** → 4. **`/implement`**

## Task Management (Linear MCP)

Tasks are managed in **Linear** via MCP server (configured in `.claude/.mcp.json`).
Project: **Lead Alliances - Bulk Video Pipeline** (team: Hyperion AI, lead: Vitalijus Alsauskas)
Timeline: 2026-03-13 → 2026-03-15

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
| Celery worker | `apps/api/worker/` (pipeline tasks) |
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
