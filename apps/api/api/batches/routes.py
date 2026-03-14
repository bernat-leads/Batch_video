"""Batch API routes."""

import json
import uuid

from fastapi import APIRouter, Form, HTTPException

from api.batches.crud import BatchCrudDep
from api.batches.schemas import BatchRead
from api.batches.services import BatchUploadServiceDep
from api.core.schemas import PageResponse
from api.deps.auth import AuthDep
from api.deps.file_upload import ValidatedFileDep

batches_router = APIRouter(prefix="/batches", tags=["batches"])


@batches_router.post("/upload", response_model=BatchRead, status_code=201)
async def upload_batch(
    validated_file: ValidatedFileDep,
    service: BatchUploadServiceDep,
    _auth: AuthDep,
    batch_name: str = Form(...),
    column_mapping: str = Form(...),
) -> BatchRead:
    """Upload an Excel/CSV file to create a batch. Processing happens in background."""
    try:
        mapping = json.loads(column_mapping)
    except json.JSONDecodeError as e:
        raise HTTPException(400, "Invalid column_mapping JSON") from e

    return await service.create_batch(
        contents=validated_file.contents,
        file_name=validated_file.filename,
        batch_name=batch_name,
        column_mapping=mapping,
    )


@batches_router.get("/", response_model=PageResponse[BatchRead])
async def list_batches(
    crud: BatchCrudDep,
    _auth: AuthDep,
    page: int = 1,
    page_size: int = 50,
) -> PageResponse[BatchRead]:
    """List batches (paginated)."""
    return await crud.get_multi(page=page, page_size=page_size)


@batches_router.get("/{batch_id}", response_model=BatchRead)
async def get_batch(
    batch_id: uuid.UUID, crud: BatchCrudDep, _auth: AuthDep
) -> BatchRead:
    """Get a batch by ID."""
    batch = await crud.get_as_schema(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@batches_router.delete("/{batch_id}", status_code=204)
async def delete_batch(batch_id: uuid.UUID, crud: BatchCrudDep, _auth: AuthDep) -> None:
    """Delete a batch, its videos, and R2 files."""
    from api.batches.tasks import cleanup_batch_files

    deleted = await crud.delete(batch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Batch not found")
    cleanup_batch_files.delay(str(batch_id))
