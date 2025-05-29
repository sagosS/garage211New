import os
import json
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, login_required, logout_user
from app.models import User, Service, Promotion, News, ContactMessage
from app import db
from werkzeug.security import check_password_hash
from app.main import main

@main.route('/')
def index():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    gallery_json = os.path.join(upload_folder, 'gallery.json')
    alts_json = os.path.join(upload_folder, 'alts.json')
    images = []
    alts = {}

    # Завантажити вибрані картинки
    if os.path.exists(gallery_json):
        try:
            with open(gallery_json, 'r') as f:
                content = f.read().strip()
                if content:
                    images = json.loads(content)
        except Exception:
            images = []

    # Завантажити alt-тексти
    if os.path.exists(alts_json):
        try:
            with open(alts_json, 'r') as f:
                alts = json.load(f)
        except Exception:
            alts = {}

    services = Service.query.order_by(Service.id.desc()).all()
    services_with_promos = [s for s in services if s.promotion][:6]
    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    news_list = News.query.order_by(News.date.desc()).limit(3).all()  # 3 останні новини

    return render_template('index.html', images=images, alts=alts, services=services, services_with_promos=services_with_promos, promotions=promotions, news_list=news_list, title="Головна сторінка")

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(phone_number=request.form['phone_number']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin.admin_index'))
            else:
                return redirect(url_for('main.worker_cabinet'))
        flash('login_error', 'danger')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('login_success', 'info')
    return redirect(url_for('main.index'))

@main.route('/cabinet')
@login_required
def worker_cabinet():
    return render_template('worker_cabinet.html')

@main.route('/news')
def news():
    news_list = News.query.order_by(News.date.desc()).all()
    news = News.query.order_by(News.date.desc()).limit(3).all()  # або інша ваша логіка
    return render_template('news_list.html', news=news, news_list=news_list)

@main.route('/book', methods=['GET', 'POST'])
def book():
    services = Service.query.order_by(Service.title).all()
    if request.method == 'POST':
        # Тут обробка форми, наприклад, збереження в БД чи надсилання email
        flash('Ваша заявка прийнята!', 'success')
        return redirect(url_for('main.book'))
    settings_path = os.path.join(current_app.static_folder, 'book_form_settings.json')
    settings = {
        "services": ["Діагностика", "ТО", "Ремонт ходової", "Заміна масла", "Ремонт гальмівної системи", "Інше"],
        "year_min": 1980,
        "year_max": 2030,
        "year_placeholder": "Наприклад: 2015"
    }
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
    return render_template('book.html', settings=settings, services=services)

@main.route('/news/<int:news_id>')
def news_detail(news_id):
    # Тут має бути пошук новини за id (наприклад, з БД)
    # Для прикладу:
    news = [
        {
            "id": 1,
            "title": "Відкриття нового сервісу",
            "date": "2025-05-20",
            "content": "Повний текст новини 1...",
            "image_url": url_for('static', filename='images/news1.jpg')
        },
        {
            "id": 2,
            "title": "Весняна акція",
            "date": "2025-04-15",
            "content": "Повний текст новини 2...",
            "image_url": url_for('static', filename='images/news2.jpg')
        },
        # ...ще новини...
    ]
    item = next((n for n in news if n["id"] == news_id), None)
    if not item:
        abort(404)
    return render_template('news_detail.html', item=item)

@main.route('/promotions')
def promotions():
    promos = Promotion.query.order_by(Promotion.id.desc()).all()
    return render_template('promotions.html', promos=promos)

@main.route('/promotions/<int:promo_id>')
def promotion_detail(promo_id):
    promo = Promotion.query.get(promo_id)
    if not promo:
        abort(404)
    return render_template('promotion_detail.html', promo=promo)

@main.route('/services')
def all_services():
    services = Service.query.order_by(Service.title).all()
    return render_template('services_list.html', services=services)

@main.route('/gallery')
def gallery():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    gallery_json = os.path.join(upload_folder, 'gallery.json')
    images = []
    if os.path.exists(gallery_json):
        with open(gallery_json, 'r') as f:
            images = json.load(f)
    # Фільтруємо тільки ті, що реально існують
    images = [img for img in images if os.path.exists(os.path.join(upload_folder, img))]

    alts_json = os.path.join(upload_folder, 'alts.json')
    alts = {}
    if os.path.exists(alts_json):
        with open(alts_json, 'r') as f:
            alts = json.load(f)
    return render_template('gallery.html', images=images, alts=alts)

@main.route('/projects')
def projects():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    projects_json = os.path.join(upload_folder, 'projects.json')
    projects = []
    if os.path.exists(projects_json):
        with open(projects_json, 'r') as f:
            projects = json.load(f)
    return render_template('projects.html', projects=projects)

@main.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        message = request.form.get('message')
        if name and phone and message:
            msg = ContactMessage(name=name, phone=phone, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('contact_success', 'success')
            return redirect(url_for('main.contacts'))
    return render_template('contacts.html', title="Контакти")
