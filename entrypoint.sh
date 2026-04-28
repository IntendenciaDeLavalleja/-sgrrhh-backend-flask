#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Clean and create Prometheus multiprocess directory
echo "Setting up Prometheus multiprocess directory at $PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

# Generate migrations from scratch if not yet initialized (fresh deploy)
# If the container restarts without recreation, migrations/ already exists
# and flask db upgrade becomes a safe no-op (already at head).
if [ ! -d "migrations" ]; then
    echo "Initializing fresh migration environment from models..."
    flask db init
    flask db migrate -m "initial_schema"
fi

# Apply any pending migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn -c /app/gunicorn.conf.py "app:create_app()"
