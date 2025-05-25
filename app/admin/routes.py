from flask import render_template
from app.admin import admin

@admin.route('/')
def dashboard():
    # Це головна сторінка адмін-панелі
    return render_template('admin/dashboard.html', title="Адмін панель")

@admin.route('/clients')
def clients():
    # Сторінка для роботи з клієнтами
    return render_template('admin/clients.html', title="Клієнти")
