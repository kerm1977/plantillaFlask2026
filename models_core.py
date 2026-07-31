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
    
    whatsapp = db.Column(db.String(20))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    address = db.Column(db.String(255))
    institution = db.Column(db.String(200))
    other_info = db.Column(db.Text)
    
    reset_token = db.Column(db.String(64))
    reset_expires = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster = db.Column(db.String(255)) 
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
    logistica_segura = db.Column(db.Boolean, default=False)
    is_sold_out = db.Column(db.Boolean, default=False)

    dias = db.Column(db.Integer, default=1)
    fecha_unica = db.Column(db.String(50))
    fecha_inicio = db.Column(db.String(50))
    fecha_regreso = db.Column(db.String(50))
    hora_salida = db.Column(db.String(50))
    lugar_salida = db.Column(db.String(200))
    puntos_recogida = db.Column(db.Text)
    itinerario = db.Column(db.Text)
    incluye = db.Column(db.Text) 
    gpx_filename = db.Column(db.String(255))
    gpx_password = db.Column(db.String(50))
    organicmaps_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventDateChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    fecha_anterior = db.Column(db.String(50))
    fecha_nueva = db.Column(db.String(50))
    usuario = db.Column(db.String(200))
    cambiado_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    type_notif = db.Column(db.String(50)) 
    message = db.Column(db.Text)

class SiteContent(db.Model):
    __tablename__ = 'site_content'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class Hiker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    pasaporte = db.Column(db.String(50))
    tipo_sangre = db.Column(db.String(10))
    fecha_nacimiento = db.Column(db.Date) 
    alergias = db.Column(db.Text)
    enfermedades_cronicas = db.Column(db.Text)
    contacto_emergencia_nombre = db.Column(db.String(200))
    contacto_emergencia_telefono = db.Column(db.String(20))
    pin_secreto = db.Column(db.String(20), unique=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    hiker_id = db.Column(db.Integer, db.ForeignKey('hiker.id'), nullable=False)
    estado_pago = db.Column(db.String(50), default='Pendiente')
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
