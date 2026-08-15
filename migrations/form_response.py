# Auto-generated migration module
from db import db

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

