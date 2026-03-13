"""Videos module — bulk video pipeline domain."""

from api.videos.routes import batches_router, shots_router, videos_router

__all__ = ["batches_router", "shots_router", "videos_router"]
