# syntax=docker/dockerfile:1
# wrbot - Telegram bot for recurring payments reminders
# Multi-stage build for smaller final image + uv for reproducible deps (from TASK-0020)

FROM python:3.11-slim-bookworm AS builder

# Install uv (pinned for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install only production dependencies using the lockfile (deterministic)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and alembic migrations
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# ---- Final runtime image ----
FROM python:3.11-slim-bookworm

WORKDIR /app

# Create non-root user (good security practice)
RUN groupadd -r appgroup --gid=10001 \
    && useradd -r -g appgroup --uid=10001 --create-home appuser \
    && mkdir -p /app/data /app/logs /app/backups \
    && chown -R appuser:appgroup /app

# Install postgresql-client for pg_dump (Postgres backups, TASK-0033). Small package.
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application code
COPY --from=builder --chown=appuser:appgroup /app/src /app/src
COPY --from=builder --chown=appuser:appgroup /app/alembic /app/alembic
COPY --from=builder --chown=appuser:appgroup /app/alembic.ini /app/alembic.ini

# Make sure we use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Entrypoint handles migrations before starting the bot
COPY --chown=appuser:appgroup docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "wrbot"]
