"""Video API routes."""

import uuid

from fastapi import APIRouter, HTTPException

from api.core.schemas import PageResponse
from api.deps.auth import AuthDep
from api.videos.crud import VideoCrudDep
from api.videos.schemas import (
    DashboardResponse,
    VideoCreate,
    VideoRead,
    VideoReadWithShots,
    VideoUpdate,
)

videos_router = APIRouter(prefix="/videos", tags=["videos"])


@videos_router.get("/stats/dashboard", response_model=DashboardResponse)
async def get_dashboard_stats(crud: VideoCrudDep, _auth: AuthDep) -> DashboardResponse:
    """Get aggregated dashboard statistics."""
    return DashboardResponse(
        stats=await crud.get_dashboard_stats(),
        daily=await crud.get_daily_stats(days=7),
    )


@videos_router.post("/", response_model=VideoRead, status_code=201)
async def create_video(
    video_in: VideoCreate, crud: VideoCrudDep, _auth: AuthDep
) -> VideoRead:
    """Create a new video record."""
    return await crud.create(video_in)


@videos_router.get("/", response_model=PageResponse[VideoRead])
async def list_videos(
    crud: VideoCrudDep,
    _auth: AuthDep,
    page: int = 1,
    page_size: int = 50,
    batch_id: uuid.UUID | None = None,
) -> PageResponse[VideoRead]:
    """List videos with optional batch_id filter."""
    if batch_id:
        return await crud.get_by_batch_id(batch_id, page=page, page_size=page_size)
    return await crud.get_multi(page=page, page_size=page_size)


@videos_router.get("/{video_id}", response_model=VideoReadWithShots)
async def get_video(
    video_id: uuid.UUID, crud: VideoCrudDep, _auth: AuthDep
) -> VideoReadWithShots:
    """Get a video by ID, including its shots."""
    video = await crud.get_with_shots(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    shot_count = len(video.shots) or 1
    result = VideoReadWithShots.model_validate(video)
    result.avg_tokens_per_shot = round(video.tokens_used / shot_count)
    result.avg_generation_time_per_shot_ms = round(
        video.generation_time_ms / shot_count
    )
    return result


@videos_router.patch("/{video_id}", response_model=VideoRead)
async def update_video(
    video_id: uuid.UUID, video_in: VideoUpdate, crud: VideoCrudDep, _auth: AuthDep
) -> VideoRead:
    """Update a video."""
    video = await crud.update(video_id, video_in)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@videos_router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: uuid.UUID, crud: VideoCrudDep, _auth: AuthDep) -> None:
    """Delete a video and its shots."""
    deleted = await crud.delete(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")
