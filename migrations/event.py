# Auto-generated migration module
from db import db

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

def _migrate_event_enlace_extra():
    """Agrega columna enlace_extra a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'enlace_extra' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN enlace_extra VARCHAR(1000)")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_enlace_extra: {e}")

def _migrate_event_texto_referencia():
    """Agrega columna texto_referencia a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'texto_referencia' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN texto_referencia TEXT")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_texto_referencia: {e}")

def _migrate_event_visitado():
    """Agrega columna visitado a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'visitado' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN visitado VARCHAR(10) DEFAULT 'No'")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_visitado: {e}")

def _migrate_event_kilometros():
    """Agrega columna kilometros a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'kilometros' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN kilometros REAL")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_kilometros: {e}")


def _migrate_event_tipo_terreno():
    """Agrega columna tipo_terreno a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'tipo_terreno' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN tipo_terreno VARCHAR(100)")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_tipo_terreno: {e}")


def _migrate_event_zona_alto_riesgo():
    """Agrega columna zona_alto_riesgo a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'zona_alto_riesgo' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN zona_alto_riesgo BOOLEAN DEFAULT 0")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_zona_alto_riesgo: {e}")


def _migrate_visitado_to_estados():
    """Convierte valores antiguos del campo visitado a los nuevos estados."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE event SET visitado = 'Visitado' WHERE visitado = 'Sí'")
        cursor.execute("UPDATE event SET visitado = 'Pendiente' WHERE visitado = 'No'")
        cursor.execute("UPDATE event SET visitado = 'Pendiente' WHERE visitado IS NULL OR visitado = ''")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_visitado_to_estados: {e}")

def _migrate_event_tipo_caminata():
    """Agrega columna tipo_caminata a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'tipo_caminata' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN tipo_caminata VARCHAR(20)")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_tipo_caminata: {e}")

def _migrate_event_precio_buseta():
    """Agrega columna precio_buseta a tabla event si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'precio_buseta' not in columns:
            cursor.execute("ALTER TABLE event ADD COLUMN precio_buseta INTEGER")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_event_precio_buseta: {e}")

