from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash
from app.models import User
from app.extensions import db
from . import admin

@admin.route('/')
@login_required
def admin_index():
    return render_template('admin/index.html')

@admin.route('/register_worker', methods=['GET', 'POST'])
@login_required
def register_worker():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        phone = request.form['phone_number']
        password = request.form['password']
        password2 = request.form['password2']
        if password != password2:
            flash('Паролі не співпадають', 'danger')
            return render_template('admin/register_worker.html')
        if User.query.filter_by(phone_number=phone).first():
            flash('Користувач з таким номером вже існує', 'danger')
            return render_template('admin/register_worker.html')
        user = User(phone_number=phone, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Працівника зареєстровано!', 'success')
        return redirect(url_for('admin.register_worker'))
    return render_template('admin/register_worker.html')

@admin.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Ви вийшли з адмінки', 'info')
    return redirect(url_for('main.index'))