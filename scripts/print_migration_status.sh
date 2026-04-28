#!/bin/sh
# Solo diagnóstico — no hace cambios, no modifica datos, no es destructivo.
# Requiere DATABASE_URL y FLASK_APP configurados.

set -e

echo "=== Migration status ==="
echo ""

echo "--- flask db current ---"
flask db current
echo ""

echo "--- flask db heads ---"
flask db heads
echo ""

echo "--- flask db history ---"
flask db history
