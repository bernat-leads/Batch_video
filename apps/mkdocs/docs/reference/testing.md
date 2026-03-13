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

## E2E Tests (Playwright)

E2E tests live in `apps/react/e2e/` and use Playwright.

```bash
pnpm test:e2e           # Run all E2E tests
pnpm test:e2e:debug     # Debug mode with browser visible
```

## Adding Tests

### For a new backend module:

1. Add unit tests to `apps/api/__tests__/{module}/`
2. Test CRUD operations with mocked DB sessions
3. Test route handlers with test client
4. Run `poetry run pytest` to verify
