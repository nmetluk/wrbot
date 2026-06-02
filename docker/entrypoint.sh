#!/bin/sh
# docker/entrypoint.sh
# Runs database migrations (idempotent) then starts the bot.
# Designed to work with both SQLite and PostgreSQL via $DATABASE_URL from .env (UPPERCASE convention).

set -e

echo "=== wrbot container starting ==="
echo "Database URL (sanitized): $(echo "${DATABASE_URL:-not set}" | sed 's#:[^@]*@#://***@#')"

# Run migrations before starting the application.
# This must succeed or the container should fail to start.
echo "Running alembic migrations..."
alembic upgrade head

echo "Migrations completed successfully."

# Hand over to the main application
echo "Starting wrbot..."
exec python -m wrbot "$@"
