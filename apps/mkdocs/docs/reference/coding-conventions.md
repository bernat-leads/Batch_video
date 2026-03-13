# Coding Conventions

## Test-Driven Development (TDD)

**We follow TDD — tests are written before implementation code.** This is a core principle, not a suggestion.

### The TDD Cycle

```mermaid
graph LR
    R["RED<br/>Write a failing test"] --> G["GREEN<br/>Write minimal code to pass"]
    G --> RF["REFACTOR<br/>Clean up, maintain tests"]
    RF --> R
```

### When to apply TDD

| Scenario | Approach |
|----------|----------|
| New backend endpoint | Write pytest test for the route first |
| New CRUD operation | Write pytest test for the DB operation first |
| New agent tool | Write test for expected state transitions first |
| New React component | Write E2E test for expected behavior first |
| New page/flow | Write Playwright test for the user journey first |
| Bug fix | Write a test that reproduces the bug, then fix it |

### Backend Testing (pytest)

```python
# apps/api/__tests__/items/test_items.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_item_returns_200(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/api/v1/items/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

**Test location:** `apps/api/__tests__/`
**Run:** `poetry run pytest` | **Single file:** `poetry run pytest __tests__/items/test_items.py` | **Verbose:** `poetry run pytest -v -s`

### E2E Testing (Playwright)

```typescript
// e2e/dashboard/navigation.spec.ts
import { test, expect } from '@playwright/test';

test('user can navigate to dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
});
```

**Test location:** `e2e/` | **Run:** `pnpm test:e2e` | **Debug:** `pnpm test:e2e:debug`

### Playwright Test Projects

| Project | Directory | Auth State |
|---------|-----------|-----------|
| `setup` | — | Generates storage state from UI sign-in |
| `unauthenticated` | `e2e/auth/` | No auth |
| `authenticated` | `e2e/dashboard/` | Uses stored auth session |
| `api` | `e2e/api/` | Direct FastAPI calls (baseURL: localhost:8000) |

---

## Coding Standards

### TypeScript (Frontend)

- **Strict mode** everywhere — no `any` unless absolutely necessary
- **Zod** for runtime validation at system boundaries (env vars, form data)
- **Orval-generated hooks** for all API calls — never write raw `fetch`/`axios` to the backend
- **React Hook Form + Zod + shadcn Form** for all forms — use `satisfies z.ZodType<T>` to tie Zod schemas to generated types
- **t3-env** for environment variables — `import.meta.env` only, never `process.env`
- **No `console.log`** in production code — use proper error boundaries and Sentry

### Python (Backend)

- **Type hints** on all function signatures — parameters and return types
- **Async everything** — all DB operations, all endpoint handlers, all service methods
- **Pydantic** for all request/response schemas — never return raw dicts from endpoints
- **No sync wrappers** — use native `async`/`await`, not `asyncio.run()` (except in Celery tasks which bridge async/sync)

### Formatting & Linting

| Tool | Scope | Config |
|------|-------|--------|
| Biome | JS/TS linting + formatting | `biome.json` (root) |
| Prettier | Import sorting, Tailwind class sorting | `prettier.config.js` (root) |
| Ruff/Black | Python formatting | `pyproject.toml` (apps/api) |

---

## File Naming

| Layer | Convention | Example |
|-------|-----------|---------|
| Frontend routes | kebab-case | `login.tsx`, `about.tsx` |
| Frontend components | kebab-case files | `logout-button.tsx` |
| Frontend lib/utils | kebab-case | `query-client.ts`, `auth.ts` |
| Backend modules | snake_case directories | `items/` |
| Backend files | snake_case | `item_service.py` |
| Backend tests | `test_` prefix | `test_items.py` |
| Seed scripts | `seed-` prefix | `seed-landing.ts` |
| Shared packages | kebab-case | `packages/ui/` |
| E2E tests | kebab-case with `.spec.ts` | `navigation.spec.ts` |

---

## Frontend Patterns

### Component Decision Tree

| Question | Answer |
|----------|--------|
| Is it a generic UI primitive (button, card, dialog)? | Import from `@packages/ui/components/shadcn/*` |
| Is it app-specific? | Create in `src/components/{feature}/` or `src/components/{name}.tsx` |
| Does it need its own file? | Yes — one component per file, extract early |

### Import Conventions

```tsx
// 1. UI primitives from shared package
import { Button } from "@packages/ui/components/shadcn/button"
import { Card } from "@packages/ui/components/shadcn/card"

// 2. Generated API client (never hand-write fetch to FastAPI)
import { useLoginApiV1AuthLoginPost } from "@packages/api-client"
import type { LoginRequest } from "@packages/api-client"

// 3. App utilities via path alias
import { requireAuth } from "@/lib/auth"
import { env } from "@/env"

// 4. Tailwind: use utility classes, follow design system tokens
```

### Data Fetching

| Source | Method | When to Use |
|--------|--------|-------------|
| Backend API | Orval-generated hooks (`@packages/api-client`) | All FastAPI endpoints |
| Auth | `meApiV1AuthMeGet()` function in route guards | Session validation |

### Toast Notifications

Use `sonner` (imported directly, not shadcn's wrapper) for mutation feedback:

```tsx
import { toast } from "sonner";

// In mutation config
onSuccess: () => toast.success("Settings saved"),
onError: () => toast.error("Failed to save settings"),
```

- Form field validation errors → inline `<FormMessage />`, NOT toast
- Auth errors → redirect to `/login`, NOT toast
- Success/error from API mutations → always toast

### UI Styling Conventions

See [Web Dashboard Reference → UI Component Styling Patterns](web-dashboard.md#ui-component-styling-patterns) for:
- Color application rules (which variable for which element)
- Card, input, button, progress bar patterns
- Loading states, empty states, animations
- Sidebar theme mapping

### Form Pattern (React Hook Form + Zod + shadcn)

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Form, FormField, FormControl, FormItem, FormLabel, FormMessage } from "@packages/ui/components/shadcn/form";

// Tie Zod schema to Orval-generated type with `satisfies`
const schema = z.object({
  password: z.string().min(1, "Required"),
}) satisfies z.ZodType<LoginRequest>;

export function MyForm() {
  const form = useForm<LoginRequest>({
    resolver: zodResolver(schema),
    defaultValues: { password: "" },
  });

  const mutation = useLoginApiV1AuthLoginPost({
    mutation: {
      onSuccess: () => navigate({ to: "/" }),
      onError: () => form.setError("password", { message: "Invalid" }),
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((v) => mutation.mutate({ data: v }))}>
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </form>
    </Form>
  );
}
```

---

## Backend Patterns

### Module Structure (every domain follows this)

```
module_name/
├── routes.py           # Thin FastAPI router (delegates to service/crud)
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic request/response models
├── crud/               # Database operations (class-based, extending BaseCrud)
├── service.py          # Business logic (optional)
└── __init__.py
```

### Typed Dependency Injection

```python
# Define: XyzDep = Annotated[Xyz, Depends()]
SessionDep = Annotated[AsyncSession, Depends(get_db)]
VideoCrudDep = Annotated[VideoCrud, Depends()]
StorageDep = Annotated[StorageService, Depends(get_storage)]

# Use in route handlers — FastAPI auto-resolves the dependency chain
@router.get("/{video_id}")
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep):
    video = await crud.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
```

### Adding a New Backend Module

1. Write tests first (`apps/api/__tests__/{module}/`)
2. Create module directory under `apps/api/api/`
3. Define SQLAlchemy model in `models/`
4. Define Pydantic schemas in `schemas.py`
5. Write CRUD class in `crud.py` (extend `BaseCrud`)
6. Create router in `routes.py`
7. Register router in `apps/api/api/app.py`
8. Import model in `migrations/env.py`
9. Create Alembic migration: `poetry run alembic revision --autogenerate -m "description"`
10. Regenerate frontend client: `pnpm run generate-api`

---

## Git

### Branching

- `main` — production, protected
- `dev` — integration branch
- **Every task gets its own branch** named after the Linear issue:
    - `hyp-123-add-user-search` — feature task
    - `hyp-456-fix-login-redirect` — bug fix task
    - `hyp-789-update-dependencies` — maintenance task
- Branch naming format: `<linear-issue-id>-<short-kebab-description>` (all lowercase, no username prefix)
- PR workflow: task branch → `dev` → `main`

### Commit Messages (Conventional Commits + Semantic Release)

All commit messages **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This is enforced by semantic-release for automated versioning and changelog generation.

**Format:** `<type>(<optional scope>): <description>`

**For breaking changes**, add `!` after the type/scope:
`feat(api)!: change authentication flow` or include `BREAKING CHANGE:` in the commit body.

| Type | When to use | Version Bump |
|------|------------|-------|
| `feat` | New feature or capability | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | — |
| `style` | Formatting, no logic change | — |
| `refactor` | Code change, no feature/fix | — |
| `perf` | Performance improvement | PATCH |
| `test` | Adding/updating tests | — |
| `chore` | Build, tooling, deps, config | — |
| `ci` | CI/CD changes | — |

**Scopes:** `agent`, `auth`, `chat`, `i18n`, `ui`, `api`, `db`, `deps`, `infra`, `sentry`, `analytics`, `worker`, `cms`, `blog`

**Examples:**
```
feat(agent): add web search tool to conversation graph
fix(auth): resolve redirect loop on expired sessions
feat(cms): add testimonials block type
chore(deps): upgrade next to 15.2
feat(api)!: change response envelope format
```

### Task Management (Linear)

We use **Linear** for task management. Linear is integrated via MCP server in Claude Code.

**Workflow:**
1. Create or pick a task in Linear
2. Create a branch: `hyp-123-short-description`
3. Reference the task in PR descriptions
4. PRs automatically link to Linear tasks when the branch name includes the task number

---

## Development Workflow

```mermaid
flowchart TD
    A["Pick or create Linear task"] --> B["/plan — Create implementation plan"]
    B --> C["Review & approve plan"]
    C --> D["Create task branch: hyp-123-description"]
    D --> E["Write tests first (TDD)"]
    E --> F["Implement to pass tests"]
    F --> G["Refactor while green"]
    G --> H["Commit with conventional messages"]
    H --> I["PR to dev"]
    I --> J["Review & merge"]
    J --> K["dev → main (release via semantic-release)"]
```

**No code is written without an approved plan. No implementation without tests first.**
