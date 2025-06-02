from app.extensions import db

class MetaTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(128), unique=True, nullable=False)  # наприклад, 'main', 'services', 'contacts'
    title = db.Column(db.String(256))
    description = db.Column(db.String(512))
    keywords = db.Column(db.String(512))