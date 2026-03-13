#!/usr/bin/env bash
set -e

# ── Functions ─────────────────────────────────────────────────────────────────

migrate() {
  echo "Running database migrations..."
  alembic upgrade head
}

start() {
  echo "Starting FastAPI server..."
  exec poetry run start
}

celery_worker() {
  echo "Starting Celery worker..."
  exec poetry run celery-worker
}

voice_worker() {
  echo "Starting voice worker..."
  exec poetry run voice-worker start
}

# ── Command dispatch ──────────────────────────────────────────────────────────

case "${1:-start}" in
  migrate)       migrate ;;
  start)         migrate && start ;;
  celery-worker) celery_worker ;;
  voice-worker)  voice_worker ;;
  *)
    echo "Unknown command: $1"
    echo "Usage: docker-entrypoint.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start          Run migrations + start FastAPI server (default)"
    echo "  migrate        Run database migrations only"
    echo "  celery-worker  Start Celery background worker"
    echo "  voice-worker   Start LiveKit voice worker"
    exit 1
    ;;
esac
