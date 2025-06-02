from app.extensions import db

class SitemapPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256), unique=True, nullable=False)
    lastmod = db.Column(db.String(32))
    changefreq = db.Column(db.String(16), default='weekly')
    priority = db.Column(db.Float, default=0.8)