import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Superusuarios
    SUPERUSER_EMAILS = os.environ.get('SUPERUSER_EMAILS', 'kenth1977@gmail.com,lthikingcr@gmail.com').split(',')
    SUPERUSER_PASSWORD = os.environ.get('SUPERUSER_PASSWORD', 'CR129x7848n')
    
    # Base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Desactivar caché de templates para desarrollo
    TEMPLATES_AUTO_RELOAD = True
    
    # Seguridad
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
