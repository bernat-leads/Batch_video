# Testing

## Overview

The backend test suite lives in `apps/fastapi/__tests__/` and uses **pytest**. Tests are split into two categories:

| Category | Marker | Default Run | LLM Calls | Speed |
|----------|--------|-------------|-----------|-------|
| **Unit tests** | *(none)* | Yes (`poetry run pytest`) | No | Fast (<5s) |
| **Eval tests** | `@pytest.mark.eval` | No (excluded by default) | Yes (OpenAI) | Slow (5-10 min) |

The split is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short -m 'not eval'"
markers = [
    "eval: LLM-based evaluation tests (require OPENAI_API_KEY, slow)",
]
```

## Running Tests

```bash
# Unit tests only (default — fast, no LLM)
poetry run pytest

# Eval tests only (slow, requires OPENAI_API_KEY)
poetry run pytest -m eval

# All tests
poetry run pytest -m ""

# Single test file
poetry run pytest __tests__/items/test_items.py -v

# Single test class
poetry run pytest __tests__/items/test_items.py::TestItemCrud -v
```

## Directory Structure

```
apps/fastapi/__tests__/
├── helpers.py                      # Shared mock utilities (to_dict, mock_scalars_result, etc.)
├── agents/                         # Agent graph, node, route, and tool tests
│   ├── test_graph.py
│   ├── test_nodes.py
│   ├── test_routes.py
│   └── test_tools.py
├── items/                          # Item CRUD and service tests
└── eval/                           # LLM-based evaluation tests (optional)
    ├── conftest.py                 # Shared transcripts + fixtures
    ├── eval_datasets.py            # Structured datasets for experiment runner
    └── eval_runner.py              # Langfuse experiment runner
```

## Unit Tests

Unit tests mock all external dependencies (DB, LLM, file I/O) and run instantly. They verify business logic, CRUD operations, schema validation, and route behavior.

**Key helpers** (`__tests__/helpers.py`):

| Helper | Purpose |
|--------|---------|
| `to_dict(result)` | Normalizes Pydantic model or dict to dict |
| `mock_scalars_result(items, session=)` | Mocks `session.execute → .scalars().all()` |
| `mock_scalar_one_or_none(value, session=)` | Mocks single-row lookup |
| `fake_db_obj(**attrs)` | Creates a MagicMock with given attributes |

### CRUD Unit Test Example

```python
# __tests__/items/test_item_crud.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from api.items.crud.item import ItemCrud
from __tests__.helpers import mock_scalar_one_or_none, fake_db_obj

@pytest.mark.asyncio
async def test_get_by_user_id_returns_item():
    session = AsyncMock()
    item = fake_db_obj(id="abc", user_id="user-1", data={})
    mock_scalar_one_or_none(item, session)

    crud = ItemCrud(session)
    result = await crud.get_by_user_id("user-1")

    assert result is item
```

### Route Unit Test Example

```python
# __tests__/items/test_item_routes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_my_item_returns_200(
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

### Agent Node Test Example

```python
# __tests__/agents/test_nodes.py
import pytest
from unittest.mock import AsyncMock, patch
from agents.nodes.conversation import conversation_node
from agents.state import ChatState

@pytest.mark.asyncio
async def test_conversation_node_invokes_llm():
    state = ChatState(messages=[], user_id="user-1", locale="en")
    config = {"configurable": {"thread_id": "t-1"}}

    with patch("agents.nodes.conversation.model") as mock_model:
        mock_model.bind_tools.return_value.ainvoke = AsyncMock(return_value=MagicMock(tool_calls=[]))
        result = await conversation_node(state, config)

    assert result is not None
```

---

## Eval Tests

Eval tests call the actual OpenAI API to verify that LLM prompts produce correct outputs. They are the **quality gate** for prompt changes.

### Test Class Taxonomy

#### 1. `TestXExperiment` — Aggregate accuracy

Runs the full dataset through `run_experiment()` and asserts average classification accuracy is ≥ 80%.

```python
class TestMyComponentExperiment:
    def test_accuracy(self):
        result = run_experiment(
            name="my_component",
            dataset=MY_DATASET,
            output_key="category",
            canonical_values=MY_CANONICAL_VALUES,
        )
        avg = next(
            (ev.value for ev in result.run_evaluations if ev.name == "avg_accuracy"),
            None,
        )
        assert avg is not None and avg >= 0.8
```

#### 2. `TestXOutputValidation` — Per-item correctness

Tests individual inputs for correct classification and validates output structure.

```python
class TestMyComponentOutputValidation:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("transcript, expected", [...])
    async def test_correct_classification(self, transcript, expected):
        result = to_dict(await my_component.analyze(transcript))
        assert result["category"] == expected
```

#### 3. `TestXEdgeCases` — Robustness

Verifies the component handles unusual input without crashing: minimal input, contradictory signals, multilingual text.

```python
class TestMyComponentEdgeCases:
    @pytest.mark.asyncio
    async def test_minimal_input_produces_valid_output(self):
        result = to_dict(await my_component.analyze("Hello."))
        assert result["category"] in MY_CANONICAL_VALUES
```

### Eval Datasets

Structured data for the experiment runner. Each item has:

```python
{
    "input": {"conversational_data": TRANSCRIPT, "label": "CategoryA"},
    "expected_output": {"category": "CategoryA"},
}
```

### Experiment Runner

`run_experiment()` runs a component on a dataset and returns evaluation results:

```python
result = run_experiment(
    name="my_component",       # Dataset name (for Langfuse reporting)
    dataset=MY_DATASET,        # From eval_datasets.py
    output_key="category",     # Field to check
    canonical_values=MY_CANONICAL_VALUES,
)

# result.item_results — per-item outputs and evaluations
# result.run_evaluations — aggregate metrics (avg_accuracy)
```

**Langfuse integration:** If `LANGFUSE_SECRET_KEY` is set, results are automatically reported to Langfuse for comparison across prompt iterations.

---

## E2E Tests (Playwright)

E2E tests live in `e2e/` at the repo root and use Playwright.

### Projects

| Project | Directory | Auth State |
|---------|-----------|-----------|
| `setup` | — | Generates storage state from UI sign-in |
| `unauthenticated` | `e2e/auth/` | No auth |
| `authenticated` | `e2e/dashboard/` | Uses stored auth session |
| `api` | `e2e/api/` | Direct FastAPI calls (baseURL: localhost:8000) |

### Example

```typescript
// e2e/dashboard/navigation.spec.ts
import { test, expect } from '@playwright/test';

test('user can navigate to settings', async ({ page }) => {
  await page.goto('/settings');
  await expect(page.getByRole('heading', { name: /settings/i })).toBeVisible();
});
```

### Running

```bash
pnpm test:e2e           # Run all E2E tests
pnpm test:e2e:debug     # Debug mode with browser visible
```

---

## Adding Tests

### For a new backend module:

1. Add unit tests to `apps/fastapi/__tests__/{module}/`
2. Test CRUD operations with mocked DB sessions
3. Test route handlers with mocked service dependencies
4. Run `poetry run pytest` to verify

### For a new agent tool:

1. Add test to `apps/fastapi/__tests__/agents/test_tools.py`
2. Mock `InjectedState` and verify returned `Command` updates
3. Test error paths — tool should return `ToolMessage` with error content

### For a new frontend page or flow:

1. Add Playwright test to `e2e/dashboard/{name}.spec.ts`
2. Use the `authenticated` project for protected pages
3. Use the `unauthenticated` project for auth pages
