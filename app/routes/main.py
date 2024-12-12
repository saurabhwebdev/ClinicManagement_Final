from flask import Blueprint, render_template, request, flash, redirect, url_for, render_template_string, make_response
from flask_login import login_required
from app.models.settings import ClinicSettings
from app import db
import json
from datetime import datetime, time, date
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.utils.email import send_email
from app.models.invoice import Invoice
from sqlalchemy.sql import func
from sqlalchemy import extract
import pdfkit

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get today's date
    today = date.today()
    
    # Get statistics
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    total_prescriptions = Prescription.query.count()
    total_invoices = Invoice.query.count()
    
    # Today's appointments
    todays_appointments = Appointment.query.filter(
        Appointment.date == today
    ).order_by(Appointment.time).limit(5).all()
    
    # Recent patients
    recent_patients = Patient.query.order_by(
        Patient.created_at.desc()
    ).limit(5).all()
    
    # Pending invoices
    pending_invoices = Invoice.query.filter(
        Invoice.status == 'pending'
    ).order_by(Invoice.due_date).limit(5).all()
    
    # Monthly statistics
    current_month = today.replace(day=1)
    monthly_patients = Patient.query.filter(
        extract('year', Patient.created_at) == today.year,
        extract('month', Patient.created_at) == today.month
    ).count()
    
    monthly_appointments = Appointment.query.filter(
        extract('year', Appointment.date) == today.year,
        extract('month', Appointment.date) == today.month
    ).count()
    
    monthly_revenue = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        extract('year', Invoice.date) == today.year,
        extract('month', Invoice.date) == today.month,
        Invoice.status == 'paid'
    ).scalar() or 0
    
    return render_template('dashboard/dashboard.html',
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         total_prescriptions=total_prescriptions,
                         total_invoices=total_invoices,
                         todays_appointments=todays_appointments,
                         recent_patients=recent_patients,
                         pending_invoices=pending_invoices,
                         monthly_patients=monthly_patients,
                         monthly_appointments=monthly_appointments,
                         monthly_revenue=monthly_revenue,
                         today=today)

@main_bp.route('/patients')
@login_required
def patients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Patient.query
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.registration_number.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%')
            )
        )
    
    patients = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('dashboard/patients/index.html', 
                         patients=patients, 
                         search=search,
                         today=date.today())

@main_bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    if request.method == 'POST':
        patient = Patient(
            registration_number=Patient.generate_registration_number(),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            gender=request.form.get('gender'),
            blood_group=request.form.get('blood_group'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            medical_history=request.form.get('medical_history'),
            allergies=request.form.get('allergies')
        )
        
        db.session.add(patient)
        db.session.commit()

        # Send welcome email if patient has email
        if patient.email:
            try:
                settings = ClinicSettings.get_settings()
                # Read the email template
                with open('app/templates/emails/patient_welcome.html', 'r') as file:
                    template = file.read()
                
                # Render the HTML template with patient and clinic data
                html_content = render_template_string(
                    template,
                    patient=patient,
                    settings=settings
                )

                # Create a simple text version
                text_content = f"""
                Welcome to {settings.clinic_name}!
                
                Your registration details:
                Registration Number: {patient.registration_number}
                Name: {patient.full_name}
                
                For appointments and queries:
                Phone: {settings.country_code} {settings.phone}
                Email: {settings.email}
                
                Thank you for choosing {settings.clinic_name}
                """

                # Send the email
                send_email(
                    to_email=patient.email,
                    subject=f"Welcome to {settings.clinic_name}",
                    body=text_content,
                    html_body=html_content
                )
                flash('Patient added successfully and welcome email sent!', 'success')
            except Exception as e:
                flash('Patient added successfully but failed to send welcome email.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Patient added successfully!', 'success')
            
        return redirect(url_for('main.patients'))
        
    return render_template('dashboard/patients/new.html')

@main_bp.route('/patients/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    return render_template('dashboard/patients/view.html', patient=patient, today=date.today())

@main_bp.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    
    if request.method == 'POST':
        # Track changes
        changes = {}
        fields_to_check = {
            'First Name': ('first_name', request.form.get('first_name')),
            'Last Name': ('last_name', request.form.get('last_name')),
            'Date of Birth': ('date_of_birth', request.form.get('date_of_birth')),
            'Gender': ('gender', request.form.get('gender')),
            'Blood Group': ('blood_group', request.form.get('blood_group')),
            'Phone': ('phone', request.form.get('phone')),
            'Email': ('email', request.form.get('email')),
            'Address': ('address', request.form.get('address')),
            'Medical History': ('medical_history', request.form.get('medical_history')),
            'Allergies': ('allergies', request.form.get('allergies'))
        }

        for label, (field, new_value) in fields_to_check.items():
            old_value = getattr(patient, field)
            if field == 'date_of_birth' and new_value:
                new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
            
            if old_value != new_value and (old_value or new_value):  # Only track if there's a real change
                changes[label] = {
                    'old': old_value if old_value else 'Not specified',
                    'new': new_value if new_value else 'Not specified'
                }
                setattr(patient, field, new_value)

        if changes and patient.email:  # Only send email if there are changes and patient has email
            try:
                settings = ClinicSettings.get_settings()
                with open('app/templates/emails/patient_update.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    patient=patient,
                    settings=settings,
                    changes=changes
                )

                # Create text version
                text_content = f"""
                Dear {patient.full_name},

                Your profile at {settings.clinic_name} has been updated.

                Changes made:
                """
                for field, values in changes.items():
                    text_content += f"\n{field}: {values['old']} → {values['new']}"

                send_email(
                    to_email=patient.email,
                    subject=f"Profile Updated - {settings.clinic_name}",
                    body=text_content,
                    html_body=html_content
                )
            except Exception as e:
                print(f"Failed to send update email: {str(e)}")

        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('main.view_patient', id=patient.id))
        
    return render_template('dashboard/patients/edit.html', patient=patient)

@main_bp.route('/patients/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    
    # Send deletion notification if patient has email
    if patient.email:
        try:
            settings = ClinicSettings.get_settings()
            with open('app/templates/emails/patient_deletion.html', 'r') as file:
                template = file.read()
            
            html_content = render_template_string(
                template,
                patient=patient,
                settings=settings
            )

            text_content = f"""
            Dear {patient.full_name},

            This email confirms that your patient profile at {settings.clinic_name} has been deleted.

            If you didn't request this deletion or have any concerns, please contact us:
            Phone: {settings.country_code} {settings.phone}
            Email: {settings.email}

            Thank you for choosing {settings.clinic_name}
            """

            send_email(
                to_email=patient.email,
                subject=f"Profile Deleted - {settings.clinic_name}",
                body=text_content,
                html_body=html_content
            )
        except Exception as e:
            print(f"Failed to send deletion email: {str(e)}")

    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('main.patients'))

@main_bp.route('/appointments')
@login_required
def appointments():
    # Redirect to the new appointments route
    return redirect(url_for('appointment.appointments'))

@main_bp.route('/prescriptions')
@login_required
def prescriptions():
    return redirect(url_for('prescription.prescriptions'))

@main_bp.route('/invoices')
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    date_filter = request.args.get('date')

    query = Invoice.query

    if search:
        query = query.join(Invoice.patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.registration_number.ilike(f'%{search}%'),
                Invoice.invoice_number.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter(Invoice.status == status)

    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(Invoice.date == filter_date)

    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    settings = ClinicSettings.get_settings()

    return render_template('dashboard/invoices/index.html',
                         invoices=invoices,
                         search=search,
                         status=status,
                         date_filter=date_filter,
                         settings=settings)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings = ClinicSettings.get_settings()
    if not settings:
        settings = ClinicSettings(
            clinic_name="My Clinic",
            doctor_name="Dr. Name",
            country_code='+91',
            currency='INR',
            email="hellocuradent@gmail.com"
        )
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.clinic_name = request.form.get('clinic_name')
        settings.doctor_name = request.form.get('doctor_name')
        settings.email = request.form.get('email')
        settings.phone = request.form.get('phone')
        settings.country_code = request.form.get('country_code')
        settings.address = request.form.get('address')
        settings.currency = request.form.get('currency')
        settings.gmail_app_password = request.form.get('gmail_app_password')
        
        # Convert time strings to time objects
        opening_time = request.form.get('opening_time')
        if opening_time:
            try:
                hour, minute = map(int, opening_time.split(':'))
                settings.opening_time = time(hour, minute)
            except (ValueError, TypeError):
                settings.opening_time = None

        closing_time = request.form.get('closing_time')
        if closing_time:
            try:
                hour, minute = map(int, closing_time.split(':'))
                settings.closing_time = time(hour, minute)
            except (ValueError, TypeError):
                settings.closing_time = None

        settings.working_days = ','.join(request.form.getlist('working_days'))
        settings.registration_number = request.form.get('registration_number')
        settings.tax_id = request.form.get('tax_id')

        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('main.settings'))

    return render_template('dashboard/settings.html', settings=settings) 

@main_bp.route('/reports')
@login_required
def reports():
    return render_template('dashboard/reports/index.html')

@main_bp.route('/reports/patients', methods=['POST'])
@login_required
def generate_patient_report():
    date_range = request.form.get('date_range')
    current_time = datetime.now()
    
    # Query patients based on date range
    query = Patient.query
    if date_range == 'month':
        start_date = date.today().replace(day=1)
        query = query.filter(Patient.created_at >= start_date)
    
    patients = query.order_by(Patient.created_at.desc()).all()
    
    # Generate PDF using the template
    html = render_template('dashboard/reports/patient_report.html',
                         patients=patients,
                         date_range=date_range,
                         clinic_settings=ClinicSettings.get_settings(),
                         now=datetime.now)
    
    pdf = pdfkit.from_string(html, False)
    
    # Create response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=patient_report_{date.today()}.pdf'
    
    return response

@main_bp.route('/reports/appointments', methods=['POST'])
@login_required
def generate_appointment_report():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    
    appointments = Appointment.query.filter(
        Appointment.date.between(start_date, end_date)
    ).order_by(Appointment.date, Appointment.time).all()
    
    html = render_template('dashboard/reports/appointment_report.html',
                         appointments=appointments,
                         start_date=start_date,
                         end_date=end_date,
                         clinic_settings=ClinicSettings.get_settings(),
                         now=datetime.now)
    
    pdf = pdfkit.from_string(html, False)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=appointment_report_{start_date}_to_{end_date}.pdf'
    
    return response

@main_bp.route('/reports/financial', methods=['POST'])
@login_required
def generate_financial_report():
    period = request.form.get('period')
    today = date.today()
    
    if period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarter':
        start_date = today.replace(day=1, month=((today.month-1)//3)*3+1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(day=1, month=1)
        end_date = today
    else:  # custom
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    
    invoices = Invoice.query.filter(
        Invoice.date.between(start_date, end_date)
    ).order_by(Invoice.date).all()
    
    html = render_template('dashboard/reports/financial_report.html',
                         invoices=invoices,
                         start_date=start_date,
                         end_date=end_date,
                         clinic_settings=ClinicSettings.get_settings(),
                         now=datetime.now)
    
    pdf = pdfkit.from_string(html, False)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=financial_report_{start_date}_to_{end_date}.pdf'
    
    return response 