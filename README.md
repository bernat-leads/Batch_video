# Internal Tool Template

A monorepo template for internal tools with a React SPA frontend and FastAPI backend. Built on the [monorepo-base-template](https://github.com/Hyperion-AI-Agency/monorepo-base-template).

## Key Features

- **React + Vite** with TanStack Router (file-based routing)
- **FastAPI** backend with CRUD examples
- **Celery** background workers (optional)
- **Single PostgreSQL** database
- **Docker + Traefik** deployment

## Getting Started

1. **Use this template** — Click "Use this template" on GitHub
2. **Clone** — `git clone <your-repo-url>`
3. **Install** — `pnpm install && cd apps/api && poetry install`
4. **Environment** — Copy `.env.example` to `.env`
5. **Infrastructure** — `docker compose -f docker-compose.local.yml up -d`
6. **Migrate** — `pnpm db:migrate`
7. **Develop** — `pnpm dev`

## Architecture

```
apps/
├── react/        # React + Vite + TanStack Router
├── api/          # FastAPI + Celery
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

## Syncing with Base Template

1. `git remote add base https://github.com/Hyperion-AI-Agency/monorepo-base-template.git`
2. `git fetch base main`
3. `git merge base/main --allow-unrelated-histories`
4. Resolve conflicts and commit
