# Clinic Management System - Installation Guide

## System Requirements

- Python 3.9 or higher
- pip (Python package installer)
- Git
- wkhtmltopdf (for PDF generation)

## Step 1: Install System Dependencies

### Windows:
1. Download and install Python from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening cmd and typing: `python --version`

2. Download and install Git from [git-scm.com](https://git-scm.com)
   - Use default installation options
   - Verify installation: `git --version`

3. Download and install wkhtmltopdf from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
   - Download the Windows installer (64-bit recommended)
   - Install to default location: `C:\Program Files\wkhtmltopdf`
   - Add to PATH:
     1. Open System Properties (Win + Pause|Break)
     2. Click "Advanced system settings"
     3. Click "Environment Variables"
     4. Under "System Variables", find and select "Path"
     5. Click "Edit"
     6. Click "New"
     7. Add `C:\Program Files\wkhtmltopdf\bin`
     8. Click "OK" on all windows
     9. Verify installation by opening a new cmd window and typing: `wkhtmltopdf --version`

### Linux (Ubuntu/Debian):

## Creating Desktop Shortcut (Easy Method)

1. First install pyinstaller:
```bash
pip install pyinstaller
```

2. Create a launcher.py file in your app directory:
```python
import os
import sys
from subprocess import Popen

def start_app():
    # Get the directory containing the script
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the app directory
    os.chdir(app_dir)
    
    # Start Flask app
    if sys.platform.startswith('win'):
        Popen(['venv\\Scripts\\python', 'run.py'])
    else:
        Popen(['./venv/bin/python', 'run.py'])

if __name__ == '__main__':
    start_app()
```

3. Create executable:
```bash
# For Windows:
pyinstaller --onefile --icon=app/static/images/icon.ico --name ClinicApp launcher.py

# For Linux/Mac:
pyinstaller --onefile --name ClinicApp launcher.py
```

4. Your executable will be created in the `dist` folder. Simply:
   - Copy the executable (ClinicApp.exe for Windows or ClinicApp for Linux/Mac) to your desktop
   - Double-click to run the application

This method creates a single executable file that you can click to start the application. No need to create batch files or desktop entries.

Note: Make sure to replace `app/static/images/icon.ico` with the path to your actual icon file if you have one.