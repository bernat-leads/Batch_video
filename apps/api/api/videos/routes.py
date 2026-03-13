"""Video, Shot, and Batch API routes."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.core.schemas import PageResponse
from api.deps.auth import AuthDep
from api.deps.db import SessionDep
from api.videos.crud import BatchCrudDep, ShotCrudDep, VideoCrudDep
from api.videos.models.shot import Shot
from api.videos.schemas import (
    BatchCreate,
    BatchRead,
    DailyStats,
    DashboardResponse,
    DashboardStats,
    ShotCreate,
    ShotRead,
    ShotUpdate,
    VideoCreate,
    VideoRead,
    VideoReadWithShots,
    VideoUpdate,
)

videos_router = APIRouter(prefix="/videos", tags=["videos"])
shots_router = APIRouter(prefix="/videos/{video_id}/shots", tags=["shots"])
batches_router = APIRouter(prefix="/batches", tags=["batches"])


# ---------------------------------------------------------------------------
# Batches
# ---------------------------------------------------------------------------


@batches_router.post("/", response_model=BatchRead, status_code=201)
async def create_batch(
    batch_in: BatchCreate, crud: BatchCrudDep, _auth: AuthDep
) -> BatchRead:
    """Create a new batch with videos."""
    return await crud.create_with_videos(batch_in)


@batches_router.get("/", response_model=PageResponse[BatchRead])
async def list_batches(
    crud: BatchCrudDep,
    _auth: AuthDep,
    page: int = 1,
    page_size: int = 50,
) -> PageResponse[BatchRead]:
    """List batches with computed video stats (paginated)."""
    return await crud.get_all_with_stats(page=page, page_size=page_size)


@batches_router.get("/{batch_id}", response_model=BatchRead)
async def get_batch(
    batch_id: uuid.UUID, crud: BatchCrudDep, _auth: AuthDep
) -> BatchRead:
    """Get a batch by ID with computed video stats."""
    batch = await crud.get_with_stats(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@batches_router.delete("/{batch_id}", status_code=204)
async def delete_batch(batch_id: uuid.UUID, crud: BatchCrudDep, _auth: AuthDep) -> None:
    """Delete a batch and all its videos."""
    deleted = await crud.delete(batch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Batch not found")


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------


@videos_router.get("/stats/dashboard", response_model=DashboardResponse)
async def get_dashboard_stats(crud: VideoCrudDep, _auth: AuthDep) -> DashboardResponse:
    """Get aggregated dashboard statistics."""
    stats = await crud.get_dashboard_stats()
    daily = await crud.get_daily_stats(days=7)
    return DashboardResponse(
        stats=DashboardStats(**stats),
        daily=[DailyStats(**d) for d in daily],
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


# ---------------------------------------------------------------------------
# Shots
# ---------------------------------------------------------------------------


@shots_router.post("/", response_model=ShotRead, status_code=201)
async def create_shot(
    video_id: uuid.UUID,
    shot_in: ShotCreate,
    video_crud: VideoCrudDep,
    shot_crud: ShotCrudDep,
    _auth: AuthDep,
) -> ShotRead:
    """Create a shot for a video."""
    if not await video_crud.exists(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    return await shot_crud.create(shot_in)


@shots_router.get("/", response_model=list[ShotRead])
async def list_shots(
    video_id: uuid.UUID, db: SessionDep, _auth: AuthDep
) -> list[ShotRead]:
    """List all shots for a video, ordered by sequence."""
    statement = select(Shot).where(Shot.video_id == video_id).order_by(Shot.order)
    result = await db.execute(statement)
    return list(result.scalars().all())


@shots_router.get("/{shot_id}", response_model=ShotRead)
async def get_shot(
    video_id: uuid.UUID, shot_id: uuid.UUID, crud: ShotCrudDep, _auth: AuthDep
) -> ShotRead:
    """Get a specific shot."""
    shot = await crud.get(shot_id)
    if not shot or shot.video_id != video_id:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@shots_router.patch("/{shot_id}", response_model=ShotRead)
async def update_shot(
    video_id: uuid.UUID,
    shot_id: uuid.UUID,
    shot_in: ShotUpdate,
    crud: ShotCrudDep,
    _auth: AuthDep,
) -> ShotRead:
    """Update a shot."""
    shot = await crud.get(shot_id)
    if not shot or shot.video_id != video_id:
        raise HTTPException(status_code=404, detail="Shot not found")
    return await crud.update(shot_id, shot_in)


@shots_router.delete("/{shot_id}", status_code=204)
async def delete_shot(
    video_id: uuid.UUID, shot_id: uuid.UUID, crud: ShotCrudDep, _auth: AuthDep
) -> None:
    """Delete a shot."""
    shot = await crud.get(shot_id)
    if not shot or shot.video_id != video_id:
        raise HTTPException(status_code=404, detail="Shot not found")
    await crud.delete(shot_id)
