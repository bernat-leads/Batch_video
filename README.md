# Lead Alliances -- Bulk Video Pipeline

Automated bulk video production pipeline for marketing teams.

Upload an Excel spreadsheet with 10--100 ad scripts, and the system produces finished 9:16 MP4 videos (TikTok / Reels / Shorts) with AI-generated visuals, voiceover, and burned-in captions.

<!-- screenshots -->

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TanStack Router, shadcn/ui (Radix + Tailwind) |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 |
| Object Storage | Cloudflare R2 (S3-compatible) |
| Video Assembly | Remotion (TypeScript) |
| TTS | ElevenLabs API |
| Script Analysis | Anthropic Claude (claude-sonnet-4-6) |
| Image Generation | Google Gemini Imagen 3 |
| API Client | Orval (auto-generated TypeScript) |
| Monorepo | Turborepo + pnpm workspaces |
| Reverse Proxy | Traefik 3.6 |
| Observability | Sentry, PostHog |
| Deployment | Docker on VPS |

## Architecture

```mermaid
graph LR
    Browser["Browser"]
    React["React SPA<br/>(Vite + TanStack Router)"]
    FastAPI["FastAPI<br/>(Python 3.12)"]
    Celery["Celery Workers"]
    DB[("PostgreSQL")]
    Redis[("Redis")]
    R2[("Cloudflare R2")]
    ElevenLabs["ElevenLabs"]
    Claude["Claude API"]
    Gemini["Gemini Imagen 3"]

    Browser -->|HTTP| React
    React -->|REST API| FastAPI
    FastAPI --> DB
    FastAPI -->|dispatch jobs| Celery
    Celery -->|broker| Redis
    Celery --> DB
    Celery -->|TTS| ElevenLabs
    Celery -->|segmentation| Claude
    Celery -->|image gen| Gemini
    Celery -->|store artifacts| R2
    React -->|poll status| FastAPI
    FastAPI -->|presigned URLs| R2
```

### Video Pipeline Flow

Each script row goes through four sequential stages, with videos processed in parallel across Celery workers:

```
Script Text --> ElevenLabs TTS --> Claude Segmentation --> Gemini Imagen 3 --> Remotion Assembly --> Upload to R2
```

1. **TTS (ElevenLabs)** -- Convert script text to voiceover audio with word-level timestamps
2. **Segmentation (Claude)** -- Split script into 5--8 second visual segments, generate image prompts and Ken Burns camera directions
3. **Image Generation (Gemini Imagen 3)** -- Generate 1080x1920 portrait images per segment (parallel within a video)
4. **Assembly (Remotion)** -- Compose final 9:16 MP4 with Ken Burns pan/zoom effects, synced audio, and TikTok-style burned-in captions

Output: 1080x1920 H.264 MP4

## Quick Start

### Prerequisites

- Node.js >= 20.0.0
- Python >= 3.11, < 3.13
- pnpm 10+
- Poetry
- Docker and Docker Compose

### 1. Clone the repository

```bash
git clone git@github.com:Hyperion-AI-Agency/lead-alliances-video-pipeline.git
cd lead-alliances-video-pipeline
```

### 2. Install dependencies

```bash
pnpm install
cd apps/api && poetry install && cd ../..
```

### 3. Set up environment variables

```bash
cp apps/api/.env.example apps/api/.env
```

Edit `apps/api/.env` and fill in the required values: `API_SECRET_KEY`, `API_APP_PASSWORD`, and API keys for ElevenLabs, Anthropic, Gemini, and Cloudflare R2.

### 4. Start local infrastructure

```bash
docker compose -f docker-compose.local.yml up -d
```

This starts PostgreSQL, Redis, Traefik (reverse proxy), Flower (Celery monitoring), and Mailcatcher.

### 5. Run database migrations

```bash
pnpm db:migrate
```

### 6. Start development servers

```bash
pnpm dev
```

### 7. Open in browser

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Flower (Celery) | http://localhost:5555 |
| Traefik Dashboard | http://localhost:8090 |
| Mailcatcher | http://localhost:1080 |

## Project Structure

```
lead-alliances-video-pipeline/
├── apps/
│   ├── react/                  # React SPA (Vite + TanStack Router)
│   │   └── src/
│   │       ├── routes/         # File-based routes
│   │       ├── components/     # Shared React components
│   │       └── lib/            # Utilities, API client setup
│   ├── api/                    # FastAPI backend (Python 3.12)
│   │   ├── api/                # Application code
│   │   │   ├── core/           # Base models, CRUD, health routes
│   │   │   ├── videos/         # Video domain (models, routes, pipeline)
│   │   │   ├── batches/        # Batch domain
│   │   │   └── deps/           # Dependencies (DB, storage, Celery, Redis)
│   │   ├── __tests__/          # pytest test suite
│   │   └── migrations/         # Alembic database migrations
│   └── mkdocs/                 # Developer documentation (MkDocs Material)
├── packages/
│   ├── ui/                     # Shared shadcn/ui component library
│   ├── api-client/             # Generated TypeScript API client (Orval)
│   ├── analytics/              # PostHog analytics wrapper
│   ├── sentry/                 # Shared Sentry configuration
│   └── email/                  # Email utilities
└── tooling/
    ├── typescript-config/      # Shared TypeScript config
    ├── eslint-config/          # Shared ESLint config
    └── prettier-config/        # Shared Prettier config
```

## Available Commands

### Root (pnpm)

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all apps in development mode |
| `pnpm build` | Build all apps and packages |
| `pnpm lint` | Run linters across all workspaces |
| `pnpm test` | Run tests across all workspaces |
| `pnpm db:generate` | Generate a new Alembic migration (autogenerate) |
| `pnpm db:migrate` | Run pending database migrations |
| `pnpm run generate-api` | Regenerate the TypeScript API client from OpenAPI spec |
| `pnpm clean` | Remove all node_modules directories |

### Backend (Poetry)

Run from `apps/api/`:

| Command | Description |
|---------|-------------|
| `poetry run start` | Start the FastAPI server |
| `poetry run dev` | Start the FastAPI server in dev mode (with reload) |
| `poetry run celery-worker` | Start a Celery worker |
| `poetry run pytest` | Run backend tests |
| `poetry run preview-video` | Preview a video locally |

## Environment Variables

All backend environment variables use the `API_` prefix. Set them in `apps/api/.env`.

### Required

| Variable | Description |
|----------|-------------|
| `API_SECRET_KEY` | Secret key for session signing |
| `API_APP_PASSWORD` | Shared team login password |
| `API_ELEVENLABS_API_KEY` | ElevenLabs API key for text-to-speech |
| `API_ANTHROPIC_API_KEY` | Anthropic API key for Claude segmentation |
| `API_GEMINI_API_KEY` | Google Gemini API key for image generation |
| `API_OPENAI_API_KEY` | OpenAI API key |
| `API_S3_ENDPOINT` | Cloudflare R2 endpoint URL |
| `API_S3_ACCESS_KEY_ID` | R2 access key ID |
| `API_S3_SECRET_ACCESS_KEY` | R2 secret access key |
| `API_S3_BUCKET_NAME` | R2 bucket name |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `API_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/api` | PostgreSQL connection string |
| `API_ENVIRONMENT` | `local` | Environment: `local`, `staging`, or `production` |
| `API_SERVER_HOST` | `0.0.0.0` | Server bind host |
| `API_SERVER_PORT` | `8000` | Server bind port |
| `API_SERVER_LOG_LEVEL` | `info` | Uvicorn log level |
| `API_SWAGGER_HIDE` | `false` | Hide Swagger docs (set `true` in production) |
| `API_S3_REGION` | `us-east-1` | S3/R2 region |
| `API_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `API_SESSION_MAX_AGE` | `604800` | Session cookie max age in seconds (7 days) |
| `API_CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis URL for Celery broker |
| `API_CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis URL for Celery results |
| `API_CELERY_TASK_TIME_LIMIT` | `1800` | Hard time limit per task (seconds) |
| `API_CELERY_TASK_SOFT_TIME_LIMIT` | `1500` | Soft time limit per task (seconds) |
| `API_PIPELINE_MAX_RETRIES` | `5` | Max retries per pipeline stage |
| `API_PIPELINE_RETRY_WAIT_SECONDS` | `2` | Base wait between retries (seconds) |
| `API_GEMINI_RATE_LIMIT` | `10` | Gemini requests per minute (0 = unlimited) |
| `API_OPENAI_RATE_LIMIT` | `0` | OpenAI requests per minute (0 = unlimited) |
| `API_ELEVENLABS_CONCURRENCY_LIMIT` | `3` | Max concurrent ElevenLabs requests |
| `API_UPLOAD_MAX_FILE_SIZE` | `10485760` | Max upload file size in bytes (10 MB) |
| `API_UPLOAD_ALLOWED_EXTENSIONS` | `[".xlsx", ".xls", ".csv"]` | Allowed upload file extensions |
| `API_FONT_DIR` | `fonts` | Directory for font files |
| `API_SENTRY_DSN` | _(none)_ | Sentry DSN for error tracking |
| `API_SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Sentry performance tracing sample rate |
| `API_SENTRY_PROFILES_SAMPLE_RATE` | `0.1` | Sentry profiling sample rate |

## Deployment

Production uses Docker Compose with Traefik for HTTPS (Let's Encrypt) and reverse proxying.

### Production services

| Service | Description |
|---------|-------------|
| `traefik` | Reverse proxy with automatic TLS certificates |
| `api` | FastAPI backend container |
| `celery-worker` | Celery background worker container |
| `app` | React frontend served via nginx |

### Deploy

```bash
# Set production environment variables
cp .env.example .env  # Edit with production values

# Build and start
docker compose -f docker-compose.prod.yml up -d --build
```

### Required production environment variables

In addition to the `API_` variables above, production requires:

| Variable | Description |
|----------|-------------|
| `DOMAIN` | Primary domain (e.g., `app.example.com`) |
| `ACME_EMAIL` | Email for Let's Encrypt certificate registration |
| `TRAEFIK_DASHBOARD_AUTH` | Basic auth credentials for Traefik dashboard |

Traefik routes traffic as follows:
- `${DOMAIN}` -- React frontend
- `api.${DOMAIN}` -- FastAPI backend
- `traefik.${DOMAIN}` -- Traefik dashboard (password-protected)

## Contributing

### Git Workflow

1. Create a branch from `dev`: `git checkout -b hyp-123-short-description`
2. Make changes following conventional commits (e.g., `feat:`, `fix:`, `chore:`)
3. Open a PR targeting `dev`
4. After review and merge to `dev`, changes are promoted to `main` for release

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add batch ZIP export
fix: correct video duration calculation
chore: update dependencies
```

### Code Standards

- **TypeScript:** Strict mode, no `any` types
- **Python:** Ruff linting, mypy strict mode, no `Any` type annotations
- **Tests:** TDD -- write tests before implementation
- **Migrations:** Always use `alembic revision --autogenerate`, never hand-write migrations

## License

Proprietary. All rights reserved.
