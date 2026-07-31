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


def _migrate_forms_ficha_medica():
    """Agrega columnas de ficha médica a las tablas form y form_response."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "show_ficha_medica" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_ficha_medica BOOLEAN DEFAULT 0")

        cursor.execute("PRAGMA table_info(form_response)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("tipo_sangre",                  "VARCHAR(10)"),
            ("alergias",                     "TEXT"),
            ("enfermedades_cronicas",        "TEXT"),
            ("contacto_emergencia_nombre",   "VARCHAR(200)"),
            ("contacto_emergencia_telefono", "VARCHAR(50)"),
        ]
        for col, definition in migrations:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE form_response ADD COLUMN {col} {definition}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_forms_ficha_medica: {e}")


def _migrate_forms_pasaporte_fecha_nacimiento():
    """Agrega columnas de pasaporte y fecha de nacimiento a las tablas form y form_response."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "show_pasaporte" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_pasaporte BOOLEAN DEFAULT 0")
        if "show_fecha_nacimiento" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_fecha_nacimiento BOOLEAN DEFAULT 0")

        cursor.execute("PRAGMA table_info(form_response)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("pasaporte",               "VARCHAR(50)"),
            ("fecha_nacimiento_dia",    "INTEGER"),
            ("fecha_nacimiento_mes",    "INTEGER"),
            ("fecha_nacimiento_anio",   "INTEGER"),
        ]
        for col, definition in migrations:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE form_response ADD COLUMN {col} {definition}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_forms_pasaporte_fecha_nacimiento: {e}")


def _migrate_hiker_pasaporte():
    """Agrega columna pasaporte a la tabla hiker."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(hiker)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "pasaporte" not in existing_cols:
            cursor.execute("ALTER TABLE hiker ADD COLUMN pasaporte VARCHAR(50)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_hiker_pasaporte: {e}")


def _migrate_form_response_reservation_number():
    """Agrega columna reservation_number a la tabla form_response."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form_response)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "reservation_number" not in existing_cols:
            cursor.execute("ALTER TABLE form_response ADD COLUMN reservation_number VARCHAR(100)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_form_response_reservation_number: {e}")


def _migrate_event_date_changes():
    """Crea tabla event_date_change si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_date_change'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE event_date_change (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    fecha_anterior VARCHAR(50),
                    fecha_nueva VARCHAR(50),
                    usuario VARCHAR(200),
                    cambiado_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(event_id) REFERENCES event (id)
                )
            ''')
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_date_changes: {e}")


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
        # Migración: ficha médica en formularios
        _migrate_forms_ficha_medica()
        # Migración: pasaporte y fecha de nacimiento en formularios
        _migrate_forms_pasaporte_fecha_nacimiento()
        # Migración: pasaporte en hiker
        _migrate_hiker_pasaporte()
        # Migración: reservation_number en form_response
        _migrate_form_response_reservation_number()
        # Migración: historial de cambios de fechas de eventos
        _migrate_event_date_changes()
        
        # Inyecta automáticamente los superusuarios
        inject_superusers()
        # Inyecta el contenido por defecto del sitio si no existe
        inject_site_content()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)