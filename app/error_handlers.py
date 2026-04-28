from flask import current_app, jsonify, render_template, request, g
from werkzeug.exceptions import HTTPException

from .extensions import db


def _request_id() -> str:
    return getattr(g, "request_id", "unknown")


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if _is_api_request():
            return jsonify(
                {
                    "error": error.name,
                    "message": error.description,
                    "request_id": _request_id(),
                }
            ), error.code

        return (
            render_template(
                "errors/http_error.html",
                status_code=error.code,
                title=error.name,
                message=error.description,
                request_id=_request_id(),
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        # Siempre rollback ante error inesperado para dejar limpia la sesión.
        try:
            db.session.rollback()
        except Exception:
            pass

        current_app.logger.exception(
            "Unhandled exception | request_id=%s | method=%s | path=%s",
            _request_id(),
            request.method,
            request.path,
        )

        if _is_api_request():
            return jsonify(
                {
                    "error": "internal_server_error",
                    "message": (
                        "Ha ocurrido un error inesperado. Intente nuevamente."
                    ),
                    "request_id": _request_id(),
                }
            ), 500

        return (
            render_template(
                "errors/500.html",
                request_id=_request_id(),
            ),
            500,
        )
