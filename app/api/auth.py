from flask import jsonify, request, session
from app.models.user import AdminUser, TwoFactorCode
from app.services.email_service import send_2fa_email
from app.extensions import db, limiter
from app.utils.logging_helper import log_activity
from flask_jwt_extended import create_access_token
import secrets
import random
from datetime import datetime, timedelta
from . import api_bp


def _generate_captcha():
    """Genera un captcha numérico y lo almacena en la sesión."""
    num1 = random.randint(1, 15)
    num2 = random.randint(1, 15)
    session['api_captcha_result'] = num1 + num2
    return f"¿Cuánto es {num1} + {num2}?"


@api_bp.route('/auth/captcha', methods=['GET'])
@limiter.limit("30 per minute")
def api_captcha():
    """Genera y devuelve la pregunta del captcha numérico."""
    question = _generate_captcha()
    return jsonify({"question": question}), 200


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """Login paso 1: valida credenciales + captcha y envía código 2FA."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos JSON"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    captcha_answer = data.get('captcha_answer')

    if not email or not password:
        return jsonify({"error": "Correo electrónico y contraseña requeridos"}), 400

    # Validar captcha
    stored_captcha = session.get('api_captcha_result')
    session.pop('api_captcha_result', None)

    if stored_captcha is None or captcha_answer is None:
        log_activity("API_LOGIN_CAPTCHA_FAIL", f"Captcha ausente para: {email}")
        return jsonify({"error": "Debe completar el captcha"}), 400

    try:
        captcha_answer_int = int(captcha_answer)
    except (ValueError, TypeError):
        log_activity("API_LOGIN_CAPTCHA_FAIL", f"Captcha inválido para: {email}")
        return jsonify({"error": "Respuesta de captcha inválida"}), 400

    if captcha_answer_int != stored_captcha:
        log_activity("API_LOGIN_CAPTCHA_FAIL", f"Captcha incorrecto para: {email}")
        return jsonify({"error": "Captcha incorrecto"}), 400

    user = AdminUser.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session['api_2fa_user_id'] = user.id

        code = ''.join([secrets.choice('0123456789') for _ in range(6)])

        tf_code = TwoFactorCode(user_id=user.id, code=code)
        db.session.add(tf_code)
        db.session.commit()

        send_2fa_email(user.email, code)

        log_activity("API_LOGIN_STEP1_SUCCESS", f"Credenciales válidas. 2FA enviado a {user.email}", user)
        return jsonify({
            "success": True,
            "message": "Código 2FA enviado al correo institucional",
            "email_preview": f"{user.email[:3]}...{user.email[-4:]}"
        }), 200

    log_activity("API_LOGIN_FAIL", f"Intento de login fallido: {email}")
    return jsonify({"success": False, "error": "Correo electrónico o contraseña inválidos"}), 401


@api_bp.route('/auth/verify-2fa', methods=['POST'])
@limiter.limit("10 per minute")
def api_verify_2fa():
    """Login paso 2: verifica el código 2FA y devuelve JWT válido por 24h."""
    if 'api_2fa_user_id' not in session:
        return jsonify({"error": "Sesión expirada o inválida"}), 401

    data = request.get_json()
    code = data.get('code', '').strip() if data else ''

    if not code:
        return jsonify({"error": "Código de verificación requerido"}), 400

    user_id = session.get('api_2fa_user_id')
    user = AdminUser.query.get(user_id)

    if not user:
        session.pop('api_2fa_user_id', None)
        return jsonify({"error": "Usuario no encontrado"}), 404

    tf_code = TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None)\
        .order_by(TwoFactorCode.created_at.desc()).first()

    if tf_code and tf_code.verify_code(code):
        tf_code.consumed_at = datetime.utcnow()
        db.session.commit()
        session.pop('api_2fa_user_id', None)

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
