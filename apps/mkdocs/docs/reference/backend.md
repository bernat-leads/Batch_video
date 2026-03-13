# Backend Reference — FastAPI SOP

> Step-by-step procedures for implementing backend features. Follow these exactly.

---

## Quick Reference

| What | Where |
|------|-------|
| App factory | `apps/api/api/app.py` |
| Settings | `apps/api/api/settings.py` (Pydantic, `API_` prefix) |
| Videos module | `apps/api/api/videos/` |
| Settings module | `apps/api/api/settings_module/` |
| Auth module | `apps/api/api/auth/` |
| Shared deps | `apps/api/api/deps/` (db, storage, celery, sentry) |
| Core (health, base) | `apps/api/api/core/` |
| Migrations | `apps/api/migrations/versions/` |
| Tests | `apps/api/__tests__/` |

## Module Structure (every domain follows this)

```
module_name/
├── __init__.py
├── enums.py            # Python str enums (when status/type fields exist)
├── routes.py           # FastAPI router — thin, delegates to crud
├── models/
│   ├── __init__.py     # Re-exports all models
│   └── model_name.py   # SQLAlchemy model
├── schemas.py          # Pydantic request/response schemas
└── crud.py             # CRUD classes (extend BaseCrud) + typed deps
```

**Current modules:** `videos/`, `settings_module/`, `auth/`, `core/`, `deps/`

---

## Registered Routes

| Router | Prefix | Source |
|--------|--------|--------|
| `core_router` | `/` | `api/core/routes.py` |
| `auth_router` | `/api/v1/auth` | `api/auth/routes.py` |
| `videos_router` | `/api/v1/videos` | `api/videos/routes.py` |
| `batches_router` | `/api/v1/batches` | `api/videos/routes.py` |
| `shots_router` | `/api/v1/videos/{video_id}/shots` | `api/videos/routes.py` |
| `settings_router` | `/api/v1/settings` | `api/settings_module/routes.py` |

**Route ordering rule:** Static paths (e.g., `/stats/dashboard`) MUST be defined BEFORE parameterized paths (e.g., `/{video_id}`) to avoid conflicts.

---

## SOP: Add a New Endpoint to Existing Module

1. Add Pydantic schema(s) in `schemas.py` (request/response)
2. Add CRUD method in `crud.py` if new query needed
3. Add route in `routes.py`:
   ```python
   @router.get("/path", response_model=MySchema)
   async def my_endpoint(crud: MyCrudDep, _auth: AuthDep):
       return await crud.my_method()
   ```
4. Regenerate frontend client: `pnpm run generate-api`

## SOP: Add a New Module

1. Create directory: `apps/api/api/{module_name}/`
2. Create `__init__.py`
3. Create `enums.py` if status/type fields needed:
   ```python
   import enum
   class MyStatus(str, enum.Enum):
       active = "active"
       inactive = "inactive"
   ```
4. Create SQLAlchemy model in `models/`:
   ```python
   class MyModel(BaseModel):
       __tablename__ = "my_table"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       status: Mapped[MyStatus] = mapped_column(String(20), default=MyStatus.active)
       # created_at, updated_at inherited from BaseModel
   ```
5. Create schemas in `schemas.py`:
   ```python
   class MyModelCreate(BaseModel):
       name: str
   class MyModelRead(BaseModel):
       id: uuid.UUID
       status: MyStatus
       created_at: datetime
       model_config = {"from_attributes": True}
   ```
6. Create CRUD in `crud.py`:
   ```python
   class MyModelCrud(BaseCrud[MyModel, MyModelCreate, MyModelUpdate]):
       def __init__(self, session: SessionDep) -> None:
           super().__init__(session=session, model=MyModel)
   MyModelCrudDep = Annotated[MyModelCrud, Depends()]
   ```
7. Create router in `routes.py`
8. Register in `apps/api/api/app.py`: `app.include_router(my_router, prefix="/api/v1")`
9. Import model in `migrations/env.py`
10. Generate migration: `cd apps/api && poetry run alembic revision --autogenerate -m "add my_table"`
11. Apply: `poetry run alembic upgrade head`
12. Regenerate client: `pnpm run generate-api`

## SOP: Add a Database Column

1. Add column to SQLAlchemy model
2. Update Pydantic schemas (Create, Update, Read) as needed
3. Generate migration: `poetry run alembic revision --autogenerate -m "add column_name to table"`
4. **If NOT NULL on existing rows:** Edit migration to add `server_default=''` (or appropriate default)
5. Apply: `poetry run alembic upgrade head`
6. Regenerate client: `pnpm run generate-api`

## SOP: Add Enum for Status Field

1. Create or update `enums.py` in the module:
   ```python
   class MyStatus(str, enum.Enum):
       active = "active"
       archived = "archived"
   ```
2. Use in model: `status: Mapped[MyStatus] = mapped_column(String(20), default=MyStatus.active)`
3. Use in schemas: `status: MyStatus` (Pydantic validates automatically)
4. Use in queries: `Model.status == MyStatus.active` (never string literals)
5. Orval auto-generates TS const enum on `pnpm run generate-api`

---

## Core Patterns

### BaseCrud (Generic)

```python
class BaseCrud(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    async def create(self, obj_in: CreateSchemaType) -> ModelType
    async def get(self, id: UUID) -> ModelType | None
    async def get_multi(self, *, page: int, page_size: int) -> PageResponse
    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType | None
    async def delete(self, id: UUID) -> bool
    async def count(self) -> int
    async def exists(self, id: UUID) -> bool
```

### Typed Dependencies

```python
SessionDep = Annotated[AsyncSession, Depends(get_db)]
VideoCrudDep = Annotated[VideoCrud, Depends()]
AuthDep = Annotated[str, Depends(require_auth)]
```

### Route Pattern

```python
@router.post("/", response_model=MyRead, status_code=201)
async def create_item(item_in: MyCreate, crud: MyCrudDep, _auth: AuthDep):
    return await crud.create(item_in)

@router.get("/{item_id}", response_model=MyRead)
async def get_item(item_id: uuid.UUID, crud: MyCrudDep, _auth: AuthDep):
    item = await crud.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```

### Database Session

```python
async def save(session: AsyncSession, db_object: object) -> None:
    session.add(db_object)
    await session.commit()
    await session.refresh(db_object)
```

---

## Key Libraries

| Library | Purpose |
|---------|---------|
| FastAPI | HTTP framework |
| SQLAlchemy 2.0 | Async ORM |
| Pydantic | Schema validation |
| Alembic | DB migrations (autogenerate only) |
| Celery + Redis | Task queue |
| boto3 | Cloudflare R2 (S3-compatible) |

## Commands

| Command | Purpose |
|---------|---------|
| `poetry run start` | Start uvicorn server |
| `poetry run pytest` | Run tests |
| `poetry run celery-worker` | Start Celery worker |
| `poetry run alembic upgrade head` | Apply migrations |
| `poetry run alembic revision --autogenerate -m "msg"` | Generate migration |
| `pnpm run generate-api` | Regenerate frontend client |
