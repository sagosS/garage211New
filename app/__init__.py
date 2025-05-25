from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


from app.static_data import (
    GARAGE_NAME, GARAGE_ADDRESS, GARAGE_PHONE, GARAGE_EMAIL,
    SOCIAL_FACEBOOK, SOCIAL_INSTAGRAM, SOCIAL_TELEGRAM, SOCIAL_VIBER
)

db = SQLAlchemy()
migrate = Migrate()

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

    # Реєстрація blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app
