# Testing

## Overview

The backend test suite lives in `apps/api/__tests__/` and uses **pytest**.

The config is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short -m 'not eval and not benchmark'"
```

## Running Tests

```bash
# All tests (default — fast, no external deps)
poetry run pytest

# Single test file
poetry run pytest __tests__/core/test_crud.py -v

# Single test class
poetry run pytest __tests__/core/test_crud.py::TestBaseCrudCreate -v

# Verbose with output
poetry run pytest -v -s
```

## Directory Structure

```
apps/api/__tests__/
├── conftest.py          # Shared fixtures (app, client, mock_session)
├── helpers.py           # Mock utilities (fake_db_obj, mock_scalars_result, etc.)
├── auth/                # Auth route tests (login, logout, session, route protection)
│   └── test_auth_routes.py
└── core/                # Core CRUD and route tests
    ├── test_crud.py     # BaseCrud unit tests (using Video model)
    └── test_routes.py   # Health check and root endpoint tests
```

## Fixtures

Defined in `__tests__/conftest.py`:

| Fixture | Description |
|---------|-------------|
| `app_core_only` | Minimal FastAPI app with only core routes (no DB/lifespan) |
| `client` | Test client for the core-only app |
| `app` | Full application instance with all routers |
| `authed_client` | Test client with no auth restrictions |
| `mock_session` | Mocked AsyncSession with standard DB operations stubbed |

## Unit Tests

Unit tests mock all external dependencies (DB, APIs) and run instantly. They verify CRUD operations, schema validation, and route behavior.

**Key helpers** (`__tests__/helpers.py`):

| Helper | Purpose |
|--------|---------|
| `fake_db_obj(**attrs)` | Creates a MagicMock with given attributes |
| `mock_scalars_result(items, session=)` | Mocks `session.execute → .scalars().all()` |
| `mock_scalar_count(value, session=)` | Mocks scalar count queries |

### CRUD Unit Test Example

```python
# __tests__/core/test_crud.py
class TestBaseCrudCreate:
    """Verify BaseCrud.create persists a new record and returns the model instance."""

    @pytest.mark.asyncio
    async def test_create_returns_model_instance(self, mock_session: AsyncMock):
        """Creating a record should return a Video instance and call save."""
        crud = BaseCrud(session=mock_session, model=Video)
        schema = FakeCreate(script_text="Hello world")

        with patch("api.core.crud.save", new_callable=AsyncMock) as mock_save:
            result = await crud.create(schema)

        assert isinstance(result, Video)
        mock_save.assert_awaited_once()
```

## Auth Tests

### Backend (`__tests__/auth/test_auth_routes.py`)

21 parametrized tests covering login, logout, session validation, and route protection.

**Pattern — parametrized route protection:**

```python
PROTECTED_ROUTES = [
    ("GET", "/api/v1/videos/"),
    ("POST", "/api/v1/videos/"),
    # ... all video/shot routes + /auth/me
]

PUBLIC_ROUTES = [
    ("GET", "/"), ("GET", "/health"),
    ("POST", "/api/v1/auth/login"), ("POST", "/api/v1/auth/logout"),
]

@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_unauthenticated(method, path, client):
    response = getattr(client, method.lower())(path)
    assert response.status_code == 401
```

Adding a new protected route? Just add it to `PROTECTED_ROUTES` — the test automatically covers it.

**Helper — signing test cookies:**

```python
def _auth_cookie(client):
    """Authenticate via login and return cookie jar for subsequent requests."""
    response = client.post("/api/v1/auth/login", json={"password": TEST_PASSWORD})
    assert response.status_code == 200
    return response.cookies
```

### Frontend E2E (`apps/react/e2e/auth.spec.ts`)

12 Playwright tests using **route interception** — no running backend needed:

```typescript
await page.route("**/api/v1/auth/me", (route) =>
  route.fulfill({
    status: 401,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Not authenticated" }),
  })
);
```

**Covered scenarios:** unauthenticated redirects, login success/failure/loading state, expired session on navigation, expired session mid-API-call, authenticated access, logout.

!!! tip "Run E2E from the right directory"
    Playwright tests must be run from `apps/react/` (not the monorepo root) so `baseURL` resolves correctly:
    ```bash
    cd apps/react && pnpm test:e2e
    ```

---

## E2E Tests (Playwright)

E2E tests live in `apps/react/e2e/` and use Playwright.

```bash
cd apps/react
pnpm test:e2e           # Run all E2E tests
pnpm test:e2e:debug     # Debug mode with browser visible
```

## Adding Tests

### For a new backend module:

1. Add unit tests to `apps/api/__tests__/{module}/`
2. Test CRUD operations with mocked DB sessions
3. Test route handlers with test client
4. Run `poetry run pytest` to verify

### For a new protected route:

1. Add the route tuple to `PROTECTED_ROUTES` in `test_auth_routes.py`
2. The parametrized test automatically verifies 401 for unauthenticated requests
