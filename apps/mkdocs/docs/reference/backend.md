# Backend Reference — FastAPI

## Quick Navigation

| Area | Path |
|------|------|
| App factory | `apps/fastapi/api/app.py` |
| Uvicorn entry point | `apps/fastapi/api/main.py` |
| Settings | `apps/fastapi/api/settings.py` |
| Agent graph | `apps/fastapi/agents/graph.py` |
| Agent nodes | `apps/fastapi/agents/nodes/` |
| Agent tools | `apps/fastapi/agents/tools.py` |
| Agent routes (CopilotKit) | `apps/fastapi/api/agents/routes.py` |
| Items module (example) | `apps/fastapi/api/items/` |
| Dependencies (auth, db, langfuse) | `apps/fastapi/api/deps/` |
| Sentry integration | `apps/fastapi/api/deps/sentry.py` |
| Langfuse integration | `apps/fastapi/api/deps/langfuse.py` |
| Core (health, base models, CRUD) | `apps/fastapi/api/core/` |
| Celery worker | `apps/fastapi/worker/` |
| Migrations | `apps/fastapi/migrations/versions/` |
| Tests | `apps/fastapi/__tests__/` |

## Project Layout

The backend is split into four top-level Python packages, each a distinct runtime:

```
apps/fastapi/
├── api/              # FastAPI HTTP server (routes, modules, deps)
├── agents/           # LangGraph agent (graph, nodes, prompts, state)
├── worker/           # Celery background tasks
├── __tests__/        # pytest tests
├── migrations/       # Alembic migrations
└── pyproject.toml    # Poetry config + CLI scripts
```

## App Factory Pattern

The FastAPI app is created via a factory function with lifespan context manager:

```python
# api/app.py
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init Sentry + LangGraph checkpointer."""
    init_sentry()
    await init_checkpointer()
    yield

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(core_router)
    app.include_router(agent_router)
    app.include_router(items_router, prefix="/api/v1")
    # ... register all routers + exception handlers
    return app
```

## Module Pattern

Every domain module under `api/` follows this structure:

```
module_name/
├── routes.py           # Thin FastAPI router (delegates to service/crud)
├── models/             # SQLAlchemy models (or models.py)
├── schemas/            # Pydantic request/response models (or schemas.py)
├── crud/               # Database operations (or crud.py)
├── service.py          # Business logic (optional — for complex modules)
└── __init__.py
```

**Current modules:** `items/`, `agents/`, `core/`, `deps/`

## Where to Put New Code

| You need... | Put it in... |
|-------------|-------------|
| A new API endpoint | `api/{module}/routes.py` → register in `api/app.py` |
| A new database table | `api/{module}/models/` → generate Alembic migration |
| Request/response types | `api/{module}/schemas/` |
| Database queries | `api/{module}/crud/` (extend `BaseCrud` for class-based) |
| Business logic | `api/{module}/service.py` |
| A shared dependency | `api/deps/` |
| A new Celery task | `worker/tasks.py` |
| A new agent node | `agents/nodes/` → wire in `agents/graph.py` |
| A new agent tool | `agents/tools.py` → add to `TOOLS` list |
| An agent prompt | `agents/prompts/` (local constants) |
| A test | `__tests__/test_{name}.py` |

---

## Core Patterns

### Typed Dependencies

All dependencies use the `Annotated[..., Depends(...)]` pattern for clean injection:

```python
# Define typed dependency alias
SessionDep = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUserDep = Annotated[User, Depends(get_user)]
ItemServiceDep = Annotated[ItemService, Depends(ItemService)]
ItemCrudDep = Annotated[ItemCrud, Depends(ItemCrud)]

# Use in route handlers
@router.get("/me")
async def get_my_item(
    service: ItemServiceDep,
    current_user: AuthenticatedUserDep,
    locale: Locale = Query(Locale.EN),
) -> ItemResponse | None:
    return await service.get_item(current_user.id, locale)
```

### Authentication

JWT validated against Better Auth's JWKS endpoint:

```python
# api/deps/auth.py
@lru_cache
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(str(settings.OAUTH_PROVIDER_JWKS_URL), cache_keys=True)

async def get_user(request: Request, jwks_client: PyJWKClient = Depends(get_jwks_client)) -> User:
    """Validate Bearer JWT and return user."""
    # Extract token from Authorization header
    # Get signing key from JWKS
    # Decode with algorithms: EdDSA, RS256, ES256
    # Validate issuer and audience
    # Return User model_validate(payload)
```

### Database Session

```python
# api/deps/db.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()

async def save(session: AsyncSession, db_object: object) -> None:
    """Add, commit, and refresh a database object."""
    session.add(db_object)
    await session.commit()
    await session.refresh(db_object)

SessionDep = Annotated[AsyncSession, Depends(get_db)]
```

### Base CRUD (Generic)

All CRUD classes extend `BaseCrud` with typed generics:

```python
# api/core/crud.py
class BaseCrud(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, session: SessionDep, model: type[ModelType]):
        self.db_session = session
        self.model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        obj_data = {k: v for k, v in obj_in.model_dump().items() if v is not None}
        db_obj = self.model(**obj_data)
        await save(self.db_session, db_obj)
        return db_obj

    async def get(self, id: UUID) -> ModelType | None: ...
    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]: ...
    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType: ...
    async def delete(self, id: UUID) -> None: ...
    async def count(self) -> int: ...
    async def exists(self, id: UUID) -> bool: ...
```

### CRUD Subclass Pattern

```python
# api/items/crud/item.py
class ItemCrud(
    BaseCrud[Item, ItemCreate, ItemUpdate]
):
    def __init__(self, session: SessionDep):
        super().__init__(session, Item)

    async def get_by_user_id(self, user_id: str) -> Item | None:
        statement = select(Item).where(
            Item.user_id == user_id
        )
        result = await self.db_session.execute(statement)
        return result.scalar_one_or_none()

# Typed dependency
ItemCrudDep = Annotated[ItemCrud, Depends(ItemCrud)]
```

### SQLAlchemy Model Pattern

```python
# api/items/models/item.py
class Item(BaseModel):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
```

**Conventions:** UUID primary keys, `created_at`/`updated_at` timestamps (UTC, no tzinfo), snake_case table and column names, indexed foreign keys.

### Service Layer Pattern

For modules with business logic beyond simple CRUD:

```python
# api/items/service.py
class ItemService:
    def __init__(
        self,
        session: SessionDep,
        item_crud: ItemCrudDep,
    ):
        self.session = session
        self.item_crud = item_crud

    async def get_item(
        self, user_id: str, locale: Locale = Locale.EN
    ) -> ItemResponse | None:
        item = await self.item_crud.get_by_user_id(user_id)
        if not item:
            return None
        return ItemResponse.model_validate(item)

    async def delete_item(self, user_id: str) -> None:
        item = await self.item_crud.get_by_user_id(user_id)
        if not item:
            raise ValueError("Item not found")
        await self.item_crud.delete(item.id)

ItemServiceDep = Annotated[ItemService, Depends(ItemService)]
```

### Route Pattern

```python
# api/items/routes.py
router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_user)],  # Auth required for all routes
)

@router.get("/me", response_model=ItemResponse | None)
async def get_my_item(
    service: ItemServiceDep,
    current_user: AuthenticatedUserDep,
    locale: Locale = Query(Locale.EN),
) -> ItemResponse | None:
    return await service.get_item(current_user.id, locale)

@router.delete("/me", status_code=204)
async def delete_my_item(
    service: ItemServiceDep,
    current_user: AuthenticatedUserDep,
) -> None:
    try:
        await service.delete_item(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
```

### Exception Handling

```python
# api/exceptions.py — global exception handlers registered in app factory
# Handlers for: HTTPException, RequestValidationError, Exception (catch-all)
# All responses use ErrorResponse schema: { status: "error", message: str, detail?: Any }
```

---

## Langfuse Integration

Langfuse is used for **LLM tracing and observability** (not prompt management). All prompts are local Python constants — see `agents/prompts/`.

```python
# api/deps/langfuse.py

@lru_cache(maxsize=1)
def get_langfuse_client() -> Langfuse:
    return Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        base_url=settings.LANGFUSE_BASE_URL,
        environment=settings.ENVIRONMENT,
    )

@contextmanager
def langfuse_trace(*, user_id: str = "", session_id: str = "", **metadata) -> Generator[dict, None, None]:
    """Establish Langfuse trace context and yield a LangChain config dict."""
    with propagate_attributes(user_id=user_id, session_id=session_id, metadata=metadata):
        yield {
            "callbacks": [CallbackHandler()],
            "tags": [settings.ENVIRONMENT],
        }
```

**Usage in LLM calls:**

```python
async with langfuse_trace(user_id=user_id) as config:
    response = await model.ainvoke([HumanMessage(content=prompt)], config=config)
```

---

## Background Processing (Celery)

```python
# worker/app.py — Celery configuration
celery_app = Celery("worker")
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_time_limit=1800,       # 30 min hard limit
    task_soft_time_limit=1500,  # 25 min soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
)

# worker/tasks.py
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def my_background_task(self, user_id: str, **kwargs) -> None:
    async def _run() -> None:
        # Perform async work here
        pass

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

## Registered Routes

| Router | Prefix | Source |
|--------|--------|--------|
| `core_router` | `/` (root) | `api/core/routes.py` — health check, root |
| `agent_router` | `/` (root) | `api/agents/routes.py` — CopilotKit endpoint |
| `items_router` | `/api/v1/items` | `api/items/routes.py` |

## Settings

Configured via Pydantic `BaseSettings` in `api/settings.py` with `API_` prefix:

| Category | Variables |
|----------|-----------|
| Core | `API_PROJECT_NAME`, `API_SECRET_KEY`, `API_ENVIRONMENT` (local/staging/production) |
| Database | `API_DATABASE_URL` (postgresql+asyncpg) |
| Server | `API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_LOG_LEVEL`, `API_SWAGGER_HIDE` |
| OAuth | `API_OAUTH_PROVIDER_URL`, `API_OAUTH_CLIENT_ID`, `API_OAUTH_CLIENT_SECRET` |
| OpenAI | `API_OPENAI_API_KEY` |
| Langfuse | `API_LANGFUSE_PUBLIC_KEY`, `API_LANGFUSE_SECRET_KEY`, `API_LANGFUSE_BASE_URL` |
| Celery | `API_CELERY_BROKER_URL`, `API_CELERY_RESULT_BACKEND` (Redis) |
| Sentry | `API_SENTRY_DSN`, `API_SENTRY_TRACES_SAMPLE_RATE`, `API_SENTRY_PROFILES_SAMPLE_RATE` |

## Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| Dependency alias | `XyzDep = Annotated[Xyz, Depends(Xyz)]` | `SessionDep`, `AuthenticatedUserDep` |
| Service class | `{Domain}Service` | `ItemService` |
| CRUD class | `{Model}Crud` | `ItemCrud` |
| Response schema | `{Model}Response` | `ItemResponse` |
| Create/Update schema | `{Model}Create` / `{Model}Update` | `ItemCreate`, `ItemUpdate` |
| Enum | `StrEnum` | `Locale.EN`, `Locale.LT` |
| Router variable | `router` | Included via `app.include_router(router)` |
| Table name | snake_case | `items`, `item_translations` |

## Key Libraries

| Library | Purpose | Used In |
|---------|---------|---------|
| FastAPI | HTTP framework | `api/` |
| SQLAlchemy 2.0 | Async ORM | `api/*/models/` |
| Pydantic | Schema validation | `api/*/schemas/` |
| Alembic | DB migrations | `migrations/` |
| LangGraph | Agent orchestration | `agents/` |
| LangChain | LLM integration | `agents/nodes/` |
| Langfuse | LLM tracing + observability | `api/deps/langfuse.py` |
| Celery | Task queue | `worker/` |
| Redis | Broker + cache | `worker/settings.py` |
| Sentry SDK | Error tracking | `api/deps/sentry.py` |

## Running

| Command | Purpose |
|---------|---------|
| `poetry run start` | Start uvicorn server |
| `poetry run pytest` | Run tests |
| `poetry run pytest -v -s` | Run tests (verbose with output) |
| `poetry run celery-worker` | Start Celery worker |
| `poetry run alembic upgrade head` | Apply migrations |
| `poetry run alembic revision --autogenerate -m "msg"` | Generate migration |
