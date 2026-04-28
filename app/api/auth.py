from datetime import datetime, timedelta

from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
import secrets

from app.models.user import AdminUser, TwoFactorCode
from app.services.email_service import send_2fa_email
from app.extensions import db, limiter
from app.utils.logging_helper import log_activity
from . import api_bp


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """Login paso 1: valida credenciales y envía código 2FA."""
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Correo electrónico y contraseña requeridos"}), 400

    user = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        log_activity("API_LOGIN_FAIL", f"Intento de login fallido: {email}")
        return jsonify({"error": "Correo electrónico o contraseña inválidos"}), 401

    # Invalidar códigos anteriores sin usar
    TwoFactorCode.query.filter_by(user_id=user.id).filter(
        TwoFactorCode.consumed_at.is_(None)
    ).delete(synchronize_session=False)

    code = ''.join([secrets.choice('0123456789') for _ in range(6)])
    tf_code = TwoFactorCode(user_id=user.id, code=code)
    db.session.add(tf_code)
    db.session.commit()

    try:
        send_2fa_email(user.email, code)
    except Exception as exc:
        current_app.logger.error(f"2FA email failed for {email}: {exc}")

    # Token pendiente de 2FA — tipo especial, expira en 10 minutos
    pending_token = create_access_token(
        identity=str(user.id),
        additional_claims={"type": "2fa_pending"},
        expires_delta=timedelta(minutes=10),
    )

    log_activity("API_LOGIN_STEP1_SUCCESS", f"Credenciales válidas. 2FA enviado a {user.email}", user)

    return jsonify({
        "requires_2fa": True,
        "pending_token": pending_token,
        "email_preview": f"{user.email[:3]}...{user.email[-4:]}",
    }), 200


@api_bp.route('/auth/verify-2fa', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def api_verify_2fa():
    """Login paso 2: verifica el código 2FA y devuelve JWT de acceso válido por 24h."""
    claims = get_jwt()
    if claims.get("type") != "2fa_pending":
        return jsonify({"error": "Token inválido para este endpoint."}), 403

    user_id = int(get_jwt_identity())

    body = request.get_json(silent=True) or {}
    code = (body.get("code") or "").strip()

    if not code:
        return jsonify({"error": "Código de verificación requerido"}), 400

    tf_code = TwoFactorCode.query.filter_by(user_id=user_id).filter(
        TwoFactorCode.consumed_at.is_(None)
    ).order_by(TwoFactorCode.id.desc()).first()

    if not tf_code or not tf_code.verify_code(code):
        log_activity("API_LOGIN_2FA_FAIL", f"Código 2FA incorrecto para usuario ID: {user_id}")
        return jsonify({"error": "Código inválido o expirado"}), 401

    tf_code.consumed_at = datetime.utcnow()

    user = AdminUser.query.get(user_id)

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "type": "access",
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
        },
        expires_delta=timedelta(hours=24),
    )

    db.session.commit()

    log_activity("API_LOGIN_2FA_SUCCESS", "Sesión JWT iniciada (24h).", user)

    return jsonify({
        "success": True,
        "message": "Sesión iniciada correctamente",
        "access_token": access_token,
        "expires_in": 86400,
        "user": {
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
        },
    }), 200
