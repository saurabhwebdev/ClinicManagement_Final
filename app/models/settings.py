from app import db

class ClinicSettings(db.Model):
    __tablename__ = 'clinic_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_name = db.Column(db.String(200), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    country_code = db.Column(db.String(5), default='+91')
    address = db.Column(db.Text)
    currency = db.Column(db.String(3), default='INR')
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    working_days = db.Column(db.String(100))
    registration_number = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    logo_path = db.Column(db.String(200))
    gmail_app_password = db.Column(db.String(100))

    @staticmethod
    def get_settings():
        settings = ClinicSettings.query.first()
        if not settings:
            settings = ClinicSettings(
                clinic_name="My Clinic",
                doctor_name="Dr. Name",
                country_code='+91',
                currency='INR',
                email="clinic@example.com"
            )
            db.session.add(settings)
            db.session.commit()
        return settings