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

