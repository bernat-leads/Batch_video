"""Video and Shot API routes."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.core.schemas import PageResponse
from api.deps.auth import AuthDep
from api.deps.db import SessionDep
from api.videos.crud import ShotCrudDep, VideoCrudDep
from api.videos.models.shot import Shot
from api.videos.schemas import (
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


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------


@videos_router.post("/", response_model=VideoRead, status_code=201)
async def create_video(video_in: VideoCreate, crud: VideoCrudDep, _auth: AuthDep):
    """Create a new video record."""
    return await crud.create(video_in)


@videos_router.get("/", response_model=PageResponse[VideoRead])
async def list_videos(crud: VideoCrudDep, _auth: AuthDep, page: int = 1, page_size: int = 50):
    """List videos with pagination."""
    return await crud.get_multi(page=page, page_size=page_size)


@videos_router.get("/{video_id}", response_model=VideoReadWithShots)
async def get_video(video_id: uuid.UUID, crud: VideoCrudDep, _auth: AuthDep):
    """Get a video by ID, including its shots."""
    video = await crud.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@videos_router.patch("/{video_id}", response_model=VideoRead)
async def update_video(video_id: uuid.UUID, video_in: VideoUpdate, crud: VideoCrudDep, _auth: AuthDep):
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
):
    """Create a shot for a video."""
    if not await video_crud.exists(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    return await shot_crud.create(shot_in)


@shots_router.get("/", response_model=list[ShotRead])
async def list_shots(video_id: uuid.UUID, db: SessionDep, _auth: AuthDep):
    """List all shots for a video, ordered by sequence."""
    statement = select(Shot).where(Shot.video_id == video_id).order_by(Shot.order)
    result = await db.execute(statement)
    return list(result.scalars().all())


@shots_router.get("/{shot_id}", response_model=ShotRead)
async def get_shot(video_id: uuid.UUID, shot_id: uuid.UUID, crud: ShotCrudDep, _auth: AuthDep):
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
):
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
