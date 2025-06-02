from app.extensions import db

class MetaTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(128), unique=True, nullable=False)
    title = db.Column(db.String(256))
    description = db.Column(db.String(512))
    keywords = db.Column(db.String(512))
    og_title = db.Column(db.String(256))
    og_description = db.Column(db.Text)
    og_image = db.Column(db.String(256))
    twitter_title = db.Column(db.String(256))
    twitter_description = db.Column(db.Text)
    twitter_image = db.Column(db.String(256))
    schema_org = db.Column(db.Text)