from app import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    invoices = db.relationship('Invoice', lazy=True)

    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @staticmethod
    def generate_registration_number():
        last_patient = Patient.query.order_by(Patient.id.desc()).first()
        if last_patient:
            last_number = int(last_patient.registration_number[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"PAT{new_number:04d}" 