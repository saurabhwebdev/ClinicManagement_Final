from flask import Blueprint, render_template, request, flash, redirect, url_for, render_template_string, send_file
from flask_login import login_required
from app.models.prescription import Prescription, PrescriptionMedicine
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.settings import ClinicSettings
from app import db
from datetime import datetime, date
from app.utils.email import send_email
import pdfkit
import tempfile
import os

# Add this configuration at the top of the file after imports
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

prescription_bp = Blueprint('prescription', __name__, url_prefix='/prescriptions')

@prescription_bp.route('/')
@login_required
def prescriptions():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    date_filter = request.args.get('date')

    query = Prescription.query

    if search:
        query = query.join(Prescription.patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.registration_number.ilike(f'%{search}%'),
                Prescription.prescription_number.ilike(f'%{search}%')
            )
        )
    
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(Prescription.date == filter_date)

    prescriptions = query.order_by(Prescription.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('dashboard/prescriptions/index.html',
                         prescriptions=prescriptions,
                         search=search,
                         date_filter=date_filter)

@prescription_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_prescription():
    patients = Patient.query.order_by(Patient.first_name).all()
    appointments = Appointment.query.filter(
        Appointment.status.in_(['scheduled', 'completed'])
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    if request.method == 'POST':
        prescription = Prescription(
            prescription_number=Prescription.generate_prescription_number(),
            patient_id=request.form.get('patient_id'),
            appointment_id=request.form.get('appointment_id') or None,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            diagnosis=request.form.get('diagnosis'),
            notes=request.form.get('notes')
        )
        
        db.session.add(prescription)

        # Add medicines
        medicine_names = request.form.getlist('medicine_name[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('instructions[]')

        for i in range(len(medicine_names)):
            if medicine_names[i]:  # Only add if medicine name is provided
                medicine = PrescriptionMedicine(
                    medicine_name=medicine_names[i],
                    dosage=dosages[i],
                    frequency=frequencies[i],
                    duration=durations[i],
                    instructions=instructions[i]
                )
                prescription.medicines.append(medicine)

        db.session.commit()

        # Send prescription email
        if prescription.patient.email:
            try:
                settings = ClinicSettings.get_settings()
                with open('app/templates/emails/prescription_created.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    prescription=prescription,
                    patient=prescription.patient,
                    settings=settings
                )

                text_content = f"""
                Dear {prescription.patient.full_name},

                Your prescription from {settings.clinic_name} is ready.
                Prescription Number: {prescription.prescription_number}
                Date: {prescription.date.strftime('%B %d, %Y')}

                Medicines Prescribed:
                """
                for medicine in prescription.medicines:
                    text_content += f"\n- {medicine.medicine_name}"
                    text_content += f"\n  Dosage: {medicine.dosage}"
                    text_content += f"\n  Frequency: {medicine.frequency}"
                    text_content += f"\n  Duration: {medicine.duration}"
                    text_content += f"\n  Instructions: {medicine.instructions}\n"

                send_email(
                    to_email=prescription.patient.email,
                    subject=f"Prescription - {settings.clinic_name}",
                    body=text_content,
                    html_body=html_content
                )
                flash('Prescription created and sent to patient!', 'success')
            except Exception as e:
                flash('Prescription created but failed to send email.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Prescription created successfully!', 'success')
            
        return redirect(url_for('prescription.view_prescription', id=prescription.id))
        
    return render_template('dashboard/prescriptions/new.html',
                         patients=patients,
                         appointments=appointments,
                         today=date.today())

@prescription_bp.route('/<int:id>')
@login_required
def view_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    return render_template('dashboard/prescriptions/view.html', prescription=prescription)

@prescription_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    patients = Patient.query.order_by(Patient.first_name).all()
    appointments = Appointment.query.filter(
        Appointment.status.in_(['scheduled', 'completed'])
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    if request.method == 'POST':
        # Track changes for email notification
        changes = {}
        old_diagnosis = prescription.diagnosis
        old_notes = prescription.notes
        
        prescription.patient_id = request.form.get('patient_id')
        prescription.appointment_id = request.form.get('appointment_id') or None
        prescription.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        prescription.diagnosis = request.form.get('diagnosis')
        prescription.notes = request.form.get('notes')

        # Track changes
        if old_diagnosis != prescription.diagnosis:
            changes['Diagnosis'] = {'old': old_diagnosis, 'new': prescription.diagnosis}
        if old_notes != prescription.notes:
            changes['Notes'] = {'old': old_notes, 'new': prescription.notes}

        # Update medicines
        # First, remove all existing medicines
        for medicine in prescription.medicines:
            db.session.delete(medicine)

        # Add updated medicines
        medicine_names = request.form.getlist('medicine_name[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('instructions[]')

        for i in range(len(medicine_names)):
            if medicine_names[i]:
                medicine = PrescriptionMedicine(
                    medicine_name=medicine_names[i],
                    dosage=dosages[i],
                    frequency=frequencies[i],
                    duration=durations[i],
                    instructions=instructions[i]
                )
                prescription.medicines.append(medicine)

        db.session.commit()

        # Send update email if there are changes
        if prescription.patient.email:
            try:
                settings = ClinicSettings.get_settings()
                with open('app/templates/emails/prescription_update.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    prescription=prescription,
                    patient=prescription.patient,
                    settings=settings,
                    changes=changes
                )

                send_email(
                    to_email=prescription.patient.email,
                    subject=f"Prescription Updated - {settings.clinic_name}",
                    body="Your prescription has been updated. Please check the attached details.",
                    html_body=html_content
                )
                flash('Prescription updated and notification sent!', 'success')
            except Exception as e:
                flash('Prescription updated but failed to send notification.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Prescription updated successfully!', 'success')
            
        return redirect(url_for('prescription.view_prescription', id=prescription.id))
        
    return render_template('dashboard/prescriptions/edit.html',
                         prescription=prescription,
                         patients=patients,
                         appointments=appointments)

@prescription_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    
    if prescription.patient.email:
        try:
            settings = ClinicSettings.get_settings()
            with open('app/templates/emails/prescription_deletion.html', 'r') as file:
                template = file.read()
            
            html_content = render_template_string(
                template,
                prescription=prescription,
                patient=prescription.patient,
                settings=settings
            )

            send_email(
                to_email=prescription.patient.email,
                subject=f"Prescription Deleted - {settings.clinic_name}",
                body="A prescription has been deleted from your records.",
                html_body=html_content
            )
        except Exception as e:
            print(f"Failed to send deletion email: {str(e)}")

    db.session.delete(prescription)
    db.session.commit()
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('prescription.prescriptions')) 

@prescription_bp.route('/<int:id>/pdf')
@login_required
def prescription_pdf(id):
    prescription = Prescription.query.get_or_404(id)
    settings = ClinicSettings.get_settings()
    
    # Render the template
    html_content = render_template('dashboard/prescriptions/pdf.html',
                                 prescription=prescription,
                                 settings=settings)
    
    # PDF options
    options = {
        'page-size': 'A4',
        'margin-top': '2.5cm',
        'margin-right': '1.5cm',
        'margin-bottom': '2.5cm',
        'margin-left': '1.5cm',
        'encoding': "UTF-8",
        'no-outline': None
    }
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        # Generate PDF with configuration
        pdfkit.from_string(html_content, tmp.name, options=options, configuration=config)
        
        # Return the PDF file
        return send_file(
            tmp.name,
            download_name=f'prescription_{prescription.prescription_number}.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        ) 