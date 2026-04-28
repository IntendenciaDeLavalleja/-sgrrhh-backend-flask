#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Clean and create Prometheus multiprocess directory
echo "Setting up Prometheus multiprocess directory at $PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn -c /app/gunicorn.conf.py "app:create_app()"
