from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.exceptions import HTTPException

from app.extensions import db

admin_bp = Blueprint('admin', __name__, template_folder='templates')


@admin_bp.errorhandler(Exception)
def handle_admin_exception(error):
    # Dejar pasar errores HTTP conocidos (404, 405, etc.) al handler global.
    if isinstance(error, HTTPException):
        return error

    try:
        db.session.rollback()
    except Exception:
        pass

    request_id = getattr(g, 'request_id', 'unknown')

    current_app.logger.exception(
        "Admin exception | request_id=%s | path=%s",
        request_id,
        request.path,
    )

    # Evitar página 500 cruda en panel admin.
    # Redirigir con código de referencia.
    if request.endpoint != 'admin.dashboard':
        flash(
            f"Ocurrió un error inesperado. Código de referencia: {request_id}",
            'error',
        )
        return redirect(url_for('admin.dashboard'))

    return render_template('errors/500.html', request_id=request_id), 500


from . import routes  # noqa: E402,F401
