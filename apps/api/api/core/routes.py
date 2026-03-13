"""Core routes - root and health check."""

from fastapi import APIRouter

router = APIRouter(tags=["core"])


@router.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "FastAPI backend is running!", "version": "0.1.0"}


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
