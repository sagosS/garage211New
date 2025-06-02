import os
import json
from flask import render_template, redirect, url_for, flash, request, abort, current_app, Response
from flask_login import login_user, login_required, logout_user, current_user
from app.models import MetaTag, SitemapPage, RobotsTxt, User, Client, Order, Service, Promotion, News, ContactMessage, ImageAlt
from app import db, cache
from werkzeug.security import check_password_hash, generate_password_hash
from app.main import main
from datetime import datetime

def get_meta(page_type, slug=None):
    """
    Повертає MetaTag для сторінки.
    page_type: назва сторінки (наприклад, 'news_detail', 'service_detail', 'main' тощо)
    slug: якщо є, шукає meta для конкретного об'єкта
    """
    if slug:
        meta = MetaTag.query.filter_by(page=page_type, slug=slug).first()
        if meta:
            return meta
    meta = MetaTag.query.filter_by(page=page_type).first()
    if meta:
        return meta
    # Фолбек на дефолтний meta
    return MetaTag.query.filter_by(page='default').first()

@main.route('/')
@cache.cached(timeout=300)  # Кешує сторінку на 5 хвилин
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

    meta = get_meta('main')
    services = Service.query.order_by(Service.id.desc()).all()
    services_with_promos = [s for s in services if s.promotion][:6]
    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    news_list = News.query.order_by(News.date.desc()).limit(3).all()  # 3 останні новини
# Отримати alt-и з бази
    alts = {alt.filename: alt.alt for alt in ImageAlt.query.filter(ImageAlt.filename.in_(images)).all()}
    return render_template('index.html', meta=meta, images=images, alts=alts, services=services, services_with_promos=services_with_promos, promotions=promotions, news_list=news_list, title="Головна сторінка")

@main.route('/cabinet')
@cache.cached(timeout=300)
@login_required
def worker_cabinet():
    orders = Order.query.filter_by(employee_id=current_user.id).order_by(Order.created_at.desc()).all()
    meta = get_meta('worker_cabinet')
    return render_template('worker_cabinet.html', orders=orders, meta=meta)

@main.route('/worker_update_status/<int:order_id>', methods=['POST'])
@cache.cached(timeout=300)
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

@main.route('/book', methods=['GET', 'POST'])
@cache.cached(timeout=300)
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
            delivery_date=None,
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
        "year_min": 1980,
        "year_max": 2030,
        "year_placeholder": "Наприклад: 2015"
    }
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
    services = Service.query.order_by(Service.title).all()
    meta = get_meta('book')
    return render_template('book.html', settings=settings, services=services, meta=meta)

@main.route('/news')
@cache.cached(timeout=300)
def news():
    news_list = News.query.order_by(News.date.desc()).all()
    news = News.query.order_by(News.date.desc()).limit(3).all()
    meta = get_meta('news')
    # Отримати alt-и з бази
    images = []
    alts = {alt.filename: alt.alt for alt in ImageAlt.query.filter(ImageAlt.filename.in_(images)).all()}
    return render_template('news_list.html', news=news, news_list=news_list, meta=meta, alts=alts)

@main.route('/news/<slug>')
@cache.cached(timeout=300)
def news_detail(slug):
    news = News.query.filter_by(slug=slug).first_or_404()
    meta = get_meta('news_detail', slug)
    return render_template('news_detail.html', news=news, meta=meta)

@main.route('/promotions')
@cache.cached(timeout=300)
def promotions():
    promos = Promotion.query.order_by(Promotion.id.desc()).all()
    meta = get_meta('promotions')
    return render_template('promotions.html', promos=promos, meta=meta)

@main.route('/promotions/<slug>')
@cache.cached(timeout=300)
def promotion_detail(slug):
    promo = Promotion.query.filter_by(slug=slug).first_or_404()
    meta = get_meta('promotion_detail', slug)
    return render_template('promotion_detail.html', promo=promo, meta=meta)

@main.route('/services')
@cache.cached(timeout=300)
def all_services():
    services = Service.query.order_by(Service.title).all()
    meta = get_meta('services')
    return render_template('services_list.html', services=services, meta=meta)

@main.route('/services/<slug>')
@cache.cached(timeout=300)
def service_detail(slug):
    service = Service.query.filter_by(slug=slug).first_or_404()
    meta = get_meta('service_detail', slug)
    return render_template('service_detail.html', service=service, meta=meta)

@main.route('/gallery')
@cache.cached(timeout=300)
def gallery():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    gallery_json = os.path.join(upload_folder, 'gallery.json')
    images = []
    if os.path.exists(gallery_json):
        with open(gallery_json, 'r') as f:
            images = json.load(f)
    images = [img for img in images if os.path.exists(os.path.join(upload_folder, img))]

    alts_json = os.path.join(upload_folder, 'alts.json')
    alts = {}
    if os.path.exists(alts_json):
        with open(alts_json, 'r') as f:
            alts = json.load(f)
        # Отримати alt-и з бази
    alts = {alt.filename: alt.alt for alt in ImageAlt.query.filter(ImageAlt.filename.in_(images)).all()}        
    meta = get_meta('gallery')
    return render_template('gallery.html', images=images, alts=alts, meta=meta)

@main.route('/projects')
@cache.cached(timeout=300)
def projects():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    projects_json = os.path.join(upload_folder, 'projects.json')
    projects = []
    images = set()
    if os.path.exists(projects_json):
        with open(projects_json, 'r') as f:
            projects = json.load(f)
            # Універсалізуємо структуру: підтримка і "image", і "images"
            for project in projects:
                if 'images' not in project:
                    if 'image' in project and project['image']:
                        project['images'] = [project['image']]
                    else:
                        project['images'] = []
                for img in project['images']:
                    images.add(img)
    # Отримати alt-и з бази лише для потрібних зображень
    from app.models import ImageAlt
    alts = {alt.filename: alt.alt for alt in ImageAlt.query.filter(ImageAlt.filename.in_(images)).all()}
    meta = get_meta('projects')
    return render_template('projects.html', projects=projects, meta=meta, alts=alts)

@main.route('/contacts', methods=['GET', 'POST'])
@cache.cached(timeout=300)
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
    meta = get_meta('contacts')
    return render_template('contacts.html', title="Контакти", meta=meta)

@main.route('/sitemap.xml')
@cache.cached(timeout=600)
def sitemap():
    pages = SitemapPage.query.all()
    meta = get_meta('sitemap')
    return render_template('sitemap.xml', pages=pages, meta=meta)

@main.route('/robots.txt')
@cache.cached(timeout=600)
def robots_txt():
    robots = RobotsTxt.query.first()
    sitemap_url = url_for('main.sitemap', _external=True)
    if robots and robots.content:
        content = robots.content.strip()
        if 'Sitemap:' not in content:
            content += f"\n\nSitemap: {sitemap_url}"
    else:
        content = f"User-agent: *\nDisallow:\n\nSitemap: {sitemap_url}"
    return Response(content, mimetype='text/plain')

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html', meta=get_meta('404')), 404

@main.route('/login', methods=['GET', 'POST'])
@cache.cached(timeout=300)
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
    meta = get_meta('login')
    return render_template('login.html', meta=meta)

@main.route('/logout')
@cache.cached(timeout=300)
@login_required
def logout():
    logout_user()
    flash('login_success', 'info')
    return redirect(url_for('main.index'))