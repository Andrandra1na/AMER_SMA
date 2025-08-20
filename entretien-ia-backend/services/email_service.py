from flask_mail import Message
from extensions import mail
from flask import current_app, render_template

def send_password_reset_email(user, token):
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/reset-password/{token}"
    
    msg = Message(
        subject="Réinitialisation de votre mot de passe - Entretien-IA",
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template(
        'reset_password_email.html',
        user_nom=user.nom,
        reset_url=reset_url
    )
    
    try:
        mail.send(msg)
        print(f"E-mail de réinitialisation envoyé avec succès à {user.email}")
    except Exception as e:
        print(f"ERREUR lors de l'envoi de l'e-mail à {user.email}: {e}")