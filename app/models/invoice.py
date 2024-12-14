from app import db
from datetime import datetime
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient')
    appointment = db.relationship('Appointment', backref='invoices')
    prescription = db.relationship('Prescription', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

    @staticmethod
    def generate_invoice_number():
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"INV{new_number:04d}"

    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount - self.discount

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InvoiceItem {self.description}>'

    def calculate_total(self):
        self.total = self.quantity * self.unit_price 