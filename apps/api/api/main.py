"""FastAPI server CLI entry point."""

import logging

import uvicorn

from api.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run FastAPI server with uvicorn."""

    uvicorn.run(
        "api.app:create_application",
        factory=True,
        access_log=True,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.SERVER_LOG_LEVEL,
        reload=settings.SERVER_APP_RELOAD,
    )


if __name__ == "__main__":
    main()
