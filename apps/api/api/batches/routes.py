"""Batch API routes."""

import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import StreamingResponse

from api.batches.crud import BatchCrud, BatchCrudDep
from api.batches.models.batch import Batch
from api.batches.schemas import BatchRead
from api.batches.service import BatchServiceDep
from api.batches.tasks import cleanup_batch_files
from api.core.schemas import PageResponse
from api.deps.auth import get_current_session
from api.deps.storage import ValidatedFileDep
from api.rate_limit import limiter
from api.storage import StorageDep
from api.videos.crud import VideoCrudDep

logger = logging.getLogger(__name__)


async def get_batch_or_404(
    batch_id: uuid.UUID = Path(),
    crud: BatchCrud = Depends(),
) -> Batch:
    """Dependency that fetches a batch by ID or raises 404."""
    batch = await crud.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


BatchDep = Annotated[Batch, Depends(get_batch_or_404)]

batches_router = APIRouter(
    prefix="/batches", tags=["batches"], dependencies=[Depends(get_current_session)]
)


@batches_router.post("/upload", response_model=BatchRead, status_code=201)
@limiter.limit("5/minute")
async def upload_batch(
    request: Request,
    validated_file: ValidatedFileDep,
    service: BatchServiceDep,
    batch_name: str = Form(...),
    column_mapping: str = Form(...),
) -> BatchRead:
    """Upload an Excel/CSV file to create a batch. Processing happens in background."""
    try:
        mapping = json.loads(column_mapping)
    except json.JSONDecodeError as error:
        raise HTTPException(400, "Invalid column_mapping JSON") from error

    return await service.create_batch(
        contents=validated_file.contents,
        file_name=validated_file.filename,
        batch_name=batch_name,
        column_mapping=mapping,
    )


@batches_router.get("/", response_model=PageResponse[BatchRead])
async def list_batches(
    crud: BatchCrudDep,
    page: int = 1,
    page_size: int = 50,
) -> PageResponse[BatchRead]:
    """List batches (paginated)."""
    page_resp = await crud.get_multi(page=page, page_size=page_size)
    page_resp.items = [BatchRead.model_validate(batch) for batch in page_resp.items]
    return page_resp


@batches_router.get("/{batch_id}", response_model=BatchRead)
async def get_batch(batch: BatchDep) -> BatchRead:
    """Get a batch by ID."""
    return BatchRead.model_validate(batch)


@batches_router.get("/{batch_id}/export-zip")
@limiter.limit("3/minute")
async def export_batch_zip(
    request: Request,
    batch: BatchDep,
    video_crud: VideoCrudDep,
    storage: StorageDep,
) -> StreamingResponse:
    """Download all completed videos in a batch as a ZIP file."""
    finished = await video_crud.get_finished_by_batch(batch.id)
    if not finished:
        raise HTTPException(status_code=400, detail="No finished videos to export")

    files = [
        (f"videos/{video.id}/output.mp4", f"video-{index:03d}-{str(video.id)[:8]}.mp4")
        for index, video in enumerate(finished, 1)
    ]

    return StreamingResponse(
        storage.stream_zip(files),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{batch.name}.zip"'},
    )


@batches_router.delete("/{batch_id}", status_code=204)
async def delete_batch(batch: BatchDep, crud: BatchCrudDep) -> None:
    """Delete a batch, its videos, and S3 files."""
    await crud.delete(batch.id)
    cleanup_batch_files.delay(str(batch.id))
