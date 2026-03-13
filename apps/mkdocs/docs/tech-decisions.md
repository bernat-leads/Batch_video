# Technical Decisions

> Key architectural and technology choices made for this project, with rationale. Claude should follow these decisions — not re-litigate them — when planning new work.

---

## Architecture

### Single Database (not two)
- **Decision:** One PostgreSQL database for the FastAPI backend (SQLAlchemy async)
- **Rationale:** This is an internal tool, not a SaaS. No separate frontend DB needed — React is a pure SPA that talks to FastAPI. All data (batches, jobs, artifacts) lives in one place.

### Shared Password Auth (not per-user)
- **Decision:** Single password (`APP_PASSWORD` env var) protects the app. No individual accounts.
- **Rationale:** Small marketing team, internal tool. Shared password is simplest. Session via cookie/token after login.

### Celery for Pipeline Orchestration
- **Decision:** Celery task chains process each video sequentially; workers handle different videos in parallel
- **Rationale:** Each pipeline stage (TTS → segmentation → image gen → assembly) must run in order, but multiple videos can process simultaneously. Celery chains + worker pool is the natural fit.

### Cloudflare R2 for Storage
- **Decision:** All artifacts (audio, images, videos) stored in Cloudflare R2
- **Rationale:** S3-compatible, no egress fees. Videos served via presigned URLs. 7-day lifecycle auto-cleanup.

### Remotion for Video Assembly
- **Decision:** Remotion renders final MP4 videos with Ken Burns effects, synced audio, and burned-in captions
- **Rationale:** Programmatic video composition in TypeScript. Ken Burns pan/zoom on AI images, word-synced captions, audio overlay — all defined as React components rendered to MP4.

### Orval for API Client Generation
- **Decision:** Auto-generate TypeScript client from FastAPI's OpenAPI spec
- **Rationale:** Type safety between frontend and backend. Run `pnpm run generate-api` to regenerate.

---

## Pipeline

### ElevenLabs for TTS
- **Decision:** ElevenLabs API for text-to-speech with word-level timestamps
- **Rationale:** High-quality voices, word-level timing data needed for caption sync.

### Claude for Script Segmentation
- **Decision:** Claude claude-sonnet-4-6 segments scripts into 5-8s visual segments with image prompts and Ken Burns directions
- **Rationale:** LLM understands narrative flow — can decide where to break visually, what imagery fits each segment, and how the camera should move.

### Gemini Imagen 3 for Image Generation
- **Decision:** Google Gemini Imagen 3 generates 1080x1920 images per segment
- **Rationale:** High-quality image generation at the required portrait aspect ratio.

### Intermediate Artifact Storage
- **Decision:** Each pipeline stage stores its output in R2 before passing to the next stage
- **Rationale:** Enables retry of individual stages without re-running the whole pipeline. Failed stage can restart from last successful artifact.

---

## Frontend

### React SPA with Vite + TanStack Router (not Next.js)
- **Decision:** Client-side React SPA, not SSR
- **Rationale:** Internal tool — no SEO, no public pages. Vite for fast dev, TanStack Router for type-safe file-based routing.

### shadcn/ui for Components
- **Decision:** shadcn/ui (Radix + Tailwind) for all UI components
- **Rationale:** Accessible, customizable, consistent. Shared via `packages/ui/`.

### @tanstack/react-query for Server State
- **Decision:** react-query for API calls and polling
- **Rationale:** Built-in polling (`refetchInterval`) for real-time batch progress. Caching and invalidation for download URLs.

---

## Backend

### FastAPI with Async SQLAlchemy
- **Decision:** Async endpoints with asyncpg
- **Rationale:** Non-blocking I/O for concurrent requests. All DB operations use `async_session`.

### Module-per-domain Structure
- **Decision:** Each domain (batches, jobs, pipeline) has its own routes, models, schemas, and crud module
- **Rationale:** Clear boundaries. New features get their own module.

### Generic BaseCrud Pattern
- **Decision:** `BaseCrud[ModelType, CreateSchemaType, UpdateSchemaType]` generic base class
- **Rationale:** DRY CRUD operations. Subclasses inject model type and add custom queries.

### Typed Dependencies (Annotated + Depends)
- **Decision:** All dependencies use `XyzDep = Annotated[Xyz, Depends(Xyz)]` pattern
- **Rationale:** Clean function signatures, auto-resolved by FastAPI.

### Alembic for Migrations
- **Decision:** Alembic for database migrations
- **Rationale:** Version-controlled, reversible migrations auto-generated from SQLAlchemy model changes.

### Retry with Backoff
- **Decision:** Failed pipeline stages retry 3x before marking job as failed
- **Rationale:** External API calls (ElevenLabs, Claude, Gemini) can have transient failures. Retries avoid losing progress on temporary issues.

---

## Conventions

### TypeScript Strict Mode
- **Decision:** Strict TypeScript everywhere in frontend
- **Rationale:** Catch errors at compile time. No `any` types unless absolutely necessary.

### Conventional Commits
- **Decision:** All commits follow Conventional Commits format
- **Rationale:** Semantic versioning and changelog generation via semantic-release.

---

_Update this when new architectural decisions are made._
