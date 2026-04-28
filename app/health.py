from flask import Blueprint, jsonify
from app.extensions import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health():
    """Liveness probe — solo confirma que Gunicorn está vivo. No consulta la BD."""
    return jsonify({'status': 'ok'}), 200


@health_bp.route('/ready', methods=['GET'])
def ready():
    """Readiness probe — verifica conectividad con la base de datos.
    Usar para diagnóstico manual. NO usar como healthcheck de Coolify."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready', 'db': 'ok'}), 200
    except Exception as exc:
        return jsonify({'status': 'not ready', 'db': str(exc)}), 503
