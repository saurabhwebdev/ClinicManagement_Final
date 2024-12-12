from app import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_number = db.Column(db.String(20), unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    date = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref='prescriptions')
    appointment = db.relationship('Appointment', backref='prescriptions')
    medicines = db.relationship('PrescriptionMedicine', backref='prescription', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prescription {self.prescription_number}>'

    @staticmethod
    def generate_prescription_number():
        last_prescription = Prescription.query.order_by(Prescription.id.desc()).first()
        if last_prescription:
            last_number = int(last_prescription.prescription_number[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"PRE{new_number:04d}"

class PrescriptionMedicine(db.Model):
    __tablename__ = 'prescription_medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))  # e.g., "1 tablet"
    frequency = db.Column(db.String(50))  # e.g., "twice daily"
    duration = db.Column(db.String(50))  # e.g., "7 days"
    instructions = db.Column(db.Text)  # e.g., "Take after meals"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PrescriptionMedicine {self.medicine_name}>' 