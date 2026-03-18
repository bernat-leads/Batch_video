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
| **Gemini Imagen 4 Fast for images** | 1080x1920 portrait images at high quality. |
| **Per-stage artifact storage in R2** | Enables retry of individual stages without full pipeline re-run. |
| **LiteLLM for cost lookup** | Single source for model pricing across providers. Auto-updates when models change. No hardcoded cost constants. |
| **Per-model cost tracking** (not per-stage) | `model_costs` JSON column stores `{model: {token_count, cost_usd}}`. When models are swapped, costs automatically track the new model name — no schema migration needed. |
| **No summed token totals** | Each model has different usage units (tokens for Claude, characters for ElevenLabs, flat per-image for Imagen). Only `total_cost_usd` is aggregated — usage counts stay per-model. |
| **Usage from API responses** | Claude: `input_tokens` + `output_tokens` from response. ElevenLabs: character count from `alignment.characters`. Imagen: no usage data returned — API is flat per-image with no token/usage metadata. |
| **OpenAI TTS removed** | Dead code path — was never wired into the pipeline. ElevenLabs is the only TTS provider. |

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
| **`async_task` decorator for Celery** | Async tasks via `asgiref.AsyncToSync`. See [Async Celery Pattern](#async-celery-pattern) below. |
| **Separate Redis clients for FastAPI vs Celery** | FastAPI uses shared `async_pool` (one event loop). Celery uses `create_async_redis()` per task (fresh connection per event loop). |

## Async Celery Pattern

Celery workers are synchronous, but the backend is fully async (SQLAlchemy async, Redis async). The `async_task` decorator in `api/deps/celery.py` bridges this using `asgiref.AsyncToSync`.

### The decorator

```python
# api/deps/celery.py
from asgiref.sync import async_to_sync

def async_task(app: Celery, *args, **kwargs):
    def _decorator(func):
        sync_call = async_to_sync(func)

        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args, **kwargs):
            return sync_call(*args, **kwargs)

        return _decorated
    return _decorator
```

### Usage

```python
from api.deps.celery import async_task, celery_app

@async_task(celery_app, bind=True, max_retries=0)
async def process_video(self, video_input_data, batch_id=None):
    async with async_session_factory() as session:
        # fully async code here
        ...
```

### Redis client rules

`async_to_sync` creates a **new event loop per task invocation**. Module-level async connection pools bind to the loop they're first used on — if that loop closes, the pool is dead.

| Context | Use | Why |
|---------|-----|-----|
| **FastAPI** (SSE, deps) | `async_pool` via `get_async_redis()` | Single event loop for the app lifetime. Pool reuse is safe. |
| **Celery tasks** | `create_async_redis()` | Fresh client per call. No shared pool = no stale loop references. |

```python
# In a Celery task:
from api.deps.redis import create_async_redis

redis_client = create_async_redis()
try:
    # use redis_client
finally:
    await redis_client.aclose()
```

### Key constraint

**Never import `async_pool` in Celery tasks.** Always use `create_async_redis()`.

## Conventions

| Decision | Rationale |
|----------|-----------|
| **TypeScript strict mode** | Catch errors at compile time. No `any`. |
| **Conventional Commits** | Semantic versioning via semantic-release. |
| **TDD** | Tests before implementation. |
