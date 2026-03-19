import bcrypt
from db import db
from models import User

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def inject_superusers():
    """Inyecta 2 superusuarios intocables si no existen en la base de datos."""
    # CORRECCIÓN: Se actualizan los correos específicos solicitados
    super_emails = ['kenth1977@gmail.com', 'lthikingcr@gmail.com']
    
    for email in super_emails: # Iterar sobre la lista
        email = email.lower() # Asegurar minúsculas individualmente
        user = User.query.filter_by(email=email).first()
        if not user:
            new_super = User(
                role='Superusuario',
                weight=100, # Peso máximo
                name='Kenneth',
                last_name_1='Ruiz',
                last_name_2='Matamoros',
                email=email,
                # Contraseña personalizada y segura solicitada
                password_hash=hash_password('CR129x7848n'),
                status='Activo',
                avatar='default.png'
            )
            db.session.add(new_super)
            print(f"--- Superusuario inyectado: {email} ---")
        else:
            # CORRECCIÓN: Si ya existen pero tienen el rol equivocado, actualizarlo.
            if user.role != 'Superusuario' or user.weight != 100:
                 user.role = 'Superusuario'
                 user.weight = 100
                 db.session.add(user) # Marcar para actualizar
                 print(f"--- Rol corregido a Superusuario para: {email} ---")

    db.session.commit()