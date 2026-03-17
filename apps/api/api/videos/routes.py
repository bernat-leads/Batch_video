"""Video API routes."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse, Response, StreamingResponse

from api.core.schemas import PageResponse
from api.deps.auth import get_current_session
from api.rate_limit import limiter
from api.storage import StorageDep
from api.videos.crud import VideoCrud, VideoCrudDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import (
    VideoCreate,
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
    page: int = 1,
    page_size: int = 50,
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

    finished = []
    for video_id in video_ids:
        video = await crud.get(video_id)
        if video and video.status == VideoStatus.finished and video.output_url:
            finished.append(video)

    if not finished:
        raise HTTPException(status_code=400, detail="No finished videos to export")

    files = [
        (f"videos/{video.id}/output.mp4", f"video-{index:03d}-{str(video.id)[:8]}.mp4")
        for index, video in enumerate(finished, 1)
    ]

    return StreamingResponse(
        storage.stream_zip(files),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="videos.zip"'},
    )


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
async def preview_video(video_id: uuid.UUID, storage: StorageDep) -> RedirectResponse:
    """Redirect to a fresh presigned URL for video preview."""
    s3_key = f"videos/{video_id}/output.mp4"
    url = storage.generate_presigned_url(s3_key)
    return RedirectResponse(url=url)


@videos_router.get("/{video_id}/download")
async def download_video(video: VideoDep, storage: StorageDep) -> StreamingResponse:
    """Download a video MP4 file."""
    if video.status != VideoStatus.finished or not video.output_url:
        raise HTTPException(status_code=400, detail="Video not ready for download")

    s3_key = f"videos/{video.id}/output.mp4"
    return StreamingResponse(
        storage.stream_file(s3_key),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="video-{str(video.id)[:8]}.mp4"'
        },
    )


@videos_router.delete("/{video_id}", status_code=204)
async def delete_video(video: VideoDep, crud: VideoCrudDep) -> None:
    """Delete a video and its shots."""
    await crud.delete(video.id)
