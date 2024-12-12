import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.settings import ClinicSettings

def send_email(to_email, subject, body, html_body=None):
    settings = ClinicSettings.get_settings()
    if not settings or not settings.email or not settings.gmail_app_password:
        raise ValueError("Email settings not configured")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = settings.email
    msg['To'] = to_email

    # Add plain text version
    msg.attach(MIMEText(body, 'plain'))

    # Add HTML version if provided
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(settings.email, settings.gmail_app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False 