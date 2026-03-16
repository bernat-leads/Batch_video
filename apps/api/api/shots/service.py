"""Shot service — create and persist individual shots."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.shots.models.shot import Shot
from api.storage import StorageService
from api.videos.pipeline.image_generation import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageGenResult
from api.videos.pipeline.segmentation.schemas import SegmentWithTiming

logger = logging.getLogger(__name__)


class ShotService:
    """Creates shot records and persists generated images to R2.

    Image generation is handled externally (by the caller) to allow
    parallel execution without concurrent session access.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        image_gen: ImageGenService,
    ) -> None:
        self._session = session
        self._storage = storage
        self.image_gen = image_gen

    async def create_shot_with_image(
        self,
        video_id: uuid.UUID,
        segment: SegmentWithTiming,
        image_result: ImageGenResult,
    ) -> Shot:
        """Create a shot record, upload the pre-generated image, and flush.

        This method is designed to be called sequentially — one shot at a time —
        because AsyncSession does not support concurrent flush operations.
        """
        shot = Shot(
            video_id=video_id,
            order=segment.order,
            text=segment.text,
            image_prompt=segment.image_prompt,
            ken_burns_config=segment.ken_burns_config.model_dump(),
            start_time=segment.start_time,
            end_time=segment.end_time,
        )
        self._session.add(shot)
        await self._session.flush()

        r2_key = f"videos/{video_id}/shots/{segment.order:03d}.png"
        try:
            self._storage.upload_file(
                r2_key, image_result.image_bytes, image_result.content_type
            )
        except Exception:
            logger.exception(
                "Shot %s (video %s): R2 upload failed for %s", shot.id, video_id, r2_key
            )
            raise

        shot.image_url = r2_key
        shot.cost_usd = image_result.cost.cost_usd

        return shot
