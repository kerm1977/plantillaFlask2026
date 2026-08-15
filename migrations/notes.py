# Auto-generated migration module
from db import db

def _migrate_notes():
    """Agrega la columna public_token a la tabla note si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(note)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if 'public_token' not in existing_cols:
            cursor.execute("ALTER TABLE note ADD COLUMN public_token VARCHAR(64)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_notes: {e}")

