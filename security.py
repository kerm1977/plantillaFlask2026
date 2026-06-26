import re
from functools import wraps
from flask import session, jsonify

# Rate limiting simple en memoria
_login_attempts = {}

def check_rate_limit(identifier, max_attempts=5, window_minutes=15):
    key = f"{identifier}_login"
    now = __import__('time').time()
    
    if key not in _login_attempts:
        _login_attempts[key] = []
    
    # Limpiar intentos viejos
    _login_attempts[key] = [t for t in _login_attempts[key] 
                            if now - t < window_minutes * 60]
    
    if len(_login_attempts[key]) >= max_attempts:
        return False
    
    _login_attempts[key].append(now)
    return True

def require_superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import Config
        if session.get('email') not in Config.SUPERUSER_EMAILS:
            return jsonify({'error': 'No autorizado'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Mínimo 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "Debe incluir mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "Debe incluir minúscula"
    if not re.search(r'[0-9]', password):
        return False, "Debe incluir número"
    return True, "Válida"
