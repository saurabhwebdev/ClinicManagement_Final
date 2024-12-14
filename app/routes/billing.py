from flask import Blueprint, render_template
from flask_login import login_required

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/upgrade')
@login_required
def upgrade():
    return render_template('dashboard/billing/upgrade.html') 