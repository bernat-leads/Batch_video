"""Video API routes."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse, StreamingResponse

from api.core.schemas import PageResponse
from api.deps.auth import get_current_session
from api.deps.db import SessionDep
from api.events.schemas import EventChannel
from api.events.service import EventServiceDep
from api.rate_limit import limiter
from api.storage import StorageDep
from api.videos.crud import VideoCrud, VideoCrudDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import (
    VideoCreate,
    VideoProgressEvent,
    VideoRead,
    VideoReadWithShots,
    VideoUpdate,
)

logger = logging.getLogger(__name__)


async def get_video_or_404(
    video_id: uuid.UUID = Path(),
    crud: VideoCrud = Depends(),
) -> Video:
    """Dependency that fetches a video by ID or raises 404."""
    video = await crud.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


VideoDep = Annotated[Video, Depends(get_video_or_404)]

videos_router = APIRouter(
    prefix="/videos", tags=["videos"], dependencies=[Depends(get_current_session)]
)


@videos_router.post("/", response_model=VideoRead, status_code=201)
async def create_video(video_in: VideoCreate, crud: VideoCrudDep) -> VideoRead:
    """Create a new video record."""
    video = await crud.create(video_in)
    return VideoRead.model_validate(video)


@videos_router.get("/", response_model=PageResponse[VideoRead])
async def list_videos(
    crud: VideoCrudDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    batch_id: uuid.UUID | None = None,
) -> PageResponse[VideoRead]:
    """List videos with optional batch_id filter."""
    if batch_id:
        page_resp = await crud.get_by_batch_id(batch_id, page=page, page_size=page_size)
    else:
        page_resp = await crud.get_multi(page=page, page_size=page_size)
    page_resp.items = [VideoRead.model_validate(video) for video in page_resp.items]
    return page_resp


@videos_router.get("/export-zip")
@limiter.limit("3/minute")
async def export_selected_videos_zip(
    request: Request,
    crud: VideoCrudDep,
    storage: StorageDep,
    video_ids: list[uuid.UUID] = Query(..., alias="video_id"),
) -> StreamingResponse:
    """Download selected videos as a ZIP file."""
    if not video_ids:
        raise HTTPException(status_code=400, detail="No video IDs provided")

    finished = await crud.get_finished_by_ids(video_ids)
    if not finished:
        raise HTTPException(status_code=400, detail="No finished videos to export")

    def _zip_name(i: int, v: Video) -> str:
        if v.file_name:
            return v.file_name if v.file_name.endswith(".mp4") else f"{v.file_name}.mp4"
        return f"video-{i:03d}-{str(v.id)[:8]}.mp4"

    files = [(_v.output_s3_key, _zip_name(_i, _v)) for _i, _v in enumerate(finished, 1)]
    return storage.build_zip_response(files)


@videos_router.get("/{video_id}", response_model=VideoReadWithShots)
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep) -> VideoReadWithShots:
    """Get a video by ID, including its shots."""
    video = await crud.get_with_shots(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    base = VideoRead.model_validate(video)
    return VideoReadWithShots(**base.model_dump(), shots=video.shots)


@videos_router.patch("/{video_id}", response_model=VideoRead)
async def update_video(
    video_in: VideoUpdate,
    crud: VideoCrudDep,
    video: VideoDep,
) -> VideoRead:
    """Update a video."""
    updated = await crud.update(video.id, video_in)
    return VideoRead.model_validate(updated)


@videos_router.get("/{video_id}/preview")
async def preview_video(video: VideoDep, storage: StorageDep) -> RedirectResponse:
    """Redirect to a fresh presigned URL for video preview."""
    url = storage.generate_presigned_url(video.output_s3_key)
    return RedirectResponse(url=url)


@videos_router.get("/{video_id}/download")
async def download_video(video: VideoDep, storage: StorageDep) -> StreamingResponse:
    """Download a video MP4 file."""
    if video.status != VideoStatus.finished or not video.output_url:
        raise HTTPException(status_code=400, detail="Video not ready for download")

    # Use custom file_name if set, otherwise fallback to ID-based name
    if video.file_name:
        name = (
            video.file_name
            if video.file_name.endswith(".mp4")
            else f"{video.file_name}.mp4"
        )
    else:
        name = f"video-{str(video.id)[:8]}.mp4"

    return StreamingResponse(
        storage.stream_file(video.output_s3_key),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@videos_router.post("/{video_id}/retry", response_model=VideoRead)
async def retry_video(
    video: VideoDep,
    session: SessionDep,
    events: EventServiceDep,
) -> VideoRead:
    """Retry a failed video from the stage that failed.

    Sets status to processing and emits progress events immediately,
    then dispatches the pipeline task in the background.
    """
    if video.status != VideoStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed videos can be retried")

    # Update status immediately so the UI reflects it
    video.status = VideoStatus.processing
    video.error_message = None
    await session.commit()
    await session.refresh(video)

    # Emit SSE events so dashboards update in real-time
    try:
        event = VideoProgressEvent(
            video_id=str(video.id),
            batch_id=str(video.batch_id) if video.batch_id else None,
            status=video.status,
            stage=video.current_stage,
        )
        channel = EventChannel.video.value.format(video_id=video.id)
        await events.emit(channel, event)
        if video.batch_id:
            batch_channel = EventChannel.batch.value.format(batch_id=video.batch_id)
            await events.emit(batch_channel, event)
    except Exception:
        logger.debug("Failed to emit retry event for video %s", video.id)

    # Dispatch the pipeline task
    from api.videos.tasks import retry_video as retry_video_task

    retry_video_task.delay(video_id=str(video.id))
    return VideoRead.model_validate(video)


@videos_router.delete("/{video_id}", status_code=204)
async def delete_video(video: VideoDep, crud: VideoCrudDep) -> None:
    """Delete a video and its shots."""
    await crud.delete(video.id)
