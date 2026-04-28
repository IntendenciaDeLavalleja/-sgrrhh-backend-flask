from flask_mail import Message
from flask import current_app, render_template
from app.extensions import mail
from threading import Thread


def _send_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error al enviar correo: {e}")


def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=_send_async, args=(current_app._get_current_object(), msg)).start()


def send_2fa_email(to_email, code):
    subject = "[RRHH Manager IDL] Código de Verificación"
    html_body = render_template('emails/2fa_code.html', code=code)
    send_email(
        subject=subject,
        recipients=[to_email],
        text_body=f"Tu código de verificación es: {code}. Expira en 10 minutos.",
        html_body=html_body,
    )
