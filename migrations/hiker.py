# Auto-generated migration module
from db import db

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

