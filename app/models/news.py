from app.extensions import db

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    slug = db.Column(db.String(128), unique=True, nullable=False)  # ДОДАЙТЕ ЦЕ ПОЛЕ