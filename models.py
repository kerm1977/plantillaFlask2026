# models.py
from db import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default='Usuario') 
    weight = db.Column(db.Integer, default=1) 
    avatar = db.Column(db.String(255), default='default.png')
    name = db.Column(db.String(100), nullable=False)
    last_name_1 = db.Column(db.String(100), nullable=False)
    last_name_2 = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Activo') 
    
    # Campos de Información Adicional (Sincronizados con routes.py)
    whatsapp = db.Column(db.String(20))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    address = db.Column(db.String(255))
    institution = db.Column(db.String(200))
    other_info = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster = db.Column(db.String(255)) # Nombre del archivo en static/uploads
    nombre_lugar = db.Column(db.String(200), nullable=False)
    dificultad = db.Column(db.String(50))
    actividad = db.Column(db.String(100))
    moneda = db.Column(db.String(5))
    precio = db.Column(db.Integer)
    reserva = db.Column(db.Integer)
    capacidad = db.Column(db.String(50))
    sinpe = db.Column(db.String(100))
    cuenta = db.Column(db.String(200))
    solo_chat = db.Column(db.Boolean, default=False)
    
    # Logística
    dias = db.Column(db.Integer, default=1)
    fecha_unica = db.Column(db.String(50))
    fecha_inicio = db.Column(db.String(50))
    fecha_regreso = db.Column(db.String(50))
    hora_salida = db.Column(db.String(50))
    lugar_salida = db.Column(db.String(200))
    puntos_recogida = db.Column(db.Text)
    itinerario = db.Column(db.Text)
    incluye = db.Column(db.Text) # Guardado como string separado por comas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    type_notif = db.Column(db.String(50)) 
    message = db.Column(db.Text)


class Song(db.Model):
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    cover_filename = db.Column(db.String(255), default='logo.png')