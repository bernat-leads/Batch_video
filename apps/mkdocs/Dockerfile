FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# System dependencies for mkdocs-material imaging
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libfreetype6 \
    libffi-dev \
    libjpeg62-turbo \
    libpng16-16 \
    zlib1g \
    pngquant \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.2.1

RUN addgroup --gid 1000 appuser \
    && adduser --uid 1000 --system --ingroup appuser appuser \
    && mkdir -p /home/appuser && chown appuser:appuser /home/appuser

WORKDIR /home/appuser
ENV PATH="/home/appuser/.venv/bin:$PATH"

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only=main

USER appuser
COPY --chown=appuser . .
RUN chmod +x docker-entrypoint.sh

ENV PORT=8001
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

ENTRYPOINT ["/home/appuser/docker-entrypoint.sh"]
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8001"]
