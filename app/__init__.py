from flask import Flask
from app.extensions import db, migrate, login_manager
from app.models import User, Client
from app.static_data import (
    GARAGE_NAME, GARAGE_ADDRESS, GARAGE_PHONE, GARAGE_EMAIL,
    SOCIAL_FACEBOOK, SOCIAL_INSTAGRAM, SOCIAL_TELEGRAM, SOCIAL_VIBER
)
from werkzeug.security import generate_password_hash

def create_admin():
    from app.models import User
    from app.extensions import db
    admin_phone = "+380000000000"
    admin_password = "123456"  # Змініть після першого входу!
    if not User.query.filter_by(phone_number=admin_phone).first():
        admin = User(
            phone_number=admin_phone,
            password=generate_password_hash(admin_password),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

def create_app():
    app = Flask(__name__)

    @app.context_processor
    def inject_garage_data():
        return dict(
            GARAGE_NAME=GARAGE_NAME,
            GARAGE_ADDRESS=GARAGE_ADDRESS,
            GARAGE_PHONE=GARAGE_PHONE,
            GARAGE_EMAIL=GARAGE_EMAIL,
            SOCIAL_FACEBOOK=SOCIAL_FACEBOOK,
            SOCIAL_INSTAGRAM=SOCIAL_INSTAGRAM,
            SOCIAL_TELEGRAM=SOCIAL_TELEGRAM,
            SOCIAL_VIBER=SOCIAL_VIBER
        )
    
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # маршрут для логіну  # type: ignore

    with app.app_context():
        create_admin()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    # Функція для завантаження користувача за ID

    # Реєстрація blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app
