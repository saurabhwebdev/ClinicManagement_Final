import os
import sys
from app import create_app, db

def get_base_path():
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    try:
        # Change to the correct directory
        os.chdir(get_base_path())
        
        print("Creating Flask application...")
        app = create_app()
        
        print("Initializing database...")
        with app.app_context():
            db.create_all()
        
        print("Starting Flask server...")
        app.run(debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error starting Flask application: {str(e)}", file=sys.stderr)
        sys.exit(1) 