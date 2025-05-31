from app.extensions import db
from datetime import datetime

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # дата заявки
    desired_date = db.Column(db.String(32))  # бажана дата обслуговування
    delivery_date = db.Column(db.String(32))  # дата здачі (можна додати окремо)
    brand = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64))
    year = db.Column(db.String(8))
    vin = db.Column(db.String(32))
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text)
    repair = db.Column(db.String(128))
    parts = db.Column(db.String(128))
    price = db.Column(db.Float)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    status = db.Column(db.String(32), default='в обробці')
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    employee = db.relationship('Employee', backref='orders')

    client = db.relationship('Client', backref='orders')