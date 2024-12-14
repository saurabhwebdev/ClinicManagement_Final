import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.settings import ClinicSettings

def send_email(to_email, subject, body, html_body=None):
    settings = ClinicSettings.get_settings()
    
    # Add validation checks
    if not settings:
        print("Error: No clinic settings found")
        return False
        
    if not settings.email:
        print("Error: No sender email configured in settings")
        return False
        
    if not settings.gmail_app_password:
        print("Error: No Gmail app password configured in settings")
        return False

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
            server.set_debuglevel(1)  # Enable debug output
            print("Connecting to SMTP server...")
            server.starttls()
            print("Starting TLS...")
            server.login(settings.email, settings.gmail_app_password)
            print("Logged in successfully")
            server.send_message(msg)
            print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        print(f"Attempted to send from: {settings.email}")
        print(f"Sending to: {to_email}")
        return False 