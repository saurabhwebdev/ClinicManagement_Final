from flask import Blueprint, render_template, request, flash, redirect, url_for, render_template_string
from flask_login import login_required
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.settings import ClinicSettings
from app import db
from datetime import datetime, date, time
from app.utils.email import send_email

appointment_bp = Blueprint('appointment', __name__, url_prefix='/appointments')

@appointment_bp.route('/')
@login_required
def appointments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    date_filter = request.args.get('date')
    search = request.args.get('search', '')

    query = Appointment.query

    # Apply filters
    if status:
        query = query.filter(Appointment.status == status)
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(Appointment.date == filter_date)
    if search:
        query = query.join(Appointment.patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%'),
                Appointment.appointment_number.ilike(f'%{search}%')
            )
        )

    # Default ordering: upcoming appointments first, then by date and time
    query = query.order_by(
        Appointment.date >= date.today(),
        Appointment.date,
        Appointment.time
    )

    appointments = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('dashboard/appointments/index.html',
                         appointments=appointments,
                         status=status,
                         date_filter=date_filter,
                         search=search)

@appointment_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    patients = Patient.query.order_by(Patient.first_name).all()
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        appointment_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        appointment_time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        
        appointment = Appointment(
            appointment_number=Appointment.generate_appointment_number(),
            patient_id=patient_id,
            date=appointment_date,
            time=appointment_time,
            duration=int(request.form.get('duration', 30)),
            reason=request.form.get('reason'),
            notes=request.form.get('notes')
        )
        
        db.session.add(appointment)
        db.session.commit()

        # Send appointment confirmation email
        patient = Patient.query.get(patient_id)
        if patient.email:
            try:
                settings = ClinicSettings.get_settings()
                with open('app/templates/emails/appointment_confirmation.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    appointment=appointment,
                    patient=patient,
                    settings=settings
                )

                text_content = f"""
                Dear {patient.full_name},

                Your appointment has been scheduled at {settings.clinic_name}.

                Appointment Details:
                Date: {appointment.date.strftime('%B %d, %Y')}
                Time: {appointment.time.strftime('%I:%M %p')}
                Duration: {appointment.duration} minutes
                Doctor: {settings.doctor_name}

                Please arrive 10 minutes before your scheduled time.

                For any queries:
                Phone: {settings.country_code} {settings.phone}
                Email: {settings.email}

                Thank you for choosing {settings.clinic_name}
                """

                send_email(
                    to_email=patient.email,
                    subject=f"Appointment Confirmation - {settings.clinic_name}",
                    body=text_content,
                    html_body=html_content
                )
                flash('Appointment scheduled and confirmation email sent!', 'success')
            except Exception as e:
                flash('Appointment scheduled but failed to send confirmation email.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Appointment scheduled successfully!', 'success')
            
        return redirect(url_for('appointment.appointments'))
        
    return render_template('dashboard/appointments/new.html', patients=patients)

@appointment_bp.route('/<int:id>')
@login_required
def view_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    return render_template('dashboard/appointments/view.html', appointment=appointment)

@appointment_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    patients = Patient.query.order_by(Patient.first_name).all()
    
    if request.method == 'POST':
        old_status = appointment.status
        old_date = appointment.date
        old_time = appointment.time

        # Track changes for email notification
        changes = {}
        
        # Update appointment
        appointment.patient_id = request.form.get('patient_id')
        appointment.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        appointment.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        appointment.duration = int(request.form.get('duration', 30))
        appointment.status = request.form.get('status')
        appointment.reason = request.form.get('reason')
        appointment.notes = request.form.get('notes')

        # Check what changed
        if old_date != appointment.date:
            changes['Date'] = {
                'old': old_date.strftime('%B %d, %Y'),
                'new': appointment.date.strftime('%B %d, %Y')
            }
        if old_time != appointment.time:
            changes['Time'] = {
                'old': old_time.strftime('%I:%M %p'),
                'new': appointment.time.strftime('%I:%M %p')
            }
        if old_status != appointment.status:
            changes['Status'] = {'old': old_status, 'new': appointment.status}

        db.session.commit()

        # Send email notification if there are changes
        if changes and appointment.patient.email:
            try:
                settings = ClinicSettings.get_settings()
                with open('app/templates/emails/appointment_update.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    appointment=appointment,
                    settings=settings,
                    changes=changes
                )

                text_content = f"""
                Dear {appointment.patient.full_name},

                Your appointment at {settings.clinic_name} has been updated.

                Changes made:
                """
                for field, values in changes.items():
                    text_content += f"\n{field}: {values['old']} → {values['new']}"

                send_email(
                    to_email=appointment.patient.email,
                    subject=f"Appointment Update - {settings.clinic_name}",
                    body=text_content,
                    html_body=html_content
                )
                flash('Appointment updated and notification email sent!', 'success')
            except Exception as e:
                flash('Appointment updated but failed to send notification email.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Appointment updated successfully!', 'success')
            
        return redirect(url_for('appointment.view_appointment', id=appointment.id))
        
    return render_template('dashboard/appointments/edit.html',
                         appointment=appointment,
                         patients=patients)

@appointment_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'cancelled'
    
    # Send cancellation email
    if appointment.patient.email:
        try:
            settings = ClinicSettings.get_settings()
            with open('app/templates/emails/appointment_cancellation.html', 'r') as file:
                template = file.read()
            
            html_content = render_template_string(
                template,
                appointment=appointment,
                patient=appointment.patient,
                settings=settings
            )

            text_content = f"""
            Dear {appointment.patient.full_name},

            Your appointment scheduled for {appointment.date.strftime('%B %d, %Y')} at {appointment.time.strftime('%I:%M %p')} has been cancelled.

            If you would like to reschedule, please contact us:
            Phone: {settings.country_code} {settings.phone}
            Email: {settings.email}

            Thank you for choosing {settings.clinic_name}
            """

            send_email(
                to_email=appointment.patient.email,
                subject=f"Appointment Cancellation - {settings.clinic_name}",
                body=text_content,
                html_body=html_content
            )
            flash('Appointment cancelled and notification email sent!', 'success')
        except Exception as e:
            flash('Appointment cancelled but failed to send notification email.', 'warning')
            print(f"Email error: {str(e)}")
    else:
        flash('Appointment cancelled successfully!', 'success')

    db.session.commit()
    return redirect(url_for('appointment.appointments')) 