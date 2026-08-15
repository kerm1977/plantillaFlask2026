# Auto-generated migration module
from db import db

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

