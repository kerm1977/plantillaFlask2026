import bcrypt
from db import db
from models import User
from config import Config

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def inject_superusers():
    """Inyecta superusuarios desde configuración si no existen."""
    for email in Config.SUPERUSER_EMAILS:
        email = email.lower().strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            new_super = User(
                role='Superusuario',
                weight=100,
                name='Kenneth',
                last_name_1='Ruiz',
                last_name_2='Matamoros',
                email=email,
                password_hash=hash_password(Config.SUPERUSER_PASSWORD),
                status='Activo',
                avatar='default.png'
            )
            db.session.add(new_super)
            print(f"--- Superusuario inyectado: {email} ---")
        else:
            if user.role != 'Superusuario' or user.weight != 100:
                 user.role = 'Superusuario'
                 user.weight = 100
                 db.session.add(user)
                 print(f"--- Rol corregido a Superusuario para: {email} ---")

    db.session.commit()