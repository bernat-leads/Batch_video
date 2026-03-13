"""Celery worker CLI entry point."""

from worker.app import celery_app


def main() -> None:
    """Run Celery worker."""
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "--pool=solo",
            "--events",
        ]
    )


if __name__ == "__main__":
    main()
