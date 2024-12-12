from app import db
from datetime import datetime
from app.models.patient import Patient

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, default=30)  # in minutes
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref='appointments')

    @property
    def status_badge_color(self):
        status_colors = {
            'scheduled': 'yellow',
            'completed': 'green',
            'cancelled': 'red'
        }
        return status_colors.get(self.status, 'gray')

    def __repr__(self):
        return f'<Appointment {self.appointment_number}>'

    @staticmethod
    def generate_appointment_number():
        last_appointment = Appointment.query.order_by(Appointment.id.desc()).first()
        if last_appointment:
            last_number = int(last_appointment.appointment_number[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"APT{new_number:04d}" 