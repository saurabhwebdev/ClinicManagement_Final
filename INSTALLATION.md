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