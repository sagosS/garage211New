from flask_login import UserMixin
from app.extensions import db

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(128), nullable=True)
    price_from = db.Column(db.Float, nullable=False)
    price_to = db.Column(db.Float, nullable=False)