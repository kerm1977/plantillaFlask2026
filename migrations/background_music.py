from db import db


def _migrate_background_music():
    """Crea la tabla background_music e inserta el registro por defecto si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS background_music (
                id INTEGER PRIMARY KEY,
                enabled BOOLEAN DEFAULT 0,
                songs TEXT DEFAULT '[]',
                random BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM background_music")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO background_music (id, enabled, songs, random)
                VALUES (1, 0, '[]', 1)
            """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_background_music: {e}")
