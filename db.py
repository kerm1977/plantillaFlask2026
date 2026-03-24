import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def configure_db_uri():
    """
    Detecta el entorno para asignar SQLite local o MySQL.
    Si está en PythonAnywhere pero no hay contraseña configurada, usa SQLite como respaldo seguro.
    """
    # IMPORTANTE: Agregamos "and 'DB_PASS' in os.environ" para que NO intente conectar a MySQL si no hemos puesto la contraseña real
    if 'PYTHONANYWHERE_DOMAIN' in os.environ and 'DB_PASS' in os.environ:
        user = os.environ.get('DB_USER', 'kenth1977')
        password = os.environ.get('DB_PASS')
        host = os.environ.get('DB_HOST', f'{user}.mysql.pythonanywhere-services.com')
        db_name = os.environ.get('DB_NAME', f'{user}$default')
        return f'mysql+pymysql://{user}:{password}@{host}/{db_name}'
    
    elif 'TAILSCALE_IP' in os.environ:
        # Configuración para red local/Tailscale (MySQL)
        host = os.environ.get('TAILSCALE_IP')
        return f'mysql+pymysql://root:root@{host}/pwa_db'
    
    else:
        # Entorno local por defecto (o Fallback seguro en la nube) -> SQLite
        basedir = os.path.abspath(os.path.dirname(__file__))
        return 'sqlite:///' + os.path.join(basedir, 'local_app.db')