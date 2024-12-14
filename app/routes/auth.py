from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db
from datetime import datetime, timedelta
from flask import render_template_string
from app.utils.email import send_email
from app.models.settings import ClinicSettings
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))
            
        # Create new user with trial period
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=3)
        
        user = User(
            email=email, 
            username=username,
            trial_start=trial_start,
            trial_end=trial_end,
            is_trial=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send trial period welcome email
        try:
            settings = ClinicSettings.get_settings()
            print(f"Email settings: {settings.email}, App password: {'Set' if settings.gmail_app_password else 'Not Set'}")
            template_path = 'app/templates/emails/trial_welcome.html'
            if not os.path.exists(template_path):
                print(f"Error: Email template not found at {template_path}")
                # Create a basic template if missing
                with open(template_path, 'w') as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <h2>Welcome to {{ settings.clinic_name }}!</h2>
    <p>Dear {{ user.username }},</p>
    <p>Your trial ends on {{ trial_end }}</p>
</body>
</html>""")
            
            with open(template_path, 'r') as file:
                template = file.read()
            
            html_content = render_template_string(
                template,
                user=user,
                trial_end=trial_end.strftime('%B %d, %Y'),
                settings=settings
            )

            text_content = f"""
            Welcome to {settings.clinic_name}!
            
            Your 3-day trial period has started and will end on {trial_end.strftime('%B %d, %Y')}.
            
            During your trial, you'll have access to all features including:
            - Patient Management
            - Appointment Scheduling
            - Prescription Management
            - Billing & Invoicing
            
            Contact us at {settings.email} if you need any assistance.
            
            Thank you for choosing our platform!
            """

            send_email(
                to_email=email,
                subject=f"Welcome to Your Trial - {settings.clinic_name}",
                body=text_content,
                html_body=html_content
            )
        except Exception as e:
            print(f"Failed to send trial welcome email: {str(e)}")
        
        flash('Registration successful! Your 3-day trial period has started.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 