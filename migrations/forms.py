# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# Auto-generated migration module
from db import db

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

def _migrate_forms_residencia():
    """Agrega columna show_residencia a form y provincia/direccion a form_response."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "show_residencia" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_residencia BOOLEAN DEFAULT 0")

        cursor.execute("PRAGMA table_info(form_response)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("provincia", "VARCHAR(50)"),
            ("direccion", "VARCHAR(500)"),
        ]
        for col, definition in migrations:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE form_response ADD COLUMN {col} {definition}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_forms_residencia: {e}")

def _migrate_forms_codigo_area():
    """Agrega columna show_codigo_area a form y codigo_area a form_response."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "show_codigo_area" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_codigo_area BOOLEAN DEFAULT 0")

        cursor.execute("PRAGMA table_info(form_response)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "codigo_area" not in existing_cols:
            cursor.execute("ALTER TABLE form_response ADD COLUMN codigo_area VARCHAR(10)")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_forms_codigo_area: {e}")

def _migrate_forms_membrete():
    """Agrega columnas show_logo y membrete a la tabla form."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(form)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "show_logo" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN show_logo BOOLEAN DEFAULT 0")
        if "membrete" not in existing_cols:
            cursor.execute("ALTER TABLE form ADD COLUMN membrete TEXT")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_forms_membrete: {e}")

