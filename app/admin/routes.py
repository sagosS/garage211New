import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash
from app.models import MetaTag, SitemapPage, RobotsTxt, User, Client, Order, Employee, Service, Promotion, News, ContactMessage, MaterialAsset
from app.extensions import db
from . import admin
from werkzeug.utils import secure_filename
import json
import pandas as pd
import requests

@admin.route('/')
@login_required
def admin_index():
    # Підрахунок працівників (роль "Майстер" або "Працівник", не адмін)
    workers_count = User.query.filter(User.role.in_(['Майстер', 'Працівник']), User.is_admin == False).count()
    # Підрахунок клієнтів (роль "Клієнт" або без ролі)
    clients_count = Client.query.count()
    # Всього заявок
    orders_count = Order.query.count()
    # Активні заявки (не завершені)
    active_orders_count = Order.query.filter(Order.status != 'завершена').count()
    # Завершені заявки
    finished_orders_count = Order.query.filter(Order.status == 'завершена').count()
    # Середній чек
    avg_order_price = db.session.query(db.func.avg(Order.price)).scalar()
    # Останні 5 заявок
    last_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    # Статистика по статусах
    from collections import defaultdict
    status_counts = defaultdict(int)
    for order in Order.query.all():
        status_counts[order.status] += 1

    return render_template(
        'admin/index.html',
        workers_count=workers_count,
        clients_count=clients_count,
        orders_count=orders_count,
        active_orders_count=active_orders_count,
        finished_orders_count=finished_orders_count,
        avg_order_price=avg_order_price,
        last_orders=last_orders,
        status_counts=status_counts
    )

@admin.route('/meta/<page>', methods=['GET', 'POST'])
@login_required
def edit_meta(page):
    meta = MetaTag.query.filter_by(page=page).first()
    if not meta:
        meta = MetaTag(page=page)
        db.session.add(meta)
    if request.method == 'POST':
        meta.title = request.form.get('title')
        meta.description = request.form.get('description')
        meta.keywords = request.form.get('keywords')
        meta.schema_org = request.form.get('schema_org')
        meta.og_title = request.form['og_title']
        meta.og_description = request.form['og_description']
        meta.og_image = request.form['og_image']
        meta.twitter_title = request.form['twitter_title']
        meta.twitter_description = request.form['twitter_description']
        meta.twitter_image = request.form['twitter_image']
        db.session.commit()
        flash('Meta-теги та schema.org оновлено!', 'success')
        return redirect(url_for('admin.edit_meta', page=page))
    return render_template('admin/edit_meta.html', meta=meta, page=page)

@admin.route('/users')
@login_required
def admin_users():
    users = User.query.order_by(User.last_name, User.first_name).all()
    return render_template('admin/users.html', users=users)

@admin.route('/clients')
@login_required
def admin_clients():
    clients = Client.query.order_by(Client.id.desc()).all()
    # Для кожного клієнта знайти кількість замовлень
    client_orders = {c.id: Order.query.filter_by(client_id=c.id).count() for c in clients}
    return render_template(
        'admin/clients.html',
        clients=clients,
        client_orders=client_orders
    )

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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@admin.route('/images', methods=['GET', 'POST'])
@login_required
def admin_images():
    if not current_user.is_admin:
        abort(403)
    static_folder = current_app.static_folder
    upload_folder = os.path.join(static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    alts_json = os.path.join(upload_folder, 'alts.json')

    # Завантажити alt-тексти
    if os.path.exists(alts_json):
        with open(alts_json, 'r') as f:
            alts = json.load(f)
    else:
        alts = {}

    if request.method == 'POST':
        file = request.files.get('image')
        alt = request.form.get('alt', '').strip()
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            if alt:
                alts[filename] = alt
                with open(alts_json, 'w') as f:
                    json.dump(alts, f, ensure_ascii=False)
            flash('Зображення завантажено!', 'success')
        else:
            flash('Неприпустимий формат файлу.', 'danger')
        return redirect(url_for('admin.admin_images'))

    images = [f for f in os.listdir(upload_folder)
              if f != 'gallery.json' and f != 'alts.json' and not f.startswith('.')]
    images = sorted(images)
    return render_template('admin/images.html', images=images, alts=alts)

@admin.route('/delete_image/<filename>', methods=['POST'])
@login_required
def delete_image(filename):
    if not current_user.is_admin:
        abort(403)
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    file_path = os.path.join(upload_folder, filename)
    # Видалити файл, якщо існує
    if os.path.exists(file_path):
        os.remove(file_path)
        # Також видалити з gallery.json, якщо там є
        gallery_json = os.path.join(upload_folder, 'gallery.json')
        if os.path.exists(gallery_json):
            try:
                with open(gallery_json, 'r') as f:
                    content = f.read().strip()
                    if content:
                        selected = json.loads(content)
                    else:
                        selected = []
            except Exception:
                selected = []
            if filename in selected:
                selected.remove(filename)
                with open(gallery_json, 'w') as f:
                    json.dump(selected, f)
        flash('Зображення видалено!', 'success')
    else:
        flash('Файл не знайдено.', 'danger')
    return redirect(url_for('admin.admin_images'))

@admin.route('/gallery_editor', methods=['GET', 'POST'])
@login_required
def gallery_editor():
    if not current_user.is_admin:
        abort(403)
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    # Відфільтрувати gallery.json та приховані файли
    images = [f for f in os.listdir(upload_folder)
              if f != 'gallery.json' and not f.startswith('.')]
    images = sorted(images)
    gallery_json = os.path.join(upload_folder, 'gallery.json')

    # Завантажити вибрані раніше
    selected = []
    if os.path.exists(gallery_json):
        try:
            with open(gallery_json, 'r') as f:
                content = f.read().strip()
                if content:
                    selected = json.loads(content)
                else:
                    selected = []
        except Exception:
            selected = []

    if request.method == 'POST':
        selected = request.form.getlist('gallery_images')
        with open(gallery_json, 'w') as f:
            json.dump(selected, f)
        flash('Галерею оновлено!', 'success')
        return redirect(url_for('admin.gallery_editor'))

    return render_template('admin/gallery_editor.html', images=images, selected=selected)

@admin.route('/projects', methods=['GET', 'POST'])
@login_required
def admin_projects():
    if not current_user.is_admin:
        abort(403)
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    projects_json = os.path.join(upload_folder, 'projects.json')
    images = [f for f in os.listdir(upload_folder)
              if f not in ('gallery.json', 'alts.json', 'projects.json') and not f.startswith('.')]
    images = sorted(images)

    # Завантажити існуючі проєкти
    projects = []
    if os.path.exists(projects_json):
        with open(projects_json, 'r') as f:
            projects = json.load(f)

    # Видалення проєкту
    delete_idx = request.args.get('delete')
    if delete_idx is not None:
        try:
            idx = int(delete_idx)
            if 0 <= idx < len(projects):
                projects.pop(idx)
                with open(projects_json, 'w') as f:
                    json.dump(projects, f, ensure_ascii=False)
                flash('Проєкт видалено!', 'success')
                return redirect(url_for('admin.admin_projects'))
        except Exception:
            flash('Помилка видалення проєкту.', 'danger')

    # Редагування проєкту
    edit_idx = request.args.get('edit')
    edit_project = None
    if edit_idx is not None:
        try:
            idx = int(edit_idx)
            if 0 <= idx < len(projects):
                edit_project = projects[idx]
        except Exception:
            edit_project = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()  # ДОДАЙТЕ ЦЕ
        selected = request.form.getlist('project_images')
        idx = request.form.get('idx')
        if idx:  # Редагування
            try:
                idx = int(idx)
                if name and selected and 0 <= idx < len(projects):
                    projects[idx] = {'name': name, 'description': description, 'images': selected}  # ДОДАЙТЕ description
                    with open(projects_json, 'w') as f:
                        json.dump(projects, f, ensure_ascii=False)
                    flash('Проєкт оновлено!', 'success')
                    return redirect(url_for('admin.admin_projects'))
            except Exception:
                flash('Помилка редагування.', 'danger')
        else:  # Додавання
            if name and selected:
                projects.append({'name': name, 'description': description, 'images': selected})  # ДОДАЙТЕ description
                with open(projects_json, 'w') as f:
                    json.dump(projects, f, ensure_ascii=False)
                flash('Проєкт створено!', 'success')
                return redirect(url_for('admin.admin_projects'))
            else:
                flash('Вкажіть назву та виберіть картинки.', 'danger')

    return render_template('admin/projects.html', images=images, projects=projects, edit_project=edit_project)

@admin.route('/orders')
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@admin.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        order.desired_date = request.form.get('desired_date')
        order.delivery_date = request.form.get('delivery_date')
        order.brand = request.form.get('brand')
        order.model = request.form.get('model')
        order.year = request.form.get('year')
        order.vin = request.form.get('vin')
        order.name = request.form.get('name')
        order.phone = request.form.get('phone')
        order.comment = request.form.get('comment')
        order.repair = request.form.get('repair')
        order.parts = request.form.get('parts')
        price = request.form.get('price')
        order.price = float(price) if price else None
        db.session.commit()
        flash('Заявку оновлено!', 'success')
        return redirect(url_for('admin.admin_orders'))
    return render_template('admin/edit_order.html', order=order)

@admin.route('/order_status/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    employees = Employee.query.order_by(Employee.name).all()
    if request.method == 'POST':
        order.status = request.form.get('status')
        emp_id = request.form.get('employee_id')
        order.employee_id = int(emp_id) if emp_id else None
        db.session.commit()
        flash('Заявку оновлено!', 'success')
        return redirect(url_for('admin.admin_orders'))
    return render_template('admin/order_status.html', order=order, employees=employees)

@admin.route('/order_calculate/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_calculate(order_id):
    order = Order.query.get_or_404(order_id)
    # Брати всіх користувачів з роллю "Працівник" (і не адмінів)
    employees = User.query.filter(User.role == 'Майстер', User.is_admin == False).order_by(User.last_name, User.first_name).all()
    services = Service.query.all()
    service = next((s for s in services if s.title == order.repair), None)
    promotion = service.promotion if service and service.promotion_id else None
    if request.method == 'POST':
        order.status = request.form.get('status')
        emp_id = request.form.get('employee_id')
        order.employee_id = int(emp_id) if emp_id else None
        price = request.form.get('price')
        order.price = float(price) if price else None
        db.session.commit()
        flash('Заявку оновлено!', 'success')
        return redirect(url_for('admin.admin_orders'))
    return render_template(
        'admin/order_calculate.html',
        order=order,
        employees=employees,
        services=services,
        promotion=promotion
    )

@admin.route('/edit_book_form', methods=['GET', 'POST'])
@login_required
def edit_book_form():
    settings_path = os.path.join(current_app.static_folder, 'book_form_settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
    else:
        settings = {
            "services": ["Діагностика", "ТО", "Ремонт ходової", "Заміна масла", "Ремонт гальмівної системи", "Інше"],
            "year_min": 1980,
            "year_max": 2030,
            "year_placeholder": "Наприклад: 2015"
        }

    if request.method == 'POST':
        services = request.form.get('services', '').split('\n')
        year_min = int(request.form.get('year_min', 1980))
        year_max = int(request.form.get('year_max', 2030))
        year_placeholder = request.form.get('year_placeholder', 'Наприклад: 2015')
        settings = {
            "services": [s.strip() for s in services if s.strip()],
            "year_min": year_min,
            "year_max": year_max,
            "year_placeholder": year_placeholder
        }
        with open(settings_path, 'w') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        flash('Налаштування форми оновлено!', 'success')
        return redirect(url_for('admin.edit_book_form'))

    return render_template('admin/edit_book_form.html', settings=settings)



@admin.route('/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    services = Service.query.order_by(Service.id.desc()).all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        slug = request.form['slug']
        price_from = float(request.form['price_from'])
        price_to = float(request.form['price_to'])
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.static_folder, 'uploads', image_filename)
            image_file.save(upload_path)
        service = Service(
            title=title,
            description=description,
            slug=slug,
            image=image_filename,
            price_from=price_from,
            price_to=price_to
        )
        db.session.add(service)
        db.session.commit()
        flash('Послугу створено!', 'success')
        return redirect(url_for('admin.admin_services'))
    services = Service.query.order_by(Service.id.desc()).all()
    return render_template('admin/services.html', services=services, promotions=promotions)

@admin.route('/services/delete/<int:service_id>')
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Послугу видалено!', 'info')
    return redirect(url_for('admin.admin_services'))

@admin.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    promotions = Promotion.query.all()
    if request.method == 'POST':
        service.title = request.form['title']
        service.description = request.form['description']
        service.slug = request.form['slug']
        service.price_from = float(request.form['price_from'])
        service.price_to = float(request.form['price_to'])
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.static_folder, 'uploads', image_filename)
            image_file.save(upload_path)
            service.image = image_filename
        promo_id = request.form.get('promotion_id')
        service.promotion_id = int(promo_id) if promo_id else None
        db.session.commit()
        flash('Послугу оновлено!', 'success')
        return redirect(url_for('admin.admin_services'))
    return render_template('admin/edit_service.html', service=service, promotions=promotions)

@admin.route('/promotions', methods=['GET', 'POST'])
@login_required
def admin_promotions():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        slug = request.form['slug']
        price = request.form.get('price')
        end_date = request.form.get('end_date')
        price = float(price) if price else None

        end_date_str = request.form.get('end_date')
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()
            except ValueError:
                flash("Невірний формат дати. Використовуйте дд.мм.рррр", "danger")
                return redirect(request.url)

        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.static_folder, 'uploads', image_filename)
            image_file.save(upload_path)
        promo = Promotion(
            title=title,
            description=description,
            slug=slug,
            image=image_filename,
            price=price,
            end_date=end_date
        )
        db.session.add(promo)
        db.session.commit()
        flash('Акцію створено!', 'success')
        return redirect(url_for('admin.admin_promotions'))

    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    return render_template('admin/promotions.html', promotions=promotions)

@admin.route('/promotions/edit/<int:promo_id>', methods=['GET', 'POST'])
@login_required
def edit_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    if request.method == 'POST':
        promo.title = request.form['title']
        promo.description = request.form['description']
        promo.slug = request.form['slug']
        price = request.form.get('price')
        end_date = request.form.get('end_date')
        promo.price = float(price) if price else None

        end_date_str = request.form.get('end_date')
        if end_date_str:
            try:
                promo.end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()
            except ValueError:
                flash("Невірний формат дати. Використовуйте дд.мм.рррр", "danger")
                return redirect(request.url)
        else:
            promo.end_date = None

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.static_folder, 'uploads', image_filename)
            image_file.save(upload_path)
            promo.image = image_filename
        db.session.commit()
        flash('Акцію оновлено!', 'success')
        return redirect(url_for('admin.admin_promotions'))
    return render_template('admin/edit_promotions.html', promo=promo)

@admin.route('/promotions/delete/<int:promo_id>', methods=['GET', 'POST'])
@login_required
def delete_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    flash('Акцію видалено!', 'success')
    return redirect(url_for('admin.admin_promotions'))

@admin.route('/news', methods=['GET', 'POST'])
@login_required
def admin_news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_str = request.form['date']
        slug = request.form['slug']
        try:
            date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            flash("Невірний формат дати. Використовуйте дд.мм.рррр", "danger")
            return redirect(request.url)
        news = News(title=title, description=description, date=date, slug=slug)
        db.session.add(news)
        db.session.commit()
        flash('Новину додано!', 'success')
        return redirect(url_for('admin.admin_news'))
    news_list = News.query.order_by(News.date.desc()).all()
    return render_template('admin/news.html', news_list=news_list)

# --- Редагування новини ---
@admin.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    if request.method == 'POST':
        news.title = request.form['title']
        news.description = request.form['description']
        news.slug = request.form['slug']
        date_str = request.form['date']
        try:
            news.date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            flash("Невірний формат дати. Використовуйте дд.мм.рррр", "danger")
            return redirect(request.url)
        db.session.commit()
        flash('Новину оновлено!', 'success')
        return redirect(url_for('admin.admin_news'))
    return render_template('admin/edit_news.html', news=news)


@admin.route('/news/delete/<int:news_id>')
@login_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('Новину видалено!', 'success')
    return redirect(url_for('admin.admin_news'))

@admin.route('/contacts')
@login_required
def admin_contacts():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contacts.html', messages=messages)

@admin.route('/contacts/read/<int:msg_id>')
@login_required
def mark_contact_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.admin_contacts'))

@admin.route('/contacts/delete/<int:msg_id>')
@login_required
def delete_contact(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(url_for('admin.admin_contacts'))

@admin.route('/assets', methods=['GET', 'POST'])
@login_required
def admin_assets():
    edit_id = request.args.get('edit')
    delete_id = request.args.get('delete')
    assets = MaterialAsset.query.all()

    # Видалення
    if delete_id:
        asset = MaterialAsset.query.get_or_404(delete_id)
        if asset.photo:
            photo_path = os.path.join(current_app.static_folder, 'assets_photos', asset.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        db.session.delete(asset)
        db.session.commit()
        flash('Матеріальну цінність видалено!', 'success')
        return redirect(url_for('admin.admin_assets'))

    # Редагування
    edit_asset = None
    if edit_id:
        edit_asset = MaterialAsset.query.get_or_404(edit_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        price = request.form.get('price', '').strip()
        quantity = request.form.get('quantity', '').strip()
        photo_file = request.files.get('photo')
        photo_url = request.form.get('photo_url', '').strip()
        asset_id = request.form.get('asset_id')
        photo_filename = None

        # if photo_file and photo_file.filename:
        #     photo_filename = secure_filename(photo_file.filename)
        #     photo_folder = os.path.join(current_app.static_folder, 'assets_photos')
        #     os.makedirs(photo_folder, exist_ok=True)
        #     photo_path = os.path.join(photo_folder, photo_filename)
        #     photo_file.save(photo_path)
        # elif photo_url:
        if photo_url:
            try:
                photo_filename = os.path.basename(photo_url.split("?")[0])
                photo_folder = os.path.join(current_app.static_folder, 'assets_photos')
                os.makedirs(photo_folder, exist_ok=True)
                photo_path = os.path.join(photo_folder, photo_filename)
                r = requests.get(photo_url, timeout=10)
                # Перевірка, що це зображення і не порожнє
                if r.status_code == 200 and r.headers.get('Content-Type', '').startswith('image/'):
                    with open(photo_path, 'wb') as f:
                        f.write(r.content)
                    if os.path.getsize(photo_path) > 0:
                        asset.photo = photo_filename
                    else:
                        os.remove(photo_path)
                        flash('Фото з URL порожнє або пошкоджене.', 'danger')
                else:
                    flash('Не вдалося завантажити фото з URL або це не зображення.', 'danger')
            except Exception as e:
                flash('Помилка при завантаженні фото з URL: ' + str(e), 'danger')

        if asset_id:  # Оновлення існуючого
            asset = MaterialAsset.query.get_or_404(asset_id)
            asset.name = name
            asset.code = code
            asset.price = float(price)
            asset.quantity = int(quantity)
            # Оновлення фото тільки якщо є новий файл або новий URL
            if photo_file and photo_file.filename:
                # Видалити старе фото
                if asset.photo:
                    old_photo_path = os.path.join(current_app.static_folder, 'assets_photos', asset.photo)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)
                photo_filename = secure_filename(photo_file.filename)
                photo_folder = os.path.join(current_app.static_folder, 'assets_photos')
                os.makedirs(photo_folder, exist_ok=True)
                photo_path = os.path.join(photo_folder, photo_filename)
                photo_file.save(photo_path)
                asset.photo = photo_filename
            elif photo_url:
                try:
                    # Видалити старе фото
                    if asset.photo:
                        old_photo_path = os.path.join(current_app.static_folder, 'assets_photos', asset.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    photo_filename = os.path.basename(photo_url.split("?")[0])
                    photo_folder = os.path.join(current_app.static_folder, 'assets_photos')
                    os.makedirs(photo_folder, exist_ok=True)
                    photo_path = os.path.join(photo_folder, photo_filename)
                    r = requests.get(photo_url, timeout=10)
                    # Перевірка, що це дійсно зображення і файл не порожній
                    if r.status_code == 200 and r.headers.get('Content-Type', '').startswith('image/'):
                        with open(photo_path, 'wb') as f:
                            f.write(r.content)
                        asset.photo = photo_filename
                    else:
                        flash('Не вдалося завантажити фото з URL або це не зображення.', 'danger')
                except Exception:
                    flash('Помилка при завантаженні фото з URL', 'danger')
            # Якщо не вибрано нове фото і не вказано новий URL — залишаємо старе фото
            db.session.commit()
            flash('Матеріальну цінність оновлено!', 'success')
            return redirect(url_for('admin.admin_assets'))
        else:  # Додавання нового
            photo_filename = None
            if photo_file and photo_file.filename:
                photo_filename = secure_filename(photo_file.filename)
                photo_folder = os.path.join(current_app.static_folder, 'assets_photos')
                os.makedirs(photo_folder, exist_ok=True)
                photo_path = os.path.join(photo_folder, photo_filename)
                photo_file.save(photo_path)
            asset = MaterialAsset(
                name=name,
                code=code,
                price=float(price),
                quantity=int(quantity),
                photo=photo_filename
            )
            db.session.add(asset)
            db.session.commit()
            flash('Матеріальну цінність додано!', 'success')
            return redirect(url_for('admin.admin_assets'))

    return render_template('admin/asset.html', assets=assets, edit_asset=edit_asset)

@admin.route('/assets/import', methods=['GET', 'POST'])
def admin_import_assets():
    if request.method == 'POST':
        file = request.files.get('excel')
        if not file:
            flash('Оберіть Excel-файл!', 'danger')
            return redirect(url_for('admin.import_assets'))
        try:
            df = pd.read_excel(file)
            imported = 0
            for _, row in df.iterrows():
                name = str(row.get('name', '')).strip()
                code = str(row.get('code', '')).strip()
                try:
                    price = float(row.get('price', ''))
                except Exception:
                    price = None
                try:
                    quantity = int(row.get('quantity', 0))
                except Exception:
                    quantity = 0
                # Перевірка на валідність
                if not name or not code or price is None or pd.isna(price):
                    continue  # пропустити невалідний рядок
                asset = MaterialAsset(
                    name=name,
                    code=code,
                    price=price,
                    quantity=quantity,
                    photo=None
                )
                db.session.add(asset)
                imported += 1
            db.session.commit()
            flash(f'Імпортовано успішно! Додано: {imported}', 'success')
            return redirect(url_for('admin.admin_assets'))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка імпорту: {e}', 'danger')
    return render_template('admin/import_assets.html')

@admin.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Ви вийшли з адмінки', 'info')
    return redirect(url_for('main.index'))

@admin.route('/sitemap', methods=['GET', 'POST'])
@login_required
def edit_sitemap():
    if request.method == 'POST':
        url = request.form.get('url')
        lastmod = request.form.get('lastmod')
        changefreq = request.form.get('changefreq')
        priority = request.form.get('priority')
        if url:
            page = SitemapPage(url=url, lastmod=lastmod, changefreq=changefreq, priority=priority)
            db.session.add(page)
            db.session.commit()
            flash('Сторінку додано до sitemap!', 'success')
        return redirect(url_for('admin.edit_sitemap'))
    pages = SitemapPage.query.all()
    return render_template('admin/edit_sitemap.html', pages=pages, now=datetime.utcnow)

@admin.route('/sitemap/delete/<int:page_id>', methods=['POST'])
@login_required
def delete_sitemap_page(page_id):
    page = SitemapPage.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash('Сторінку видалено з sitemap!', 'success')
    return redirect(url_for('admin.edit_sitemap'))

@admin.route('/robots', methods=['GET', 'POST'])
@login_required
def edit_robots():
    robots = RobotsTxt.query.first()
    if not robots:
        robots = RobotsTxt(content="")
        db.session.add(robots)
    if request.method == 'POST':
        robots.content = request.form.get('content', '')
        db.session.commit()
        flash('robots.txt оновлено!', 'success')
        return redirect(url_for('admin.edit_robots'))
    return render_template('admin/edit_robots.html', robots=robots)