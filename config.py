import os
import secrets
from datetime import timedelta


def _get_or_create_secret_key():
    """Obtiene la SECRET_KEY de una variable de entorno, o la persiste en
    un archivo local para que NO cambie entre reinicios del servidor.
    Si la clave cambiara en cada reinicio (como ocurria antes con
    os.urandom() evaluado en cada arranque), todas las sesiones de los
    usuarios logueados se invalidan silenciosamente, obligandolos a
    iniciar sesion de nuevo (a veces hasta 2 veces si el servidor se
    reinicia justo despues del primer login)."""
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key

    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret_key')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                existing = f.read().strip()
                if existing:
                    return existing
        except Exception:
            pass

    new_key = secrets.token_hex(32)
    try:
        with open(key_file, 'w') as f:
            f.write(new_key)
    except Exception:
        pass
    return new_key


class Config:
    SECRET_KEY = _get_or_create_secret_key()
    # Superusuarios
    SUPERUSER_EMAILS = os.environ.get('SUPERUSER_EMAILS', 'kenth1977@gmail.com,lthikingcr@gmail.com').split(',')
    SUPERUSER_PASSWORD = os.environ.get('SUPERUSER_PASSWORD')
    
    # Base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Desactivar caché de templates para desarrollo
    TEMPLATES_AUTO_RELOAD = True
    
    # Seguridad
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Sesión permanente de 24 horas
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
