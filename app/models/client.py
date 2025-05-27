from flask_login import UserMixin
from app.extensions import db

class Client(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<Client {self.phone_number}>'