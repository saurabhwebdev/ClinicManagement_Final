from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin = User(
                email='admin@gmail.com',
                username='Admin',
                password_hash=generate_password_hash('admin@123'),
                role='admin',
                is_trial=False,
                trial_start=datetime.utcnow(),
                trial_end=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    create_admin_user() 