# Backend Reference — FastAPI

## Quick Navigation

| Area | Path |
|------|------|
| App factory | `apps/api/api/app.py` |
| Uvicorn entry point | `apps/api/api/main.py` |
| Settings | `apps/api/api/settings.py` |
| Videos module | `apps/api/api/videos/` |
| Dependencies (db, storage, celery) | `apps/api/api/deps/` |
| Sentry integration | `apps/api/api/deps/sentry.py` |
| R2 storage | `apps/api/api/deps/storage.py` |
| Celery config + worker | `apps/api/api/deps/celery.py` |
| Celery tasks | `apps/api/api/deps/tasks.py` |
| Core (health, base models, CRUD) | `apps/api/api/core/` |
| Migrations | `apps/api/migrations/versions/` |
| Tests | `apps/api/__tests__/` |

## Project Layout

```
apps/api/
├── api/              # FastAPI HTTP server (routes, modules, deps)
│   ├── auth/         # Authentication (login, logout, session check)
│   ├── core/         # Base models, CRUD, health routes
│   ├── videos/       # Video pipeline domain (models, routes, schemas, crud)
│   └── deps/         # Shared dependencies (db, storage, celery, sentry, auth)
├── __tests__/        # pytest tests
├── migrations/       # Alembic migrations
└── pyproject.toml    # Poetry config + CLI scripts
```

## App Factory Pattern

```python
# api/app.py
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init Sentry."""
    init_sentry()
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
    app.include_router(videos_router, prefix="/api/v1")
    app.include_router(shots_router, prefix="/api/v1")
    return app
```

## Module Pattern

Every domain module under `api/` follows this structure:

```
module_name/
├── routes.py           # FastAPI router (delegates to crud)
├── models/             # SQLAlchemy models
├── schemas.py          # Pydantic request/response schemas
├── crud.py             # CRUD dependency classes (extend BaseCrud)
└── __init__.py
```

**Current modules:** `videos/`, `auth/`, `core/`, `deps/`

## Where to Put New Code

| You need... | Put it in... |
|-------------|-------------|
| A new API endpoint | `api/{module}/routes.py` → register in `api/app.py` |
| A new database table | `api/{module}/models/` → generate Alembic migration |
| Request/response types | `api/{module}/schemas.py` |
| Database queries | `api/{module}/crud.py` (extend `BaseCrud`) |
| A shared dependency | `api/deps/` |
| A new Celery task | `api/deps/tasks.py` |
| A test | `__tests__/{module}/test_{name}.py` |

---

## Core Patterns

### Base Model (SQLAlchemy)

All models inherit `created_at` and `updated_at` from `BaseModel`:

```python
# api/core/models.py
class BaseModel(DeclarativeBase):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=True,
    )
```

### SQLAlchemy Model Pattern

```python
# api/videos/models/video.py
class Video(BaseModel):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    # ... created_at and updated_at inherited from BaseModel
```

**Conventions:** UUID primary keys, timestamps inherited from BaseModel (UTC, no tzinfo), snake_case table and column names, indexed foreign keys.

### Typed Dependencies

All dependencies use the `Annotated[..., Depends(...)]` pattern:

```python
# Define typed dependency alias
SessionDep = Annotated[AsyncSession, Depends(get_db)]
VideoCrudDep = Annotated[VideoCrud, Depends()]
ShotCrudDep = Annotated[ShotCrud, Depends()]
StorageDep = Annotated[StorageService, Depends(get_storage)]

# Use in route handlers
@router.get("/{video_id}", response_model=VideoReadWithShots)
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep):
    video = await crud.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
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
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_data)
        await save(self.db_session, db_obj)
        return db_obj

    async def get(self, id: UUID) -> ModelType | None: ...
    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]: ...
    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType | None: ...
    async def delete(self, id: UUID) -> bool: ...
    async def count(self) -> int: ...
    async def exists(self, id: UUID) -> bool: ...
```

### CRUD Subclass Pattern

```python
# api/videos/crud.py
class VideoCrud(BaseCrud[Video, VideoCreate, VideoUpdate]):
    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Video)

class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)

# Typed dependencies — inject directly into route handlers
VideoCrudDep = Annotated[VideoCrud, Depends()]
ShotCrudDep = Annotated[ShotCrud, Depends()]
```

### Route Pattern

```python
# api/videos/routes.py
videos_router = APIRouter(prefix="/videos", tags=["videos"])
shots_router = APIRouter(prefix="/videos/{video_id}/shots", tags=["shots"])

@videos_router.post("/", response_model=VideoRead, status_code=201)
async def create_video(video_in: VideoCreate, crud: VideoCrudDep):
    """Create a new video record."""
    return await crud.create(video_in)

@videos_router.get("/{video_id}", response_model=VideoReadWithShots)
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep):
    """Get a video by ID, including its shots."""
    video = await crud.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
```

### Exception Handling

```python
# api/exceptions.py — global exception handlers registered in app factory
# Handlers for: HTTPException, RequestValidationError, Exception (catch-all)
# All responses use ErrorResponse schema: { status: "error", message: str, detail?: Any }
```

---

## Cloudflare R2 Storage

```python
# api/deps/storage.py
class StorageService:
    """S3-compatible client for Cloudflare R2."""

    def upload_file(self, key: str, data: bytes, content_type: str) -> None: ...
    def download_file(self, key: str) -> bytes: ...
    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str: ...
    def delete_file(self, key: str) -> None: ...

StorageDep = Annotated[StorageService, Depends(get_storage)]
```

---

## Background Processing (Celery)

```python
# api/deps/celery.py — Celery app config + worker entry point
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

def main() -> None:
    """Run Celery worker (concurrency=1 locally)."""
    celery_app.worker_main(argv=["worker", "--loglevel=info", "--concurrency=1", "--pool=solo", "--events"])

# api/deps/tasks.py
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def my_background_task(self, **kwargs) -> None:
    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

## Registered Routes

| Router | Prefix | Tags | Source |
|--------|--------|------|--------|
| `core_router` | `/` | core | `api/core/routes.py` — health check, root |
| `auth_router` | `/api/v1/auth` | auth | `api/auth/routes.py` — login, logout, session check |
| `videos_router` | `/api/v1/videos` | videos | `api/videos/routes.py` |
| `shots_router` | `/api/v1/videos/{video_id}/shots` | shots | `api/videos/routes.py` |

## Settings

Configured via Pydantic `BaseSettings` in `api/settings.py` with `API_` prefix:

| Category | Variables |
|----------|-----------|
| Core | `API_PROJECT_NAME`, `API_SECRET_KEY`, `API_ENVIRONMENT` (local/staging/production) |
| Auth | `API_APP_PASSWORD`, `API_SESSION_MAX_AGE` (default: 7 days), `API_CORS_ORIGINS` |
| Database | `API_DATABASE_URL` (postgresql+asyncpg) |
| Server | `API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_LOG_LEVEL`, `API_SWAGGER_HIDE` |
| Cloudflare R2 | `API_R2_ACCOUNT_ID`, `API_R2_ACCESS_KEY_ID`, `API_R2_SECRET_ACCESS_KEY`, `API_R2_BUCKET_NAME` |
| ElevenLabs | `API_ELEVENLABS_API_KEY` |
| Anthropic | `API_ANTHROPIC_API_KEY` |
| Gemini | `API_GEMINI_API_KEY` |
| Celery | `API_CELERY_BROKER_URL`, `API_CELERY_RESULT_BACKEND` (Redis) |
| Sentry | `API_SENTRY_DSN`, `API_SENTRY_TRACES_SAMPLE_RATE`, `API_SENTRY_PROFILES_SAMPLE_RATE` |

## Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| Dependency alias | `XyzDep = Annotated[Xyz, Depends()]` | `VideoCrudDep`, `SessionDep`, `AuthDep`, `SerializerDep` |
| CRUD class | `{Model}Crud` | `VideoCrud`, `ShotCrud` |
| Read schema | `{Model}Read` | `VideoRead`, `ShotRead` |
| Create/Update schema | `{Model}Create` / `{Model}Update` | `VideoCreate`, `VideoUpdate` |
| Router variable | `{domain}_router` | `videos_router`, `shots_router` |
| Table name | snake_case | `videos`, `shots` |

## Key Libraries

| Library | Purpose | Used In |
|---------|---------|---------|
| FastAPI | HTTP framework | `api/` |
| SQLAlchemy 2.0 | Async ORM | `api/*/models/` |
| Pydantic | Schema validation | `api/*/schemas.py` |
| Alembic | DB migrations | `migrations/` |
| Celery | Task queue | `api/deps/celery.py` |
| Redis | Broker + result backend | `api/deps/celery.py` |
| boto3 | Cloudflare R2 (S3-compatible) | `api/deps/storage.py` |
| itsdangerous | Signed cookie sessions | `api/deps/auth.py` |
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
