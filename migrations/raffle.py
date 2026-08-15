# Auto-generated migration module
from db import db

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

