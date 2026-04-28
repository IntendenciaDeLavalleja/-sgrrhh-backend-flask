#!/bin/sh
set -eu

echo "=== Backend entrypoint starting ==="

# ── Prometheus multiprocess directory ────────────────────────────────────────
export PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus_multiproc_dir}"
echo "Setting up Prometheus multiprocess directory at $PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*

# ── Wait for database ─────────────────────────────────────────────────────────
if [ "${WAIT_FOR_DB:-true}" = "true" ]; then
    echo "Waiting for database to be available..."

    python3 - <<'PY'
import os, socket, sys, time
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI", "")
if not url:
    print("ERROR: DATABASE_URL is not set.")
    sys.exit(1)

parsed = urlparse(url)
host   = parsed.hostname
port   = parsed.port or 3306

if not host:
    print("ERROR: Could not parse database host from DATABASE_URL.")
    sys.exit(1)

timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))
start   = time.time()

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            waited = int(time.time() - start)
            print(f"Database {host}:{port} is ready (waited {waited}s).")
            break
    except OSError as exc:
        waited = int(time.time() - start)
        if waited >= timeout:
            print(f"ERROR: Database {host}:{port} not available after {timeout}s: {exc}")
            sys.exit(1)
        print(f"  Waiting for {host}:{port} ({waited}s/{timeout}s)...", flush=True)
        time.sleep(2)
PY

else
    echo "WAIT_FOR_DB=false, skipping database wait."
fi

# ── Database migrations ───────────────────────────────────────────────────────
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "RUN_MIGRATIONS=true, running database migrations..."

    if [ ! -f "/app/migrations/env.py" ]; then
        echo ""
        echo "ERROR: RUN_MIGRATIONS=true but /app/migrations/env.py was not found."
        echo "The migrations/ folder must be committed to Git and present in the Docker image."
        echo "For normal Coolify deploys, leave RUN_MIGRATIONS=false (the default)."
        echo ""
        exit 1
    fi

    flask db upgrade
    echo "Database migrations completed."
else
    echo "RUN_MIGRATIONS=false, skipping database migrations during normal app boot."
fi

# ── Start Gunicorn ────────────────────────────────────────────────────────────
echo "Starting Gunicorn..."
exec gunicorn -c /app/gunicorn.conf.py "${APP_MODULE:-app:create_app()}"
