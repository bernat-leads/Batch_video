"""Dashboard API routes."""

from fastapi import APIRouter

from api.dashboard.crud import DashboardCrudDep
from api.dashboard.schemas import DashboardResponse
from api.deps.auth import AuthDep

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    crud: DashboardCrudDep, _auth: AuthDep
) -> DashboardResponse:
    """Get aggregated dashboard statistics."""
    return DashboardResponse(
        stats=await crud.get_stats(),
        daily=await crud.get_daily_stats(days=7),
    )
