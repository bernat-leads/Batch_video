"""Development entry point — runs FastAPI and Celery worker concurrently."""

import subprocess
import sys


def main() -> None:
    """Start both FastAPI server and Celery worker in parallel."""
    api_cmd = [sys.executable, "-m", "api.main"]
    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "api.deps.celery:celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=1",
        "--pool=solo",
        "--events",
    ]

    procs: list[subprocess.Popen] = []
    try:
        procs.append(subprocess.Popen(api_cmd))
        procs.append(subprocess.Popen(worker_cmd))

        # Wait for either process to exit
        for proc in procs:
            proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            proc.wait()


if __name__ == "__main__":
    main()
