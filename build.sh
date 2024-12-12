#!/bin/bash
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y wkhtmltopdf

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade 