# Lead Alliances - Bulk Video Pipeline

Automated bulk video pipeline for marketing teams. Upload an Excel spreadsheet with 10-100 ad scripts, and the system produces finished 9:16 MP4 videos (TikTok/Reels/Shorts) with AI-generated visuals, voiceover, and captions.

## Pipeline

```
Excel Upload → ElevenLabs TTS → Claude Segmentation → Gemini Imagen 3 → Remotion Assembly → MP4 Output
```

1. **Upload** — Excel file with ad scripts (10-100 rows)
2. **TTS** — ElevenLabs generates voiceover for each script
3. **Segmentation** — Claude splits scripts into visual scenes
4. **Image Generation** — Gemini Imagen 3 creates scene visuals
5. **Assembly** — Remotion combines audio, images, and captions into 9:16 MP4
6. **Delivery** — Finished videos stored in Cloudflare R2

## Tech Stack

- **Frontend:** React + shadcn/ui (Vite + TanStack Router)
- **Backend:** Python + FastAPI
- **Queue:** Redis + Celery (4 parallel workers)
- **Video:** Remotion
- **Storage:** Cloudflare R2
- **Hosting:** VPS (Docker)
- **Monorepo:** Turborepo + pnpm

## Getting Started

1. **Clone** — `git clone git@github.com:Hyperion-AI-Agency/lead-alliances-video-pipeline.git`
2. **Install** — `pnpm install && cd apps/api && poetry install`
3. **Environment** — Copy `.env.example` to `.env` in `apps/react/` and `apps/api/`
4. **Infrastructure** — `docker compose -f docker-compose.local.yml up -d`
5. **Migrate** — `pnpm db:migrate`
6. **Develop** — `pnpm dev`

## Architecture

```
apps/
├── react/        # React + Vite + TanStack Router (upload UI, video preview)
├── api/          # FastAPI + Celery (pipeline orchestration)
├── storybook/    # Component documentation
├── email/        # Email template dev server
└── keycloak-theme/

packages/
├── ui/           # shadcn/ui components
├── analytics/    # PostHog
├── sentry/       # Error tracking
├── api-client/   # Generated API client
└── email/        # Email templates

tooling/
├── typescript-config/
├── prettier-config/
└── eslint-config/
```

## Project Management

- **Linear:** [Lead Alliances - Bulk Video Pipeline](https://linear.app/hyperion-ai/project/lead-alliances-bulk-video-pipeline-9e8153abaef0)
- **1Password:** Lead Alliances - Shared

## Syncing with Base Template

1. `git remote add base https://github.com/Hyperion-AI-Agency/monorepo-base-template.git`
2. `git fetch base main`
3. `git merge base/main --allow-unrelated-histories`
4. Resolve conflicts and commit
