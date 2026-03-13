"""FastAPI application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from agents.checkpointer import init_checkpointer
from api.agents.routes import router as agent_router
from api.core import router as core_router
from api.deps.sentry import init_sentry
from api.exceptions import register_exception_handlers
from api.items import router as items_router
from api.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Async startup/shutdown for the application."""
    init_sentry()
    await init_checkpointer()
    yield


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        swagger_ui_init_oauth=settings.swagger_ui_init_oauth,
        lifespan=lifespan,
    )

    # TODO: Restrict CORS in production to specific origins instead of allowing all
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(core_router)
    app.include_router(agent_router)

    API_V1_STR: str = "/api/v1"

    app.include_router(items_router, prefix=API_V1_STR)

    return app
