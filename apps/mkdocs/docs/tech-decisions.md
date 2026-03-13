# Technical Decisions

> Key architectural and technology choices made for this project, with rationale. Claude should follow these decisions — not re-litigate them — when planning new work.

---

## Architecture

### Separate Frontend and Backend Databases
- **Decision:** Two PostgreSQL databases — one for Next.js/Payload, one for FastAPI
- **Rationale:** Clean separation of concerns. Frontend DB handles auth, CMS, and sessions. Backend DB handles domain models. Each uses its native ORM (Drizzle vs SQLAlchemy).

### Better Auth as OIDC Provider
- **Decision:** Better Auth handles all user-facing auth; FastAPI trusts it via OIDC/JWKS
- **Rationale:** Single source of truth for user identity. FastAPI doesn't manage users — it validates JWTs. This avoids auth duplication.

### LangGraph for Agent Orchestration
- **Decision:** LangGraph state machine with conversation + tools loop
- **Rationale:** The agent requires tool-calling (background task dispatch, web search, data fetching). LangGraph's graph model with `ToolNode` makes the conversation → tools → conversation loop clean and extensible.

### CopilotKit for Chat UI
- **Decision:** CopilotKit + AG-UI protocol for frontend-to-agent communication
- **Rationale:** Provides streaming, tool rendering, and state management out of the box. The agent endpoint follows the AG-UI spec for real-time response streaming.

### Orval for API Client Generation
- **Decision:** Auto-generate TypeScript client from FastAPI's OpenAPI spec
- **Rationale:** Type safety between frontend and backend. Changes to FastAPI schemas automatically propagate to frontend types. Run `pnpm run generate-api` to regenerate.

### Payload CMS for Content Management
- **Decision:** Payload CMS (embedded in Next.js) for all marketing/content pages
- **Rationale:** Provides admin UI, localization, block-based page building, media management, and live preview. All landing pages, blog posts, and site settings are CMS-managed.

### CMS-Driven Landing Pages with Block System
- **Decision:** Landing pages built from composable Payload blocks, rendered by `BlocksRenderer`
- **Rationale:** Non-developers can edit landing pages via Payload admin. Each block has a Payload schema (fields) and a React component (renderer). New block types are easy to add.

### Page Templates for Header/Footer
- **Decision:** Header and footer blocks stored in `page-templates` collection, rendered by public layout
- **Rationale:** Consistent site chrome across all public pages. Editable via CMS admin without code changes.

---

## Frontend

### Next.js App Router (not Pages Router)
- **Decision:** Use App Router with React Server Components
- **Rationale:** Better data fetching patterns, server actions, and layout nesting. All new pages should use App Router patterns.

### tRPC for Internal Queries
- **Decision:** tRPC for Next.js server-to-client communication
- **Rationale:** Type-safe API layer without code generation. Used for data that lives in the frontend DB.

### Server Actions for Mutations
- **Decision:** Use Next.js server actions for auth, subscriptions, and email
- **Rationale:** Collocated server logic, automatic form integration, no API route boilerplate.

### @tanstack/react-form for Forms
- **Decision:** Use @tanstack/react-form with Zod validators (not react-hook-form)
- **Rationale:** First-class TypeScript support, built-in Zod integration via `validators: { onChange: schema }`, field-level validation, and clean API with `form.Field` render props.

### @tanstack/react-query for Server State
- **Decision:** Use @tanstack/react-query for API calls and mutations (including orval-generated hooks)
- **Rationale:** Provides caching, invalidation, infinite queries, and mutation state management. Orval generates query hooks that use react-query under the hood.

### unstable_cache for CMS Data
- **Decision:** Use Next.js `unstable_cache` with tags and revalidation for CMS data fetching
- **Rationale:** ISR-like caching for Payload CMS queries. Tagged with collection names for targeted revalidation. 1-hour TTL default.

### DataProvider Context for Domain Pages
- **Decision:** Shared context provider wraps domain data pages
- **Rationale:** Domain data fetched once and shared across all related pages via React context. Avoids redundant API calls.

### SubscriptionGuard (Client-Side Redirect)
- **Decision:** Client component that redirects unsubscribed users to `/subscription`
- **Rationale:** Protected layout checks subscription server-side and passes `hasSubscription` prop. Guard handles client-side redirect with exemptions for settings/subscription pages.

---

## Backend

### FastAPI with Async SQLAlchemy
- **Decision:** Async endpoints with asyncpg
- **Rationale:** Non-blocking I/O for concurrent requests. All DB operations use `async_session`.

### Module-per-domain Structure
- **Decision:** Each domain has its own routes, models, schemas, and crud module
- **Rationale:** Clear boundaries. New features get their own module following this pattern.

### Generic BaseCrud Pattern
- **Decision:** `BaseCrud[ModelType, CreateSchemaType, UpdateSchemaType]` generic base class
- **Rationale:** DRY CRUD operations. Subclasses inject model type and add custom queries. All methods async.

### Typed Dependencies (Annotated + Depends)
- **Decision:** All dependencies use `XyzDep = Annotated[Xyz, Depends(Xyz)]` pattern
- **Rationale:** Clean function signatures, auto-resolved by FastAPI. Services, CRUD classes, auth, and DB sessions all use this pattern consistently.

### Service Layer for Complex Modules
- **Decision:** Service classes orchestrate multiple CRUD operations and external services
- **Rationale:** Routes stay thin (just HTTP concerns). Business logic lives in services. Services get dependencies injected via constructor.

### Alembic for Migrations
- **Decision:** Alembic (not raw SQL) for backend DB migrations
- **Rationale:** Version-controlled, reversible migrations. Auto-generated from SQLAlchemy model changes.

### API Module Structure (Flat Top-Level Packages)
- **Decision:** Split into `api/` (HTTP), `agents/` (LangGraph), and `worker/` (Celery) as separate top-level packages
- **Rationale:** Clean separation of concerns. Each is a distinct runtime. Shared via imports, separate entry points via Poetry scripts.

### Langfuse for Tracing (Prompts Are Local)
- **Decision:** Langfuse is used for LLM tracing and observability. Prompts are **local Python constants** in `agents/prompts/` (not fetched from Langfuse cloud).
- **Rationale:** Local prompts give better version control, code review, and IDE support. Langfuse cloud prompt management added latency and made prompt changes harder to track in git. Tracing remains in Langfuse for cost/latency monitoring.

### Celery for Background Processing
- **Decision:** Celery + Redis for async background task processing
- **Rationale:** Long-running tasks are too slow for synchronous response. Background processing with tool-triggered dispatch keeps the agent responsive.

### Sentry for Error Tracking
- **Decision:** Sentry SDK on both frontend (client/server/edge) and backend (FastAPI/SQLAlchemy/Celery)
- **Rationale:** Production visibility into errors and performance. Optional via DSN — no-op when unconfigured.

### PostHog for Product Analytics
- **Decision:** PostHog via `@packages/analytics` shared package, proxied through Next.js rewrites
- **Rationale:** First-party analytics proxy avoids ad blockers. Centralized event constants ensure consistency.

---

## Conventions

### TypeScript Strict Mode
- **Decision:** Strict TypeScript everywhere in frontend
- **Rationale:** Catch errors at compile time. No `any` types unless absolutely necessary.

### Biome for Linting
- **Decision:** Biome (not ESLint alone) for fast linting and formatting
- **Rationale:** Faster than ESLint, handles both linting and formatting. See `biome.json` at root.

---

_Update this when new architectural decisions are made._
