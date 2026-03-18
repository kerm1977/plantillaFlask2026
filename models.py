# modes.py
from db import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default='Usuario') # Superusuario, Administrador, Colaborador, Usuario
    weight = db.Column(db.Integer, default=1) # 100 para superusuarios inyectados
    avatar = db.Column(db.String(255), default='default.png')
    name = db.Column(db.String(100), nullable=False)
    last_name_1 = db.Column(db.String(100), nullable=False)
    last_name_2 = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)
    
    # --- NUEVOS CAMPOS DE INFORMACIÓN ADICIONAL ---
    whatsapp = db.Column(db.String(20))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    address = db.Column(db.Text)
    institution = db.Column(db.String(150))
    other_info = db.Column(db.String(255))
    # ----------------------------------------------
    
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Activo') # Activo, Bloqueado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    type_notif = db.Column(db.String(50)) # Feriado, Evento, etc.
    message = db.Column(db.Text)