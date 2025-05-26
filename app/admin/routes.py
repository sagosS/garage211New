from flask import render_template
from flask_login import login_required
from . import admin

@admin.route('/')
@login_required
def admin_index():
    return render_template('admin/index.html')