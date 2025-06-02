import os
import json
from flask import render_template, redirect, url_for, flash, request, abort, current_app, Response
from flask_login import login_user, login_required, logout_user, current_user
from app.models import MetaTag, SitemapPage, RobotsTxt, User, Client, Order, Service, Promotion, News, ContactMessage
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from app.main import main
from datetime import datetime

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

    meta = MetaTag.query.filter_by(page='main').first()
    services = Service.query.order_by(Service.id.desc()).all()
    services_with_promos = [s for s in services if s.promotion][:6]
    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    news_list = News.query.order_by(News.date.desc()).limit(3).all()  # 3 останні новини

    return render_template('index.html', meta=meta, images=images, alts=alts, services=services, services_with_promos=services_with_promos, promotions=promotions, news_list=news_list, title="Головна сторінка")

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
    orders = Order.query.filter_by(employee_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('worker_cabinet.html', orders=orders)

@main.route('/worker_update_status/<int:order_id>', methods=['POST'])
@login_required
def worker_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.employee_id != current_user.id:
        flash('Ви не можете змінювати цей заказ', 'danger')
        return redirect(url_for('main.worker_cabinet'))
    new_status = request.form.get('status')
    if new_status in ['в роботі', 'завершена']:
        order.status = new_status
        db.session.commit()
        flash('Статус оновлено!', 'success')
    return redirect(url_for('main.worker_cabinet'))

@main.route('/news')
def news():
    news_list = News.query.order_by(News.date.desc()).all()
    news = News.query.order_by(News.date.desc()).limit(3).all()  # або інша ваша логіка
    return render_template('news_list.html', news=news, news_list=news_list)

@main.route('/book', methods=['GET', 'POST'])
def book():
    services = Service.query.order_by(Service.title).all()
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        vin = request.form.get('vin')
        service = request.form.get('service')
        desired_date = request.form.get('date')
        comment = request.form.get('comment')

        # Додаємо клієнта, якщо не існує
        client = Client.query.filter_by(phone_number=phone).first()
        if not client:
            client = Client(phone_number=phone, name=name, password=generate_password_hash(phone))
            db.session.add(client)
            db.session.commit()

        # Додаємо заявку
        order = Order(
            created_at=datetime.utcnow(),
            desired_date=desired_date,
            delivery_date=None,  # можна додати поле у форму
            brand=brand,
            model=model,
            year=year,
            vin=vin,
            name=name,
            phone=phone,
            comment=comment,
            repair=service,
            parts=None,
            price=None,
            client_id=client.id
        )
        db.session.add(order)
        db.session.commit()
        flash('Ваша заявка прийнята!', 'success')
        return redirect(url_for('main.index'))
    settings_path = os.path.join(current_app.static_folder, 'book_form_settings.json')
    settings = {
        # "services": ["Діагностика", "ТО", "Ремонт ходової", "Заміна масла", "Ремонт гальмівної системи", "Інше"],
        "year_min": 1980,
        "year_max": 2030,
        "year_placeholder": "Наприклад: 2015"
    }
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
    services = Service.query.order_by(Service.title).all()
    return render_template('book.html', settings=settings, services=services)

@main.route('/news/<slug>')
def news_detail(slug):
    news = News.query.filter_by(slug=slug).first_or_404()
    return render_template('news_detail.html', news=news)

@main.route('/promotions/<slug>')
def promotion_detail(slug):
    promo = Promotion.query.filter_by(slug=slug).first_or_404()
    return render_template('promotion_detail.html', promo=promo)

@main.route('/services/<slug>')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug).first_or_404()
    return render_template('service_detail.html', service=service)

@main.route('/promotions')
def promotions():
    promos = Promotion.query.order_by(Promotion.id.desc()).all()
    return render_template('promotions.html', promos=promos)

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

@main.route('/sitemap.xml')
def sitemap():
    pages = SitemapPage.query.all()
    return render_template('sitemap.xml', pages=pages)

@main.route('/robots.txt')
def robots_txt():
    robots = RobotsTxt.query.first()
    sitemap_url = url_for('main.sitemap', _external=True)
    if robots and robots.content:
        content = robots.content.strip()
        # Додаємо Sitemap, якщо його немає у content
        if 'Sitemap:' not in content:
            content += f"\n\nSitemap: {sitemap_url}"
    else:
        content = f"User-agent: *\nDisallow:\n\nSitemap: {sitemap_url}"
    return Response(content, mimetype='text/plain')

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
