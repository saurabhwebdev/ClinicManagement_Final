from flask import Blueprint, render_template, request, flash, redirect, url_for, render_template_string, send_file
from flask_login import login_required
from app.models.invoice import Invoice, InvoiceItem
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.settings import ClinicSettings
from app import db
from datetime import datetime, date, timedelta
from app.utils.email import send_email
import pdfkit
import tempfile
import os
import io

# PDF Configuration
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoices')

@invoice_bp.route('/')
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

    return render_template('dashboard/invoices/index.html',
                         invoices=invoices,
                         search=search,
                         status=status,
                         date_filter=date_filter)

@invoice_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    patients = Patient.query.order_by(Patient.first_name).all()
    
    # Modify the appointments query to join with patient data and include more details
    appointments = Appointment.query.join(
        Appointment.patient
    ).filter(
        Appointment.status.in_(['completed', 'scheduled'])  # Include both completed and scheduled appointments
    ).order_by(
        Appointment.date.desc(), 
        Appointment.time.desc()
    ).all()
    
    prescriptions = Prescription.query.order_by(Prescription.date.desc()).all()
    settings = ClinicSettings.get_settings()

    if request.method == 'POST':
        # Create new invoice
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            patient_id=request.form.get('patient_id'),
            appointment_id=request.form.get('appointment_id') or None,
            prescription_id=request.form.get('prescription_id') or None,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else None,
            tax_rate=float(request.form.get('tax_rate', 0)),
            discount=float(request.form.get('discount', 0)),
            notes=request.form.get('notes'),
            status='pending'
        )

        db.session.add(invoice)

        # Add invoice items
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')

        for i in range(len(descriptions)):
            if descriptions[i] and unit_prices[i]:  # Only add if description and price are provided
                item = InvoiceItem(
                    description=descriptions[i],
                    quantity=int(quantities[i]),
                    unit_price=float(unit_prices[i])
                )
                item.calculate_total()
                invoice.items.append(item)

        # Calculate invoice totals
        invoice.calculate_totals()
        db.session.commit()

        # Send invoice email
        if invoice.patient.email:
            try:
                with open('app/templates/emails/invoice_created.html', 'r') as file:
                    template = file.read()
                
                html_content = render_template_string(
                    template,
                    invoice=invoice,
                    patient=invoice.patient,
                    settings=settings
                )

                send_email(
                    to_email=invoice.patient.email,
                    subject=f"Invoice {invoice.invoice_number} - {settings.clinic_name}",
                    body=f"Your invoice (#{invoice.invoice_number}) has been generated.",
                    html_body=html_content
                )
                flash('Invoice created and sent successfully!', 'success')
            except Exception as e:
                flash('Invoice created but failed to send email.', 'warning')
                print(f"Email error: {str(e)}")
        else:
            flash('Invoice created successfully!', 'success')

        return redirect(url_for('invoice.view_invoice', id=invoice.id))

    return render_template('dashboard/invoices/new.html',
                         patients=patients,
                         appointments=appointments,
                         prescriptions=prescriptions,
                         settings=settings,
                         today=date.today(),
                         default_due_date=date.today() + timedelta(days=30))

@invoice_bp.route('/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    settings = ClinicSettings.get_settings()
    return render_template('dashboard/invoices/view.html',
                         invoice=invoice,
                         settings=settings)

@invoice_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    patients = Patient.query.order_by(Patient.first_name).all()
    appointments = Appointment.query.filter(
        Appointment.status == 'completed'
    ).order_by(Appointment.date.desc()).all()
    prescriptions = Prescription.query.order_by(Prescription.date.desc()).all()
    settings = ClinicSettings.get_settings()

    if request.method == 'POST':
        # Update invoice details
        invoice.patient_id = request.form.get('patient_id')
        invoice.appointment_id = request.form.get('appointment_id') or None
        invoice.prescription_id = request.form.get('prescription_id') or None
        invoice.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        invoice.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else None
        invoice.tax_rate = float(request.form.get('tax_rate', 0))
        invoice.discount = float(request.form.get('discount', 0))
        invoice.notes = request.form.get('notes')

        # Clear existing items
        invoice.items = []

        # Add new items
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')

        for i in range(len(descriptions)):
            if descriptions[i] and unit_prices[i]:
                item = InvoiceItem(
                    description=descriptions[i],
                    quantity=int(quantities[i]),
                    unit_price=float(unit_prices[i])
                )
                item.calculate_total()
                invoice.items.append(item)

        # Calculate invoice totals
        invoice.calculate_totals()
        db.session.commit()

        flash('Invoice updated successfully!', 'success')
        return redirect(url_for('invoice.view_invoice', id=invoice.id))

    return render_template('dashboard/invoices/edit.html',
                         invoice=invoice,
                         patients=patients,
                         appointments=appointments,
                         prescriptions=prescriptions,
                         settings=settings)

@invoice_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    patient = invoice.patient
    settings = ClinicSettings.get_settings()

    # Send deletion notification email
    if patient.email:
        try:
            html_content = render_template('emails/invoice_deletion.html',
                                         invoice=invoice,
                                         patient=patient,
                                         settings=settings)
            
            send_email(
                to_email=patient.email,
                subject=f"Invoice {invoice.invoice_number} Deleted - {settings.clinic_name}",
                body=f"Invoice #{invoice.invoice_number} has been deleted from our records.",
                html_body=html_content
            )
        except Exception as e:
            print(f"Email error: {str(e)}")

    db.session.delete(invoice)
    db.session.commit()
    
    flash('Invoice deleted successfully!', 'success')
    return redirect(url_for('invoice.invoices'))

@invoice_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    invoice = Invoice.query.get_or_404(id)
    settings = ClinicSettings.get_settings()

    new_status = request.form.get('status')
    if new_status == 'paid':
        invoice.status = 'paid'
        invoice.payment_date = datetime.utcnow()
        invoice.payment_method = request.form.get('payment_method')

        # Send payment confirmation email
        if invoice.patient.email:
            try:
                html_content = render_template('emails/payment_confirmation.html',
                                             invoice=invoice,
                                             patient=invoice.patient,
                                             settings=settings)
                
                send_email(
                    to_email=invoice.patient.email,
                    subject=f"Payment Confirmation - Invoice {invoice.invoice_number}",
                    body=f"Payment for invoice #{invoice.invoice_number} has been received.",
                    html_body=html_content
                )
            except Exception as e:
                print(f"Email error: {str(e)}")

    db.session.commit()
    flash(f'Invoice status updated to {new_status}!', 'success')
    return redirect(url_for('invoice.view_invoice', id=id))

@invoice_bp.route('/<int:id>/pdf')
@login_required
def invoice_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    settings = ClinicSettings.get_settings()

    html = render_template('dashboard/invoices/pdf.html',
                         invoice=invoice,
                         settings=settings)

    # Create PDF
    pdf = pdfkit.from_string(html, False, configuration=config)

    # Create response
    response = send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'invoice_{invoice.invoice_number}.pdf'
    )

    return response