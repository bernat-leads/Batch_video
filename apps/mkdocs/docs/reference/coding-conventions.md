# Coding Conventions

> Standard operating procedures for writing code in this project. Follow these exactly.

---

## Golden Rules

1. **No inline styles** — use Tailwind utility classes mapped to CSS custom properties via `@theme`
2. **No custom SVGs** — use `lucide-react` for icons, `recharts` for charts
3. **No hardcoded API calls** — use Orval-generated hooks and query keys from `@packages/api-client`
4. **No hand-written migrations** — always `alembic revision --autogenerate`
5. **Use enums** — Python `str, enum.Enum` for status fields, Orval generates TS const objects
6. **Auth in route guards only** — no auth logic in QueryClient or axios interceptors

---

## File Naming

| Layer | Convention | Example |
|-------|-----------|---------|
| Route files | kebab-case | `login.tsx`, `$batchId.tsx` |
| Components | kebab-case | `status-badge.tsx`, `batch-header.tsx` |
| Route-local components | `_components/` folder next to route | `routes/app/batches/_components/` |
| Shared components | `src/components/` | `components/ui/`, `components/layout/` |
| Hooks | `use-` prefix, kebab-case | `use-delete-video.ts` |
| Lib/utils | kebab-case | `query-client.ts`, `batch-status.ts` |
| Backend modules | snake_case directories | `videos/`, `settings_module/` |
| Backend files | snake_case | `crud.py`, `schemas.py` |
| Tests | `test_` prefix (Python), `.spec.ts` (Playwright) | `test_videos.py`, `smoke.spec.ts` |

---

## Frontend Code Standards

### TypeScript

- **Strict mode** — no `any` unless absolutely necessary
- **Orval-generated hooks** for all API calls — never `fetch`/`axios`
- **Orval query keys** for cache invalidation — `getListVideosApiV1VideosGetQueryKey()`
- **Zod + `satisfies z.ZodType<T>`** to tie schemas to generated types
- **t3-env** for env vars — `import.meta.env` only, never `process.env`
- **No `console.log`** in production code

### Styling

- **Tailwind utility classes only** — no `style={{}}` props
- CSS custom properties are mapped in `global.css` `@theme` block → available as Tailwind classes:
  - `text-text-primary`, `bg-card-bg`, `border-border`, `bg-brand`, `text-status-error`, etc.
- **Exception**: Runtime-computed values like `style={{ width: \`\${percent}%\` }}` for progress bars
- **Icons**: Always `lucide-react` — import individually: `import { Film } from "lucide-react"`
- **Charts**: Always `recharts` — `AreaChart`, `RadialBarChart`, etc.

### Component Organization

| Question | Answer |
|----------|--------|
| Used by only one route? | Put in `routes/<route>/_components/` |
| Used by multiple routes? | Put in `src/components/<feature>/` |
| Generic UI primitive? | Import from `@packages/ui/components/shadcn/*` |
| Custom reusable UI? | Put in `src/components/ui/` |

### Import Order

```tsx
// 1. React / third-party
import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";

// 2. Generated API client
import { useListVideosApiV1VideosGet } from "@packages/api-client";
import type { VideoRead } from "@packages/api-client";

// 3. UI primitives from shared package
import { Button } from "@packages/ui/components/shadcn/button";

// 4. App components and utilities
import { PageHeader } from "@/components/layout/page-header";
import { formatDuration } from "@/lib/format";
```

### Data Fetching

| Need | Use |
|------|-----|
| Read data | Orval `useXxxGet()` hook |
| Mutate data | Orval `useXxxPost/Put/Patch/Delete()` hook |
| Cache invalidation | `queryClient.invalidateQueries({ queryKey: getXxxQueryKey() })` |
| Route guard API call | Direct Orval function (not hook): `meApiV1AuthMeGet()` |

### Mutation Pattern

```tsx
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const queryClient = useQueryClient();
const mutation = useCreateVideoApiV1VideosPost({
  mutation: {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
      toast.success("Video created");
    },
    onError: () => toast.error("Failed to create video"),
  },
});
```

### Toast Notifications

- **Mutation success/error** → `toast.success()` / `toast.error()` from `sonner`
- **Form validation** → inline `<FormMessage />` (React Hook Form)
- **Auth errors** → redirect to `/login` via route `beforeLoad` guard
- **Never**: custom colored spans for status text

---

## Backend Code Standards

### Python

- **Type hints** on all function signatures — parameters and return types
- **Async everything** — all DB ops, all endpoints, all service methods
- **Pydantic schemas** for all request/response — never return raw dicts from endpoints
- **`str, enum.Enum`** for status fields — defined in `enums.py`, used in models and schemas
- **No sync wrappers** — native `async`/`await` (except Celery tasks bridging with `asyncio.run()`)

### Enums

```python
# api/videos/enums.py
class VideoStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class VideoStage(str, enum.Enum):
    queued = "queued"
    tts = "tts"
    segmentation = "segmentation"
    image_generation = "image_generation"
    assembly = "assembly"
    upload = "upload"
    done = "done"
```

Use in models: `status: Mapped[VideoStatus] = mapped_column(String(20), default=VideoStatus.pending)`
Use in schemas: `status: VideoStatus` (Pydantic auto-validates)
Use in queries: `Video.status == VideoStatus.completed` (never string literals)

### Module Structure

```
module_name/
├── __init__.py
├── enums.py            # str enums for status fields
├── routes.py           # Thin FastAPI router (delegates to crud)
├── models/             # SQLAlchemy models
│   ├── __init__.py
│   └── model_name.py
├── schemas.py          # Pydantic request/response schemas
└── crud.py             # CRUD classes extending BaseCrud + typed deps
```

### Dependency Injection

```python
# Define: XyzDep = Annotated[Xyz, Depends()]
VideoCrudDep = Annotated[VideoCrud, Depends()]

# Use in handlers — FastAPI auto-resolves
@router.get("/{video_id}")
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep, _auth: AuthDep):
    ...
```

---

## SOP: Add a New Backend Module

1. Create module directory: `apps/api/api/{module_name}/`
2. Define enums in `enums.py` (if status fields needed)
3. Create SQLAlchemy model in `models/`
4. Define Pydantic schemas in `schemas.py`
5. Write CRUD class in `crud.py` (extend `BaseCrud`, create typed dep)
6. Create router in `routes.py`
7. Register router in `apps/api/api/app.py`
8. Import model in `migrations/env.py`
9. Generate migration: `cd apps/api && poetry run alembic revision --autogenerate -m "description"`
10. Apply migration: `poetry run alembic upgrade head`
11. Regenerate frontend client: `pnpm run generate-api`

---

## SOP: Add a New Frontend Page

1. Create route file in `src/routes/` (TanStack Router auto-discovers)
2. Create `_components/` folder next to the route for page-specific components
3. Use Orval hooks for data fetching
4. Use `PageHeader` for consistent page titles
5. Add loading skeleton and empty state
6. Regenerate route tree: `npx @tanstack/router-cli generate`

---

## Git

### Branching

- `main` → production | `dev` → integration
- Task branches: `hyp-123-short-description` (Linear issue ID)
- PR flow: task branch → `dev` → `main`

### Commits (Conventional Commits)

Format: `<type>(<scope>): <description>`

| Type | When | Version Bump |
|------|------|-------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `refactor` | Code change, no feature/fix | — |
| `chore` | Build, tooling, deps | — |
| `test` | Tests | — |
| `docs` | Documentation | — |

Scopes: `api`, `ui`, `auth`, `worker`, `db`, `deps`, `infra`, `dashboard`

---

## SOP: Refactor / Audit Code Quality

Use the `/refactor` skill (`.claude/skills/refactor/`) to audit and fix code quality.

```
/refactor frontend     # Only apps/react/src/
/refactor backend      # Only apps/api/api/
/refactor all          # Both
/refactor <path>       # Specific file or directory
```

Rules are defined in `.claude/skills/refactor/references/rules.md` (25 rules):
- **F-01–F-15**: Frontend (import order, unused imports, named exports, theme tokens, inline styles, card pattern, icons, API calls, mutations, loading/empty states, section headers, delete confirmation, disabled states, no console.log)
- **B-01–B-10**: Backend (type hints, async, Pydantic schemas, enum usage, dependency injection, route ordering, module structure, no secrets, migration defaults, schema naming)
- **S-01–S-04**: Shared (no dead code, consistent naming, TODOs with context, UI label consistency)

---

## SOP: Destructive Actions

All delete/destructive buttons must use `ConfirmDeleteDialog`:

1. Import `ConfirmDeleteDialog` from `@/components/ui/confirm-delete-dialog`
2. Wrap the trigger button as a child
3. Provide `title`, `description`, and `onConfirm` handler
4. For dropdown menus: add `onSelect={(e) => e.preventDefault()}` on the `DropdownMenuItem` to keep the dialog open

---

## UI Label Mapping

| Backend Field | UI Label |
|--------------|----------|
| `generation_time_ms` | "Video Length" |
| `tokens_used` | "Tokens" |
| `total_cost_usd` | "Cost" |
| `avg_cost_per_shot_usd` | "Cost" (in per-shot context) |
| `file_size_bytes` | "File Size" |
| `current_stage` | Pipeline stage names |
| `created_at` | "Created" |

---

## Key Commands

```bash
pnpm dev                    # Start all apps
pnpm build                  # Build everything
pnpm lint                   # Lint all packages
pnpm run generate-api       # Regenerate API client from OpenAPI spec
poetry run start            # Start FastAPI only
poetry run pytest           # Backend tests
poetry run alembic revision --autogenerate -m "msg"  # Generate migration
poetry run alembic upgrade head                       # Apply migrations
```
