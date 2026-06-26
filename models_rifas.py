from db import db
from datetime import datetime

class Raffle(db.Model):
    __tablename__ = 'raffle'
    id = db.Column(db.Integer, primary_key=True)
    raffle_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    prize = db.Column(db.String(500), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    raffle_date = db.Column(db.Date, nullable=False)
    raffle_time = db.Column(db.String(50))
    image_filename = db.Column(db.String(255), nullable=False)
    winning_numbers = db.Column(db.Text, default='[]')
    sinpe_name_default = db.Column(db.String(200))
    sinpe_phone_default = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    selections = db.relationship('RaffleSelection', backref='raffle', lazy=True, cascade='all, delete-orphan')

class RaffleSelection(db.Model):
    __tablename__ = 'raffle_selection'
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'), nullable=False)
    number = db.Column(db.String(5), nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)
    customer_cedula = db.Column(db.String(50))
    pin = db.Column(db.String(10), nullable=False)
    selection_password = db.Column(db.String(100), nullable=False, default='', server_default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_canceled = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50), default='No especificado')
    sinpe_name = db.Column(db.String(200))
    sinpe_phone = db.Column(db.String(50))
    __table_args__ = (db.UniqueConstraint('raffle_id', 'number', name='_raffle_number_uc'),)
