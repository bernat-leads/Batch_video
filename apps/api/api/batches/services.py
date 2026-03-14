"""Business logic services for the batches module."""

from pathlib import PurePosixPath
from typing import Annotated

from fastapi import Depends

from api.batches.crud import BatchCrudDep
from api.batches.schemas import BatchRead
from api.batches.tasks import process_batch
from api.deps.storage import StorageDep

_CONTENT_TYPES: dict[str, str] = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
}


class BatchUploadService:
    """Handles R2 upload, batch record creation, and Celery task dispatch."""

    def __init__(self, crud: BatchCrudDep, storage: StorageDep) -> None:
        self.crud = crud
        self.storage = storage

    async def create_batch(
        self,
        contents: bytes,
        file_name: str,
        batch_name: str,
        column_mapping: dict,
    ) -> BatchRead:
        """Store file in R2, create batch record, and launch background processing."""
        ext = PurePosixPath(file_name).suffix.lower()

        batch = await self.crud.create_from_upload(
            batch_name=batch_name,
            column_mapping=column_mapping,
            file_name=file_name,
            file_key=f"batches/pending{ext}",
        )
        batch_id = batch.id

        file_key = f"batches/{batch_id}/original{ext}"
        self.storage.upload_file(file_key, contents, _CONTENT_TYPES.get(ext, "application/octet-stream"))
        await self.crud.update_file_key(batch_id, file_key)

        process_batch.delay(str(batch_id))

        return await self.crud.get_as_schema(batch_id)


BatchUploadServiceDep = Annotated[BatchUploadService, Depends()]
