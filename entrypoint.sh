#!/bin/sh

set -e

echo "=== Backend entrypoint starting ==="

# ── Prometheus multiprocess directory ────────────────────────────────────────
PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus_multiproc_dir}"
export PROMETHEUS_MULTIPROC_DIR
echo "Setting up Prometheus multiprocess directory at $PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

# ── Wait for database ─────────────────────────────────────────────────────────
echo "Waiting for database to be available..."
python /app/wait_for_db.py 60

# ── Database migrations ───────────────────────────────────────────────────────
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then

    if [ ! -f "/app/migrations/env.py" ]; then
        echo ""
        echo "ERROR: /app/migrations/env.py not found."
        echo "The migrations/ folder must be committed to Git and present in the Docker image."
        echo "NEVER run 'flask db init' or 'flask db migrate' in production."
        echo "To skip migrations on this deploy, set the env var: RUN_MIGRATIONS=false"
        echo ""
        exit 1
    fi

    echo "Running: flask db upgrade"
    flask db upgrade
    echo "Migrations applied successfully."

else
    echo "RUN_MIGRATIONS=false — skipping migrations."
fi

# ── Start Gunicorn ────────────────────────────────────────────────────────────
echo "Starting Gunicorn..."
exec gunicorn -c /app/gunicorn.conf.py "app:create_app()"
