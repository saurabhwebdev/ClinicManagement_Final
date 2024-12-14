from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from datetime import datetime

def check_trial_status(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_trial and datetime.utcnow() > current_user.trial_end:
            flash('Your trial period has expired. Please upgrade your account.', 'warning')
            return redirect(url_for('billing.upgrade'))  # Create this route for upgrading
        return f(*args, **kwargs)
    return decorated_function 