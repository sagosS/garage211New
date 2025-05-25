from flask import render_template
from app.main import main
from app.forms import ApplicationForm

@main.route('/')
def index():
    form = ApplicationForm()
    return render_template('index.html', title="Головна сторінка", form=form)

@main.route('/news')
def news():
    return render_template('news.html', title="Новини")

@main.route('/promotions')
def promotions():
    return render_template('promotions.html', title="Акції")

@main.route('/gallery')
def gallery():
    return render_template('gallery.html', title="Галерея")

@main.route('/contacts')
def contacts():
    return render_template('contacts.html', title="Контакти")

@main.route('/application')
def application():
    return render_template('application.html', title="Подати заявку")
