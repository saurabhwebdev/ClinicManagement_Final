from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import all blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.appointment import appointment_bp
    from app.routes.prescription import prescription_bp
    from app.routes.invoice import invoice_bp
    from app.routes.billing import billing_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(billing_bp)

    # Add context processor for global template variables
    @app.context_processor
    def inject_settings():
        from app.models.settings import ClinicSettings
        settings = ClinicSettings.get_settings()
        return dict(clinic_settings=settings)

    return app 