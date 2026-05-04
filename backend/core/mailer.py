import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Paramètres SMTP (à définir dans le .env ou le dashboard de l'hébergeur)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME or "noreply@hackensae.sn")

def send_email(to_email: str, subject: str, body: str):
    """
    Envoi d'un email réel si les identifiants SMTP sont configurés,
    sinon affiche l'email dans la console pour le développement.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        # Mode développement (simulation)
        separator = "=" * 60
        email_display = f"""
{separator}
📧 SIMULATION D'ENVOI D'EMAIL (Pas d'identifiants SMTP trouvés)
{separator}
À      : {to_email}
Sujet  : {subject}
{separator}
{body}
{separator}
"""
        print(email_display)
        logger.info(f"Email simulé envoyé à {to_email} - Sujet: {subject}")
        return

    # Mode production (envoi réel)
    try:
        msg = MIMEMultipart()
        msg['From'] = f"HackENSAE <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Ajout du corps du message
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Connexion au serveur SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Sécurise la connexion
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Envoi
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email réel envoyé avec succès à {to_email} - Sujet: {subject}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email à {to_email}: {e}")
        print(f"Détails de l'erreur SMTP: {e}")
