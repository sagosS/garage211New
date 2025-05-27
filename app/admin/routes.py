import os
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash
from app.models import User, Client, Service
from app.extensions import db
from . import admin
from werkzeug.utils import secure_filename
import json

@admin.route('/')
@login_required
def admin_index():
    workers_count = User.query.filter_by(is_admin=False).count()
    clients_count = Client.query.count()
    return render_template('admin/index.html', workers_count=workers_count, clients_count=clients_count)

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
        selected = request.form.getlist('project_images')
        idx = request.form.get('idx')
        if idx:  # Редагування
            try:
                idx = int(idx)
                if name and selected and 0 <= idx < len(projects):
                    projects[idx] = {'name': name, 'images': selected}
                    with open(projects_json, 'w') as f:
                        json.dump(projects, f, ensure_ascii=False)
                    flash('Проєкт оновлено!', 'success')
                    return redirect(url_for('admin.admin_projects'))
            except Exception:
                flash('Помилка редагування.', 'danger')
        else:  # Додавання
            if name and selected:
                projects.append({'name': name, 'images': selected})
                with open(projects_json, 'w') as f:
                    json.dump(projects, f, ensure_ascii=False)
                flash('Проєкт створено!', 'success')
                return redirect(url_for('admin.admin_projects'))
            else:
                flash('Вкажіть назву та виберіть картинки.', 'danger')

    return render_template('admin/projects.html', images=images, projects=projects, edit_project=edit_project)

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
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
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
            image=image_filename,
            price_from=price_from,
            price_to=price_to
        )
        db.session.add(service)
        db.session.commit()
        flash('Послугу створено!', 'success')
        return redirect(url_for('admin.admin_services'))

    services = Service.query.order_by(Service.id.desc()).all()
    return render_template('admin/services.html', services=services)

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
    if request.method == 'POST':
        service.title = request.form['title']
        service.description = request.form['description']
        service.price_from = float(request.form['price_from'])
        service.price_to = float(request.form['price_to'])
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.static_folder, 'uploads', image_filename)
            image_file.save(upload_path)
            service.image = image_filename
        db.session.commit()
        flash('Послугу оновлено!', 'success')
        return redirect(url_for('admin.admin_services'))
    return render_template('admin/edit_service.html', service=service)

@admin.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Ви вийшли з адмінки', 'info')
    return redirect(url_for('main.index'))