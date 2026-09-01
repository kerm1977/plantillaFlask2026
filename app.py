# app.py
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

import os
from flask import Flask, request
from config import Config
from db import db, configure_db_uri
from routes import bp, inject_site_content
from routes.cotizador import bp as bp_cotizador
from users import inject_superusers
from socketio_instance import socketio
from migrations import run_migrations

import models_core, models_forms, models_rifas, models_publicaciones, models_cotizador, models_home_media  # Cargar todos los modelos


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Agregar logging para debug de templates
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Configuración inteligente de Base de Datos
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_db_uri()

    # Inicializar la base de datos con la app
    db.init_app(app)

    # Inicializar Socket.IO (edición colaborativa en tiempo real de notas)
    socketio.init_app(app)

    # Registrar las rutas
    app.register_blueprint(bp)
    app.register_blueprint(bp_cotizador)

    @app.after_request
    def no_cache_private_pages(response):
        if not request.path.startswith('/static'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        return response

    @app.template_filter('colones')
    def colones_filter(value):
        try:
            return f"₡{int(float(value)):,}"
        except (ValueError, TypeError, AttributeError):
            return value

    # Crear tablas e inyectar usuarios dentro del contexto de la aplicación
    with app.app_context():
        # Crea el archivo local_app.db y todas sus tablas si no existen
        db.create_all()
        
        # Aplicar migraciones manuales
        run_migrations()

        # Inyecta automáticamente los superusuarios
        inject_superusers()
        # Inyecta el contenido por defecto del sitio si no existe
        inject_site_content()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5050))
    socketio.run(app, debug=Config.DEBUG, host='0.0.0.0', port=port, use_reloader=False, allow_unsafe_werkzeug=True)