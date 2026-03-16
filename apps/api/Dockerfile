FROM python:3.12-slim-bookworm

# Environment
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_INSTALLER_MAX_WORKERS=1

# System dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry as root
RUN pip install --no-cache-dir poetry==2.2.1

# Create user and app dir
RUN addgroup --gid 1000 appuser \
    && adduser --uid 1000 --system --ingroup appuser appuser \
    && mkdir -p /home/appuser && chown appuser:appuser /home/appuser \
    && mkdir -p /data/uploads && chown appuser:appuser /data/uploads

WORKDIR /home/appuser
ENV PATH="/home/appuser/.venv/bin:$PATH"

# Copy dependency manifests first for better layer caching
COPY apps/api/pyproject.toml apps/api/poetry.lock ./

# Install dependencies as root
RUN poetry install --only=main -v

# Hand over to app user
USER appuser

# Copy the app
COPY --chown=appuser apps/api/ .

RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/home/appuser/docker-entrypoint.sh"]
CMD ["start"]
