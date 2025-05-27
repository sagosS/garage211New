from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, login_required, logout_user
from app.models import User
from werkzeug.security import check_password_hash
from app.main import main
from app.forms import ApplicationForm

@main.route('/')
def index():
    return render_template('index.html', title="Головна сторінка")

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
        flash('Невірний логін або пароль')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з кабінету', 'info')
    return redirect(url_for('main.index'))

@main.route('/cabinet')
@login_required
def worker_cabinet():
    return render_template('worker_cabinet.html')

@main.route('/news')
def news():
    news = [
        {
            "id": 1,
            "title": "Відкриття нового сервісу",
            "date": "2025-05-20",
            "preview": "Ми відкрили новий сучасний сервіс для наших клієнтів!",
            "image_url": url_for('static', filename='images/news1.jpg')
        },
        {
            "id": 2,
            "title": "Весняна акція",
            "date": "2025-04-15",
            "preview": "Знижки на всі види робіт до кінця квітня!",
            "image_url": url_for('static', filename='images/news2.jpg')
        },
        # ...ще новини...
    ]
    return render_template('news.html', title="Новини", news=news)

@main.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        # Тут обробка форми, наприклад, збереження в БД чи надсилання email
        flash('Ваша заявка прийнята!', 'success')
        return redirect(url_for('main.book'))
    return render_template('book.html')

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
    promotions = [
        {
            "id": 1,
            "title": "Знижка 20% на діагностику",
            "date": "2025-06-01",
            "preview": "Отримайте знижку 20% на повну діагностику авто до кінця місяця!",
            "image_url": url_for('static', filename='images/promo1.jpg')
        },
        {
            "id": 2,
            "title": "Безкоштовна заміна масла",
            "date": "2025-05-15",
            "preview": "При замовленні ТО — заміна масла безкоштовно!",
            "image_url": url_for('static', filename='images/promo2.jpg')
        },
        # ...ще акції...
    ]
    return render_template('promotions.html', promotions=promotions)

@main.route('/promotions/<int:promo_id>')
def promotion_detail(promo_id):
    promotions = [
        {
            "id": 1,
            "title": "Знижка 20% на діагностику",
            "date": "2025-06-01",
            "content": "Детальний опис акції 1...",
            "image_url": url_for('static', filename='images/promo1.jpg')
        },
        {
            "id": 2,
            "title": "Безкоштовна заміна масла",
            "date": "2025-05-15",
            "content": "Детальний опис акції 2...",
            "image_url": url_for('static', filename='images/promo2.jpg')
        },
        # ...ще акції...
    ]
    promo = next((p for p in promotions if p["id"] == promo_id), None)
    if not promo:
        abort(404)
    return render_template('promotion_detail.html', promo=promo)

@main.route('/gallery')
def gallery():
    images = [
        {"thumb": "thumb1.jpg", "full": "full1.jpg", "caption": "Станція №1"},
        {"thumb": "thumb2.jpg", "full": "full2.jpg", "caption": "Станція №2"},
        {"thumb": "thumb3.jpg", "full": "full3.jpg", "caption": "Наші майстри"},
        # ...ще фото...
    ]
    return render_template('gallery.html', title="Галерея", images=images)

@main.route('/contacts')
def contacts():
    return render_template('contacts.html', title="Контакти")
