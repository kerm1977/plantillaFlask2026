# Auto-generated migration module
from db import db

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

