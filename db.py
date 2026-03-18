import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def configure_db_uri():
    """
    Detecta el entorno para asignar SQLite local o MySQL en red/PythonAnywhere.
    """
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        # Configuración para PythonAnywhere (MySQL)
        user = os.environ.get('DB_USER', 'tu_usuario')
        password = os.environ.get('DB_PASS', 'tu_pass')
        host = os.environ.get('DB_HOST', f'{user}.mysql.pythonanywhere-services.com')
        db_name = os.environ.get('DB_NAME', f'{user}$default')
        return f'mysql+pymysql://{user}:{password}@{host}/{db_name}'
    
    elif 'TAILSCALE_IP' in os.environ:
        # Configuración para red local/Tailscale (MySQL)
        host = os.environ.get('TAILSCALE_IP')
        return f'mysql+pymysql://root:root@{host}/pwa_db'
    
    else:
        # Entorno de desarrollo local por defecto (SQLite)
        basedir = os.path.abspath(os.path.dirname(__file__))
        return 'sqlite:///' + os.path.join(basedir, 'local_app.db')