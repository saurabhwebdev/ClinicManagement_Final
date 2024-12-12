# Deploying Clinic Management System on Render

## Prerequisites

1. A Render account (https://render.com)
2. A GitHub repository with your application code
3. PostgreSQL database (can be created on Render)

## Step 1: Prepare Your Database

1. Log in to your Render dashboard
2. Click "New +" and select "PostgreSQL"
3. Fill in the details:
   - Name: `clinic-management-db`
   - Database: `clinic_db`
   - User: Leave as auto-generated
   - Region: Choose nearest to your users
4. Click "Create Database"
5. Save the following information:
   - Internal Database URL
   - External Database URL
   - User
   - Password

## Step 2: Deploy the Web Service

1. In Render dashboard, click "New +" and select "Web Service"
2. Connect your GitHub repository
3. Fill in the configuration:
   - Name: `clinic-management`
   - Environment: `Python 3`
   - Region: Same as database
   - Branch: `main`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn run:app`
   - Instance Type: Choose based on your needs (starter is good for testing)

4. Add Environment Variables:
   ```
   DATABASE_URL=your_postgres_url_from_step_1
   FLASK_APP=run.py
   FLASK_ENV=production
   SECRET_KEY=your_secure_secret_key
   ```

5. Click "Create Web Service"

## Step 3: Initial Setup

1. Once deployed, access your application URL
2. Create the admin user through Render shell:
   - Go to your web service
   - Click "Shell"
   - Run:
     ```bash
     flask create-admin
     ```
   - Follow the prompts

## Step 4: Configure Email (Optional)

1. In your web service settings, add these environment variables:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

## Step 5: PDF Generation Setup

1. The build script automatically installs wkhtmltopdf
2. Add this environment variable if needed:
   ```
   WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf
   ```

## Troubleshooting

### Database Issues
If you encounter database issues:
1. Connect to the database shell:
   ```bash
   flask db stamp head
   flask db migrate
   flask db upgrade
   ```

### PDF Generation Issues
1. Check if wkhtmltopdf is installed:
   ```bash
   wkhtmltopdf --version
   ```
2. Verify the path:
   ```bash
   which wkhtmltopdf
   ```

### Application Logs
1. In Render dashboard, go to your web service
2. Click "Logs" to view application logs

## Maintenance

### Database Backups
Render automatically creates daily backups of your PostgreSQL database.

To manually backup:
1. Go to your database in Render
2. Click "Backups"
3. Click "Create Backup"

### Updating the Application
1. Push changes to your GitHub repository
2. Render will automatically redeploy

### Monitoring
1. Set up Render monitoring alerts:
   - Go to web service settings
   - Click "Monitoring"
   - Configure alerts for:
     - HTTP errors
     - Response time
     - CPU usage
     - Memory usage

## Security Recommendations

1. Use strong, unique passwords
2. Enable 2FA on your Render account
3. Regularly update dependencies
4. Monitor application logs
5. Use environment variables for sensitive data
6. Enable automatic database backups 