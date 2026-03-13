"""AppSettings CRUD with singleton pattern."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from api.deps.db import SessionDep, save
from api.settings_module.models.app_settings import AppSettings
from api.settings_module.schemas import AppSettingsUpdate


class AppSettingsCrud:
    """CRUD for singleton app settings."""

    def __init__(self, session: SessionDep) -> None:
        self.db_session = session

    async def get(self) -> AppSettings:
        """Get the singleton settings row, creating defaults if none exists."""
        stmt = select(AppSettings).limit(1)
        result = await self.db_session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = AppSettings()
            await save(self.db_session, settings)
        return settings

    async def update(self, obj_in: AppSettingsUpdate) -> AppSettings:
        """Update settings (upsert)."""
        settings = await self.get()
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        await save(self.db_session, settings)
        return settings


AppSettingsCrudDep = Annotated[AppSettingsCrud, Depends()]
