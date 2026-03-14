"""Shot API routes."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.deps.auth import AuthDep
from api.deps.db import SessionDep
from api.shots.crud import ShotCrudDep
from api.shots.models.shot import Shot
from api.shots.schemas import ShotCreate, ShotRead, ShotUpdate
from api.videos.crud import VideoCrudDep

shots_router = APIRouter(prefix="/videos/{video_id}/shots", tags=["shots"])


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
