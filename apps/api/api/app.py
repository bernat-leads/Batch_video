"""FastAPI application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from api.auth import auth_router
from api.batches.routes import batches_router
from api.core import router as core_router
from api.dashboard import dashboard_router
from api.deps.sentry import init_sentry
from api.events.routes import events_router
from api.exceptions import register_exception_handlers
from api.rate_limit import limiter
from api.settings import settings
from api.settings_module import settings_router
from api.shots.routes import shots_router
from api.videos.routes import videos_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Async startup/shutdown for the application."""
    init_sentry()
    yield
    from api.deps.redis import shutdown_redis

    await shutdown_redis()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(core_router)

    API_V1_STR: str = "/api/v1"

    app.include_router(auth_router, prefix=API_V1_STR)
    app.include_router(dashboard_router, prefix=API_V1_STR)
    app.include_router(batches_router, prefix=API_V1_STR)
    app.include_router(videos_router, prefix=API_V1_STR)
    app.include_router(shots_router, prefix=API_V1_STR)
    app.include_router(settings_router, prefix=API_V1_STR)
    app.include_router(events_router, prefix=API_V1_STR)

    return app
