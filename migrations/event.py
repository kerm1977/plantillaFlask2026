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

