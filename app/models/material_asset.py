from app.extensions import db

class MaterialAsset(db.Model):
    __tablename__ = 'material_asset'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # ДОДАНО
    photo = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<MaterialAsset {self.name}>"