from flask import jsonify, request, current_app
from app.models.user import AdminUser, TwoFactorCode
from app.services.email_service import send_2fa_email
from app.extensions import db, limiter
from app.utils.logging_helper import log_activity
from flask_jwt_extended import create_access_token
import secrets
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from . import api_bp

# ---------------------------------------------------------------------------
# HMAC token para el paso 2FA — stateless, sin sesión Flask.
# Formato: "{user_id}:{timestamp}:{hmac_sha256}"
# ---------------------------------------------------------------------------

def _hmac_sign(payload: str) -> str:
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    sig = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def _hmac_verify(token: str, max_age: int) -> "str | None":
    """Verifica firma y expiración. Devuelve el payload o None si inválido."""
    try:
        *parts, received_sig = token.split(':')
        payload = ':'.join(parts)
        secret = current_app.config['SECRET_KEY'].encode('utf-8')
        expected_sig = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received_sig, expected_sig):
            return None
        timestamp = int(parts[-1])
        if int(time.time()) - timestamp > max_age:
            return None
        return payload
    except (ValueError, TypeError, IndexError):
        return None


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """Login paso 1: valida credenciales y envía código 2FA."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos JSON"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Correo electrónico y contraseña requeridos"}), 400

    user = AdminUser.query.filter_by(email=email).first()

    if user and user.check_password(password):
        pending_token = _hmac_sign(f"{user.id}:{int(time.time())}")

        code = ''.join([secrets.choice('0123456789') for _ in range(6)])

        tf_code = TwoFactorCode(user_id=user.id, code=code)
        db.session.add(tf_code)
        db.session.commit()

        send_2fa_email(user.email, code)

        log_activity("API_LOGIN_STEP1_SUCCESS", f"Credenciales válidas. 2FA enviado a {user.email}", user)
        return jsonify({
            "success": True,
            "message": "Código 2FA enviado al correo institucional",
            "email_preview": f"{user.email[:3]}...{user.email[-4:]}",
            "pending_token": pending_token,
        }), 200

    log_activity("API_LOGIN_FAIL", f"Intento de login fallido: {email}")
    return jsonify({"success": False, "error": "Correo electrónico o contraseña inválidos"}), 401


@api_bp.route('/auth/verify-2fa', methods=['POST'])
@limiter.limit("10 per minute")
def api_verify_2fa():
    """Login paso 2: verifica el código 2FA y devuelve JWT válido por 24h."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos JSON"}), 400

    code = data.get('code', '').strip()
    pending_token = data.get('pending_token', '')

    if not code:
        return jsonify({"error": "Código de verificación requerido"}), 400

    # Verificar token pendiente de 2FA (expira en 10 minutos)
    payload = _hmac_verify(pending_token, max_age=600)
    if payload is None:
        return jsonify({"error": "Sesión expirada o inválida"}), 401

    try:
        user_id_str, _ts = payload.split(':')
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Token inválido"}), 401

    user = AdminUser.query.get(user_id)

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    tf_code = TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None)\
        .order_by(TwoFactorCode.created_at.desc()).first()

    if tf_code and tf_code.verify_code(code):
        tf_code.consumed_at = datetime.utcnow()
        db.session.commit()

        # JWT válido por 24 horas
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
            expires_delta=timedelta(hours=24)
        )

        log_activity("API_LOGIN_2FA_SUCCESS", "Sesión JWT iniciada (24h).", user)

        return jsonify({
            "success": True,
            "message": "Sesión iniciada correctamente",
            "access_token": access_token,
            "expires_in": 86400,
            "user": {
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser
            }
        }), 200

    log_activity("API_LOGIN_2FA_FAIL", f"Código 2FA incorrecto para usuario ID: {user_id}", user)
    return jsonify({"success": False, "error": "Código inválido o expirado"}), 400
