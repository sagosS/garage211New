from app.extensions import db

class ImageAlt(db.Model):
    __tablename__ = 'image_alt'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), unique=True, nullable=False)
    alt = db.Column(db.String(512), nullable=False)