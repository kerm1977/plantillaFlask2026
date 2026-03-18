# users.py
import bcrypt
from db import db
from models import User

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def inject_superusers():
    """Inyecta 2 superusuarios intocables si no existen en la base de datos."""
    super_emails = ['admin1@sistema.local', 'admin2@sistema.local']
    for email in super_emails:
        user = User.query.filter_by(email=email).first()
        if not user:
            new_super = User(
                role='Superusuario',
                weight=100, # Peso máximo, no pueden ser editados por otros supers
                name='Super',
                last_name_1='Administrador',
                last_name_2='Sistema',
                email=email,
                password_hash=hash_password('Root#Admin2026'),
                status='Activo'
            )
            db.session.add(new_super)
    db.session.commit()