from app.extensions import db

class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(128), nullable=True)
    price = db.Column(db.Float, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    slug = db.Column(db.String(128), unique=True, nullable=False)