from db import db
from datetime import datetime

class Cotizador(db.Model):
    __tablename__ = 'cotizador'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True)
    clave_acceso = db.Column(db.String(100), nullable=False)
    titulo = db.Column(db.String(500))
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    lugares = db.relationship('CotizadorLugar', backref='cotizador', lazy=True, cascade='all, delete-orphan')

class CotizadorLugar(db.Model):
    __tablename__ = 'cotizador_lugar'
    id = db.Column(db.Integer, primary_key=True)
    cotizador_id = db.Column(db.Integer, db.ForeignKey('cotizador.id'), nullable=False)
    nombre = db.Column(db.String(500), nullable=False)
    provincia = db.Column(db.String(100))
    duracion = db.Column(db.String(20), default='1_dia')  # 1_dia o multiples_dias
    fecha_ida = db.Column(db.String(20))
    fecha_regreso = db.Column(db.String(20))
    hora = db.Column(db.String(10))
    maps_ida = db.Column(db.String(1000))
    maps_regreso = db.Column(db.String(1000))
    moneda = db.Column(db.String(20), default='colones')
    precio = db.Column(db.Float)
    order = db.Column(db.Integer, default=0)
