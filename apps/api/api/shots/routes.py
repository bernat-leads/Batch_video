"""Shot API routes."""

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.deps.auth import AuthDep
from api.deps.storage import S3ClientDep
from api.shots.crud import ShotCrudDep
from api.shots.schemas import ShotCreate, ShotRead, ShotUpdate
from api.storage import StorageService
from api.videos.crud import VideoCrudDep
from api.videos.models.video import Video

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
    video_id: uuid.UUID, crud: ShotCrudDep, _auth: AuthDep
) -> list[ShotRead]:
    """List all shots for a video, ordered by sequence."""
    return await crud.get_by_video(video_id)


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


@shots_router.get("/{shot_order}/preview")
async def preview_shot(
    video_id: uuid.UUID, shot_order: int, s3: S3ClientDep, _auth: AuthDep
) -> RedirectResponse:
    """Redirect to a fresh presigned URL for shot image preview."""
    storage = StorageService(s3)
    url = storage.generate_presigned_url(Video.build_shot_s3_key(video_id, shot_order))
    return RedirectResponse(url=url)
