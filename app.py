# app.py
import os
from flask import Flask
from config import Config
from db import db, configure_db_uri
from routes import bp, inject_site_content
from users import inject_superusers

import models_core, models_forms, models_rifas, models_publicaciones  # Cargar todos los modelos

def _migrate_raffle_selection():
    """Agrega columnas faltantes en raffle_selection sin borrar datos existentes."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(raffle_selection)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        migrations = [
            ("selection_password", "VARCHAR(100) NOT NULL DEFAULT ''"),
            ("customer_cedula",    "VARCHAR(50)"),
            ("sinpe_name",         "VARCHAR(200)"),
            ("sinpe_phone",        "VARCHAR(50)"),
            ("payment_method",     "VARCHAR(50) DEFAULT 'No especificado'"),
            ("is_canceled",        "BOOLEAN DEFAULT 0"),
        ]
        for col, definition in migrations:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE raffle_selection ADD COLUMN {col} {definition}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_raffle_selection: {e}")


def _migrate_user_reset():
    """Agrega columnas de recuperación de contraseña al modelo User."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        for col, definition in [("reset_token", "VARCHAR(64)"), ("reset_expires", "VARCHAR(30)")]:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {definition}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_user_reset: {e}")


def _migrate_publicacion():
    """Agrega columnas de redes sociales a la tabla publicacion."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(publicacion)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("telefono",   "VARCHAR(50)"),
            ("whatsapp",   "VARCHAR(50)"),
            ("facebook",   "VARCHAR(300)"),
            ("instagram",  "VARCHAR(300)"),
            ("tiktok",     "VARCHAR(300)"),
            ("youtube",    "VARCHAR(300)"),
            ("rifa_url_2",          "VARCHAR(500)"),
            ("colaborar_detalle",   "VARCHAR(300) DEFAULT 'Apoyo Sueños de Vida'"),
        ]
        for col, definition in migrations:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE publicacion ADD COLUMN {col} {definition}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_publicacion: {e}")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuración inteligente de Base de Datos
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_db_uri()

    # Inicializar la base de datos con la app
    db.init_app(app)
    
    # Registrar las rutas
    app.register_blueprint(bp)


    # Crear tablas e inyectar usuarios dentro del contexto de la aplicación
    with app.app_context():
        # Crea el archivo local_app.db y todas sus tablas si no existen
        db.create_all()
        
        # Migración automática: agrega columnas faltantes en raffle_selection
        _migrate_raffle_selection()
        # Migración: columnas de recuperación de contraseña
        _migrate_user_reset()
        # Migración: redes sociales en publicacion
        _migrate_publicacion()
        
        # Inyecta automáticamente los superusuarios
        inject_superusers()
        # Inyecta el contenido por defecto del sitio si no existe
        inject_site_content()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)