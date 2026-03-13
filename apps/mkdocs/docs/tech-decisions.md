# Technical Decisions

> Decisions are final. Follow them — don't re-litigate. Update this file when new decisions are made.

---

## Architecture

| Decision | Rationale |
|----------|-----------|
| **Single PostgreSQL database** | Internal tool, not SaaS. All data in one place. |
| **Shared password auth** (no per-user accounts) | Small marketing team. `APP_PASSWORD` env var + cookie session. |
| **Celery for pipeline orchestration** | Sequential stages per video, parallel across videos. |
| **Cloudflare R2 for storage** | S3-compatible, no egress fees. Presigned URLs. 7-day lifecycle. |
| **Remotion for video assembly** | Programmatic video composition in TypeScript. Ken Burns + captions + audio sync. |
| **Orval for API client generation** | Type safety frontend↔backend. `pnpm run generate-api`. |

## Pipeline

| Decision | Rationale |
|----------|-----------|
| **ElevenLabs for TTS** | High-quality voices, word-level timestamps for caption sync. |
| **Claude for segmentation** | LLM understands narrative flow — visual breaks, image prompts, camera directions. |
| **Gemini Imagen 3 for images** | 1080x1920 portrait images at high quality. |
| **Per-stage artifact storage in R2** | Enables retry of individual stages without full pipeline re-run. |

## Frontend

| Decision | Rationale |
|----------|-----------|
| **React SPA + Vite** (not Next.js) | Internal tool — no SEO, no SSR needed. Fast dev with Vite. |
| **TanStack Router** | Type-safe file-based routing. |
| **shadcn/ui** (Radix + Tailwind) | Accessible, customizable. Shared via `packages/ui/`. |
| **Tailwind utility classes** with `@theme` token mapping | All styling via classes — no inline `style={{}}`. Theme tokens map CSS variables to Tailwind. |
| **lucide-react for ALL icons** | Never create custom SVG elements. |
| **recharts for ALL charts** | Never create custom SVG charts. |
| **Route-specific `_components/` folders** | Components used by one route live next to it. Shared components in `src/components/`. |
| **Framer Motion for route transitions** | `AnimatePresence` for proper exit animations. No CSS View Transitions API. |
| **sonner for toasts** (not shadcn wrapper) | shadcn's wrapper imports `next-themes` (unavailable in Vite). |
| **Polling** (not WebSockets) | `refetchInterval: 3000` is simpler. Video gen takes minutes — 3s polling isn't wasteful. |
| **No auth in QueryClient** | Auth handled by route `beforeLoad` guards only. QueryClient is plain. |
| **Batch status derived from video counts** | No `status` column on batches table. Computed via `deriveBatchStatus()`. |
| **Video `prompt` field** copied from master_prompt | Each video stores its own prompt at creation time from settings. |

## Backend

| Decision | Rationale |
|----------|-----------|
| **FastAPI + async SQLAlchemy** | Non-blocking I/O. All operations async. |
| **Module-per-domain structure** | Clear boundaries. `routes.py`, `models/`, `schemas.py`, `crud.py`, `enums.py`. |
| **Generic `BaseCrud` pattern** | DRY CRUD operations. Subclasses add custom queries. |
| **Typed deps** (`Annotated + Depends`) | Clean signatures, auto-resolved. |
| **Python `str, enum.Enum`** for status fields | Type safety in models, schemas, queries. Never string literals. Orval generates TS enums. |
| **Alembic autogenerate only** | Never hand-write migrations. `alembic revision --autogenerate`. |
| **Simple SQL aggregates** for stats (not materialized views) | Hundreds of rows, <5ms queries. Materialized views are overkill. |
| **Retry 3x with backoff** for pipeline stages | External APIs have transient failures. |

## Conventions

| Decision | Rationale |
|----------|-----------|
| **TypeScript strict mode** | Catch errors at compile time. No `any`. |
| **Conventional Commits** | Semantic versioning via semantic-release. |
| **TDD** | Tests before implementation. |
