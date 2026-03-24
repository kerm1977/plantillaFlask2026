# app.py
import os
from flask import Flask
from db import db, configure_db_uri
from routes import bp
from users import inject_superusers
from music_bp import music_bp  # <-- IMPORTANTE: Importamos el blueprint de música

import models  # <-- ESTA LÍNEA ES CRÍTICA: Obliga a leer los modelos antes de crear la BD

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_super_secreta_pwa')
    
    # Configuración inteligente de Base de Datos
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_db_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar la base de datos con la app
    db.init_app(app)
    
    # Registrar las rutas
    app.register_blueprint(bp)
    app.register_blueprint(music_bp) # <-- NUEVO: Registramos el blueprint de música


    # Crear tablas e inyectar usuarios dentro del contexto de la aplicación
    with app.app_context():
        # Crea el archivo local_app.db y todas sus tablas si no existen
        db.create_all()
        
        # Inyecta automáticamente los superusuarios
        inject_superusers()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)