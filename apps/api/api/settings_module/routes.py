"""AppSettings API routes."""

from fastapi import APIRouter

from api.deps.auth import AuthDep
from api.settings_module.crud import AppSettingsCrudDep
from api.settings_module.schemas import AppSettingsRead, AppSettingsUpdate

settings_router = APIRouter(prefix="/settings", tags=["settings"])


@settings_router.get("/", response_model=AppSettingsRead)
async def get_settings(crud: AppSettingsCrudDep, _auth: AuthDep) -> AppSettingsRead:
    """Get current app settings."""
    return await crud.get()


@settings_router.put("/", response_model=AppSettingsRead)
async def update_settings(
    settings_in: AppSettingsUpdate, crud: AppSettingsCrudDep, _auth: AuthDep
) -> AppSettingsRead:
    """Update app settings."""
    return await crud.update(settings_in)
